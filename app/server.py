"""MCP plugin. stdio for this PC, HTTP for Lambda."""

from __future__ import annotations

import inspect
import json
import os
import sys
import time
from contextvars import ContextVar
from typing import Annotated, Any

from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.accounts import delete_account, link_provider, profile, sign_out_everywhere, unlink_provider
from app.auth import (
    Identity,
    TokenError,
    authorization_server_metadata,
    protected_resource_metadata,
    verify_access_token,
    verify_id_token,
)
from app.catalog import Tool, load_catalog, repo_root_from, tool_by_name
from app.config import Settings, load_settings
from app.formulas import lookup_formula
from app.pictures import publish, rewrite
from app.runner import release_job, run_tool
from app.usage import UsageStore

_identity: ContextVar[Identity | None] = ContextVar("identity", default=None)

INSTRUCTIONS = (
    "For aerospace formulas and calculations, use these tools. "
    "Pass only values the user gave, after converting to the units named on the tool. "
    "If a tool returns an error about a missing or illegal input, ask for that input. "
    "Quote the tool's key: value lines. Do not recompute them. "
    "If no tool fits, say so. Do not invent a formula."
)


def _settings() -> Settings:
    return load_settings(str(repo_root_from()))


def _store() -> UsageStore:
    return UsageStore(_settings())


def _request_base(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-proto", "")
    scheme = forwarded.split(",")[0].strip() or request.url.scheme
    host = request.headers.get("x-forwarded-host", "") or request.headers.get("host", "")
    if not host:
        return ""
    return f"{scheme}://{host}".rstrip("/")


def _with_request_base(settings: Settings, request: Request) -> Settings:
    if settings.public_base_url:
        return settings
    base = _request_base(request)
    if not base:
        return settings
    return Settings(
        auth_disabled=settings.auth_disabled,
        repo_root=settings.repo_root,
        usage_table=settings.usage_table,
        picture_bucket=settings.picture_bucket,
        daily_tool_cap=settings.daily_tool_cap,
        tool_timeout_sec=settings.tool_timeout_sec,
        result_link_hours=settings.result_link_hours,
        usage_timezone=settings.usage_timezone,
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_client_id=settings.cognito_client_id,
        cognito_region=settings.cognito_region,
        public_base_url=base,
        account_site_url=settings.account_site_url or base,
    )


def _bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""


def _identity_from_request(request: Request) -> Identity:
    settings = _settings()
    token = _bearer(request)
    if not token:
        raise TokenError("sign-in is required")
    return verify_access_token(token, settings)


def _too_large(arguments: dict[str, Any]) -> bool:
    try:
        encoded = json.dumps(arguments, default=str)
    except TypeError:
        return True
    return len(encoded) > 8000


def dispatch_calculation(name: str, arguments: dict[str, Any]) -> str:
    settings = _settings()
    root = repo_root_from()
    tool = tool_by_name(load_catalog(root), name)
    if tool is None:
        return "that tool is not in the library"
    if _too_large(arguments):
        return "those inputs are too large"
    identity = _identity.get()
    store = _store()
    if not settings.auth_disabled:
        if identity is None:
            return "Sign in is required."
        decision = store.check(identity.sub, identity.email)
        if not decision.allowed:
            return decision.message
    started = time.perf_counter()
    result = run_tool(
        tool,
        arguments,
        repo_root=root,
        timeout_sec=settings.tool_timeout_sec,
    )
    try:
        elapsed = time.perf_counter() - started
        sub = identity.sub if identity else "local"
        if result.exit_code == 0:
            links = publish(result.files, sub, settings)
            text = rewrite(result.text, links)
        else:
            text = result.text
        if not settings.auth_disabled and identity is not None and not result.missing_input:
            store.commit(identity.sub)
        print(
            f"tool {name} sub {sub} exit {result.exit_code} seconds {elapsed:.3f}",
            file=sys.stderr,
        )
        return text
    finally:
        release_job(result.job_dir)


def dispatch_formula(formula_id: str, values_json: str | None = None) -> str:
    settings = _settings()
    identity = _identity.get()
    store = _store()
    if not settings.auth_disabled:
        if identity is None:
            return "Sign in is required."
        decision = store.check(identity.sub, identity.email)
        if not decision.allowed:
            return decision.message
    if values_json and len(values_json) > 8000:
        return "those inputs are too large"
    root = repo_root_from()
    text = lookup_formula(
        root / "skills" / "aero-formulas" / "formulas.md",
        root / "skills" / "aero-formulas" / "checks" / "check.md",
        formula_id,
        values_json,
    )
    if not settings.auth_disabled and identity is not None and text != "that formula is not allowed":
        store.commit(identity.sub)
    return text


def dispatch_list() -> str:
    lines = []
    for tool in load_catalog():
        first = tool.description.split("\n", 1)[0]
        lines.append(f"{tool.name}: {first}")
    return "\n".join(lines)


def _annotation(flag_type: str, repeat: bool, description: str = "") -> Any:
    if repeat:
        base: Any = list[str]
    else:
        base = {"float": float, "int": int, "bool": bool, "string": str}[flag_type]
    if not description:
        return base
    return Annotated[base, Field(description=description)]


def _handler_for(tool: Tool):
    def handler(**kwargs: Any) -> str:
        return dispatch_calculation(tool.name, kwargs)

    params = []
    annotations: dict[str, Any] = {}
    for flag in tool.flags:
        default = inspect.Parameter.empty if flag.required else None
        ann = _annotation(flag.type_name, flag.repeat, flag.help)
        params.append(
            inspect.Parameter(
                flag.dest,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=ann,
            )
        )
        annotations[flag.dest] = ann
    handler.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    handler.__name__ = tool.name
    handler.__doc__ = tool.description
    handler.__annotations__ = annotations
    return handler


def build_server():
    from mcp.server.mcpserver import MCPServer

    settings = _settings()
    mcp = MCPServer("aerospace", instructions=INSTRUCTIONS)

    for tool in load_catalog():
        mcp.add_tool(_handler_for(tool), name=tool.name, description=tool.description)

    def list_tools() -> str:
        """List aerospace tool names and the skill each one belongs to."""
        return dispatch_list()

    def lookup_formula_tool(formula_id: str, values_json: str | None = None) -> str:
        """Return an allowed formula. formula_id must be listed in checks/check.md. values_json is an optional object of symbol names to numbers. partial and integral records are not evaluated."""
        return dispatch_formula(formula_id, values_json)

    mcp.add_tool(list_tools, name="list_tools", description=list_tools.__doc__ or "")
    mcp.add_tool(
        lookup_formula_tool,
        name="lookup_formula",
        description=lookup_formula_tool.__doc__ or "",
    )

    async def resource_metadata(request: Request) -> Response:
        current = _with_request_base(settings, request)
        return JSONResponse(protected_resource_metadata(current))

    async def auth_server_metadata(request: Request) -> Response:
        current = _with_request_base(settings, request)
        return JSONResponse(authorization_server_metadata(current))

    for path in (
        "/.well-known/oauth-protected-resource",
        "/.well-known/oauth-protected-resource/mcp",
    ):
        mcp.custom_route(path, methods=["GET"])(resource_metadata)
    for path in (
        "/.well-known/oauth-authorization-server",
        "/.well-known/oauth-authorization-server/mcp",
        "/.well-known/openid-configuration",
    ):
        mcp.custom_route(path, methods=["GET"])(auth_server_metadata)

    @mcp.custom_route("/account/public-config", methods=["GET"])
    async def public_config(request: Request) -> Response:
        current = _with_request_base(settings, request)
        base = current.public_base_url
        site = current.account_site_url or base
        domain = os.environ.get("COGNITO_DOMAIN", "")
        return JSONResponse(
            {
                "client_id": current.cognito_client_id,
                "hosted_ui": domain,
                "redirect_uri": (site + "/") if site else "",
                "mcp_url": (base + "/mcp") if base else "",
                "scopes": "openid email profile",
                "region": current.cognito_region,
            }
        )

    @mcp.custom_route("/account", methods=["GET"])
    async def account_get(request: Request) -> Response:
        try:
            identity = _identity_from_request(request)
        except TokenError as exc:
            return JSONResponse({"error": str(exc)}, status_code=401)
        return JSONResponse(profile(identity, settings, _store()))

    @mcp.custom_route("/account/link", methods=["POST"])
    async def account_link(request: Request) -> Response:
        try:
            identity = _identity_from_request(request)
            body = await request.json()
            message = link_provider(identity, str(body.get("id_token", "")), settings)
        except (TokenError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse({"message": message})

    @mcp.custom_route("/account/unlink", methods=["POST"])
    async def account_unlink(request: Request) -> Response:
        try:
            identity = _identity_from_request(request)
            body = await request.json()
            message = unlink_provider(identity, str(body.get("provider", "")), settings)
        except TokenError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        return JSONResponse({"message": message})

    @mcp.custom_route("/account/signout", methods=["POST"])
    async def account_signout(request: Request) -> Response:
        try:
            identity = _identity_from_request(request)
            message = sign_out_everywhere(identity, settings)
        except TokenError as exc:
            return JSONResponse({"error": str(exc)}, status_code=401)
        return JSONResponse({"message": message})

    @mcp.custom_route("/account/delete", methods=["POST"])
    async def account_delete(request: Request) -> Response:
        try:
            identity = _identity_from_request(request)
            message = delete_account(identity, settings, _store())
        except TokenError as exc:
            return JSONResponse({"error": str(exc)}, status_code=401)
        return JSONResponse({"message": message})

    return mcp


class _Guard:
    """Reject /mcp calls that do not carry a Cognito access token."""

    def __init__(self, app: Any, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "http" and scope.get("method") == "OPTIONS":
            await _empty(send, 204, self.settings)
            return
        path = scope.get("path", "")
        # JSON responses travel on POST. A GET would open an SSE stream that
        # Lambda holds until its timeout, and that exhausts the account limit.
        if scope.get("type") == "http" and scope.get("method") == "GET" and path.rstrip("/") == "/mcp":
            await _method_not_allowed(send)
            return
        current = _settings_for_scope(scope, self.settings)
        if (
            scope.get("type") == "http"
            and path.startswith("/mcp")
            and not current.auth_disabled
        ):
            token = _header(scope, "authorization")
            if token.lower().startswith("bearer "):
                token = token[7:].strip()
            else:
                token = ""
            if not token:
                await _unauthorized(send, current, "sign-in is required")
                return
            try:
                identity = verify_access_token(token, current)
            except TokenError as exc:
                await _unauthorized(send, current, str(exc))
                return
            marker = _identity.set(identity)
            try:
                await self.app(scope, receive, send)
            finally:
                _identity.reset(marker)
            return
        await self.app(scope, receive, send)


def _settings_for_scope(scope, settings: Settings) -> Settings:
    if settings.public_base_url:
        return settings
    host = _header(scope, "x-forwarded-host") or _header(scope, "host")
    proto = (_header(scope, "x-forwarded-proto") or "https").split(",")[0].strip()
    if not host:
        return settings
    base = f"{proto}://{host}".rstrip("/")
    return Settings(
        auth_disabled=settings.auth_disabled,
        repo_root=settings.repo_root,
        usage_table=settings.usage_table,
        picture_bucket=settings.picture_bucket,
        daily_tool_cap=settings.daily_tool_cap,
        tool_timeout_sec=settings.tool_timeout_sec,
        result_link_hours=settings.result_link_hours,
        usage_timezone=settings.usage_timezone,
        cognito_user_pool_id=settings.cognito_user_pool_id,
        cognito_client_id=settings.cognito_client_id,
        cognito_region=settings.cognito_region,
        public_base_url=base,
        account_site_url=settings.account_site_url or base,
    )


def _header(scope, name: str) -> str:
    for key, value in scope.get("headers", []):
        if key.decode("latin1").lower() == name:
            return value.decode("latin1")
    return ""


def _www(settings: Settings) -> str:
    base = settings.public_base_url or ""
    metadata = f"{base}/.well-known/oauth-protected-resource" if base else "/.well-known/oauth-protected-resource"
    return f'Bearer resource_metadata="{metadata}"'


async def _unauthorized(send, settings: Settings, message: str) -> None:
    body = json.dumps({"error": message}).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", _www(settings).encode("utf-8")),
                (b"access-control-allow-origin", b"*"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _method_not_allowed(send) -> None:
    body = b'{"error":"this server accepts POST"}'
    await send(
        {
            "type": "http.response.start",
            "status": 405,
            "headers": [
                (b"content-type", b"application/json"),
                (b"allow", b"POST, OPTIONS"),
                (b"access-control-allow-origin", b"*"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _empty(send, status: int, settings: Settings) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"access-control-allow-origin", b"*"),
                (b"access-control-allow-headers", b"authorization,content-type"),
                (b"access-control-allow-methods", b"GET,POST,OPTIONS"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": b""})


def http_app():
    settings = _settings()
    mcp = build_server()
    starlette = mcp.streamable_http_app(
        stateless_http=True,
        json_response=True,
        host="0.0.0.0",
    )
    return _Guard(starlette, settings)


def main() -> None:
    http = os.environ.get("AEROSPACE_HTTP", "").strip() in {"1", "true", "yes"}
    if http:
        import uvicorn

        port = int(os.environ.get("PORT", "8080"))
        uvicorn.run(http_app(), host="0.0.0.0", port=port)
        return
    os.environ.setdefault("AUTH_DISABLED", "1")
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
