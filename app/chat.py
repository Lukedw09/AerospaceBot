"""Site chat. Grok calls the same aerospace programs the MCP server runs."""

from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.catalog import load_catalog, repo_root_from
from app.config import grok_api_key, grok_model
from app.runner import result_root_for
from app.usage import UsageStore

GROK_URL = "https://api.x.ai/v1/chat/completions"
GROK_TIMEOUT_SEC = 120
MAX_MESSAGE_CHARS = 8000
MAX_CONVERSATION_CHARS = 100_000
MAX_TOOL_ROUNDS = 8
MAX_TOOL_TEXT = 20_000
IMAGE_PREFIXES = ("graph:", "coefficients_graph:", "polar_graph:")

SYSTEM_PROMPT = (
    "You are Astraeus, an aerospace assistant. "
    "Every calculated number you state must come from a tool result in this conversation, "
    "never from memory or your own arithmetic. "
    "State units and the tool's caveats. "
    "If a tool needs an input the user did not give, ask instead of guessing. "
    "When the user explicitly asks for an example, choose the missing inputs yourself, "
    "including random values in a normal range for that tool. "
    "Tell the user those values are an example you chose, then run the tool. "
    "A tool note that says not to invent inputs does not apply to that explicit example. "
    "Do not choose inputs unless they asked for an example. "
    "Earlier assistant text may be quoted, but any new calculated number needs a tool call."
)

_openai_tools: list[dict[str, Any]] | None = None
_parameter_names: dict[str, list[str]] | None = None
_source_rows: dict[str, dict[str, str]] | None = None
_catalog_by_name: dict[str, Any] | None = None


class GrokError(Exception):
    """The chat provider failed. The message is intentionally empty."""

    def __init__(self, reason: str = "") -> None:
        super().__init__()
        self.reason = reason


def _scrub(value: Any, key: str) -> Any:
    if not key:
        return value
    if isinstance(value, str):
        return value.replace(key, "")
    if isinstance(value, list):
        return [_scrub(item, key) for item in value]
    if isinstance(value, dict):
        return {name: _scrub(item, key) for name, item in value.items()}
    return value


def _json(body: dict[str, Any], status: int, key: str = "") -> JSONResponse:
    return JSONResponse(_scrub(body, key), status_code=status)


def _usage(store: UsageStore, sub: str) -> dict[str, int]:
    snap = store.snapshot(sub)
    used = int(snap["used_today"])
    cap = int(snap["daily_cap"])
    return {"used_today": used, "daily_cap": cap, "remaining": max(0, cap - used)}


def _tools() -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    global _openai_tools, _parameter_names
    if _openai_tools is not None and _parameter_names is not None:
        return _openai_tools, _parameter_names
    from app.server import build_server

    mcp = build_server()
    raw = getattr(mcp._tool_manager, "_tools", {})
    openai: list[dict[str, Any]] = []
    names: dict[str, list[str]] = {}
    for name, registered in raw.items():
        schema = getattr(registered, "parameters", None)
        if not isinstance(schema, dict):
            schema = {"type": "object", "properties": {}}
        else:
            schema = dict(schema)
        schema = _parameters(schema)
        properties = schema.get("properties") or {}
        description = getattr(registered, "description", "") or ""
        openai.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": schema,
                },
            }
        )
        names[name] = sorted(str(key) for key in properties)
    _openai_tools = openai
    _parameter_names = names
    return openai, names


def _parameters(schema: dict[str, Any]) -> dict[str, Any]:
    """Copy a tool schema into a form the chat API can compile."""
    copied = json.loads(json.dumps(schema))
    if not isinstance(copied, dict):
        copied = {"type": "object", "properties": {}}
    copied.setdefault("type", "object")
    copied["additionalProperties"] = False
    properties = copied.get("properties")
    if isinstance(properties, dict):
        for prop in properties.values():
            if not isinstance(prop, dict):
                continue
            if prop.get("default") is None:
                prop.pop("default", None)
            encoded = json.dumps(prop)
            if "$ref" in encoded or "anyOf" in prop or "oneOf" in prop:
                description = prop.get("description")
                prop.clear()
                prop["type"] = "string"
                if isinstance(description, str) and description:
                    prop["description"] = description
    return copied


def _source_catalog() -> dict[str, dict[str, str]]:
    global _source_rows
    if _source_rows is not None:
        return _source_rows
    text = (repo_root_from() / "sources.md").read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not re.fullmatch(r"V\d+", cells[0]):
            continue
        href = ""
        found = re.search(r"\((https?://[^)]+)\)", cells[1])
        if found:
            href = found.group(1)
        document = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cells[1])
        rows[cells[0]] = {"id": cells[0], "document": document, "href": href}
    _source_rows = rows
    return rows


def _catalog_tool(name: str) -> Any:
    global _catalog_by_name
    if _catalog_by_name is None:
        _catalog_by_name = {tool.name: tool for tool in load_catalog()}
    return _catalog_by_name.get(name)


def sources_for(name: str) -> list[dict[str, str]]:
    if name in {"list_tools", "lookup_formula"}:
        return []
    tool = _catalog_tool(name)
    if tool is None:
        return []
    folder = tool.script.parent
    cited = folder / "sources.md"
    if cited.is_file():
        text = cited.read_text(encoding="utf-8")
    else:
        skill = folder / "SKILL.md"
        text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    catalog = _source_catalog()
    found: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"\bV\d+\b", text):
        source_id = match.group(0)
        if source_id in seen or source_id not in catalog:
            continue
        seen.add(source_id)
        found.append(catalog[source_id])
    return found


def _plot_src(value: str) -> str | None:
    if value.startswith("https://") or value.startswith("http://"):
        return value
    path = Path(value)
    try:
        if not path.is_file() or path.suffix.lower() != ".png":
            return None
        root = result_root_for(repo_root_from()).resolve()
        path.resolve().relative_to(root)
    except (OSError, ValueError):
        return None
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG"):
        return None
    encoded = base64.b64encode(data).decode("ascii")
    return "data:image/png;base64," + encoded


def plots_from(name: str, text: str) -> list[dict[str, str]]:
    plots: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        for prefix in IMAGE_PREFIXES:
            if not stripped.startswith(prefix):
                continue
            src = _plot_src(stripped.split(":", 1)[1].strip())
            if src:
                plots.append({"tool": name, "src": src})
    return plots


def _for_model(text: str) -> str:
    if len(text) <= MAX_TOOL_TEXT:
        return text
    return text[:MAX_TOOL_TEXT] + "\n... truncated"


def _run_tool(name: str, arguments: dict[str, Any]) -> str:
    from app.server import (
        _unknown_parameter_message,
        dispatch_calculation,
        dispatch_formula,
        dispatch_list,
    )

    _listed, names = _tools()
    if name not in names:
        return "that tool is not in the library"
    if name == "list_tools":
        message = _unknown_parameter_message(arguments, names[name])
        if message:
            return f"error: {message}"
        return dispatch_list()
    if name == "lookup_formula":
        message = _unknown_parameter_message(arguments, names[name])
        if message:
            return f"error: {message}"
        formula_id = arguments.get("formula_id")
        return dispatch_formula(
            "" if formula_id is None else str(formula_id),
            arguments.get("values_json"),
        )
    return dispatch_calculation(name, arguments)


def _conversation(payload: Any) -> tuple[list[dict[str, str]], str | None]:
    if not isinstance(payload, dict):
        return [], "send a message"
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return [], "send a message"
    kept: list[dict[str, str]] = []
    total = 0
    for item in messages:
        if not isinstance(item, dict):
            return [], "send a message"
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        content = item.get("content")
        if not isinstance(content, str):
            return [], "send a message"
        if len(content) > MAX_MESSAGE_CHARS:
            return [], "that message is too long"
        total += len(content)
        if total > MAX_CONVERSATION_CHARS:
            return [], "that conversation is too long"
        kept.append({"role": role, "content": content})
    if not kept or kept[-1]["role"] != "user":
        return [], "send a message"
    return kept, None


def _log_provider(exc: BaseException, key: str) -> str:
    reason = ""
    if isinstance(exc, urllib.error.HTTPError):
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except OSError:
            raw = ""
        if "Incorrect API key" in raw:
            reason = "key"
        detail = f"HTTP {exc.code} {raw[:400]}"
    else:
        detail = f"{type(exc).__name__}: {exc}"
    if key:
        detail = detail.replace(key, "[redacted]")
    print("chat provider failed: " + detail[:500], file=sys.stderr)
    return reason


def complete(messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str, key: str) -> dict[str, Any]:
    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "reasoning_effort": "low",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        GROK_URL,
        data=payload,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=GROK_TIMEOUT_SEC) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        message = data["choices"][0]["message"]
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise GrokError(_log_provider(exc, key)) from None
    if not isinstance(message, dict):
        _log_provider(TypeError("chat response had no message"), key)
        raise GrokError()
    return message


def _reply(result: dict[str, Any], store: UsageStore, sub: str, key: str, status: int = 200) -> JSONResponse:
    body = {
        "answer": result["answer"],
        "plots": result["plots"],
        "details": result["details"],
        "usage": _usage(store, sub),
        "stopped": result["stopped"],
    }
    return _json(body, status, key)


def run_turn(kept: list[dict[str, str]], store: UsageStore, sub: str, key: str, model: str) -> JSONResponse:
    tools, _names = _tools()
    grok_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}, *kept]
    details: list[dict[str, Any]] = []
    plots: list[dict[str, str]] = []
    rounds = 0
    answer = ""
    stopped = ""
    while True:
        try:
            message = complete(grok_messages, tools, model, key)
        except GrokError as exc:
            if exc.reason == "key":
                return _json({"error": "The xAI API key was rejected."}, 502, key)
            return _json({"error": "The chat service did not answer."}, 502, key)
        except Exception as exc:
            _log_provider(exc, key)
            return _json({"error": "The chat service did not answer."}, 502, key)
        content = message.get("content") or ""
        if not isinstance(content, str):
            content = ""
        tool_calls = message.get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            answer = content
            break
        rounds += 1
        prepared: list[dict[str, Any]] = []
        for index, call in enumerate(tool_calls):
            if not isinstance(call, dict):
                continue
            function = call.get("function") if isinstance(call.get("function"), dict) else {}
            raw_arguments = function.get("arguments")
            arguments, error = _parse_arguments(raw_arguments)
            prepared.append(
                {
                    "id": str(call.get("id") or f"call_{rounds}_{index}"),
                    "name": str(function.get("name") or ""),
                    "arguments": arguments,
                    "raw": raw_arguments if isinstance(raw_arguments, str) else json.dumps(arguments),
                    "error": error,
                }
            )
        if not prepared:
            answer = content
            break
        finished: list[tuple[dict[str, Any], str]] = []
        limit = ""
        for item in prepared:
            if item["error"]:
                output = str(item["error"])
            else:
                output = _run_tool(str(item["name"]), item["arguments"])
            finished.append((item, output))
            details.append(
                {
                    "tool": item["name"],
                    "arguments": item["arguments"],
                    "output": output,
                    "sources": [] if item["error"] else sources_for(str(item["name"])),
                }
            )
            plots.extend(plots_from(str(item["name"]), output))
            if output.startswith("Daily limit reached"):
                limit = output
                break
        if limit:
            answer = limit
            stopped = "limit"
            break
        grok_messages.append(
            {
                "role": "assistant",
                "content": content or None,
                "tool_calls": [
                    {
                        "id": item["id"],
                        "type": "function",
                        "function": {"name": item["name"], "arguments": item["raw"]},
                    }
                    for item, _output in finished
                ],
            }
        )
        for item, output in finished:
            grok_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": item["id"],
                    "content": _for_model(output),
                }
            )
        if rounds >= MAX_TOOL_ROUNDS:
            answer = content.strip() or "Stopped after 8 tool rounds."
            stopped = "rounds"
            break
    return _reply(
        {"answer": answer, "plots": plots, "details": details, "stopped": stopped},
        store,
        sub,
        key,
    )


def _parse_arguments(raw: Any) -> tuple[dict[str, Any], str | None]:
    if raw is None or raw == "":
        return {}, None
    if isinstance(raw, dict):
        return raw, None
    if not isinstance(raw, str):
        return {}, "error: arguments are not valid JSON"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}, "error: arguments are not valid JSON"
    if not isinstance(parsed, dict):
        return {}, "error: arguments are not valid JSON"
    return parsed, None


def _limit_result(message: str) -> dict[str, Any]:
    return {"answer": message, "plots": [], "details": [], "stopped": "limit"}


async def handle_status(request: Request) -> JSONResponse:
    from app.auth import TokenError
    from app.server import _identity_from_request, _settings

    settings = _settings()
    if settings.auth_disabled:
        store = UsageStore(settings)
        body = {"sign_in_required": False, **_usage(store, "")}
        return _json(body, 200)
    try:
        identity = _identity_from_request(request)
    except TokenError as exc:
        return _json({"error": str(exc)}, 401)
    store = UsageStore(settings)
    body = {"sign_in_required": True, **_usage(store, identity.sub)}
    return _json(body, 200)


async def handle_post(request: Request) -> JSONResponse:
    from app.auth import TokenError
    from app.server import _identity, _identity_from_request, _settings

    settings = _settings()
    identity = None
    if not settings.auth_disabled:
        try:
            identity = _identity_from_request(request)
        except TokenError as exc:
            return _json({"error": str(exc)}, 401)
    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        return _json({"error": "send a message"}, 400)
    kept, problem = _conversation(payload)
    if problem:
        status = 400
        return _json({"error": problem}, status)
    store = UsageStore(settings)
    sub = identity.sub if identity is not None else ""
    if identity is not None and not settings.auth_disabled:
        decision = store.check(identity.sub, identity.email)
        if not decision.allowed:
            return _reply(_limit_result(decision.message), store, sub, "")
        store.commit(identity.sub)
    try:
        key = grok_api_key()
    except Exception:
        return _json({"error": "chat is not configured"}, 503)
    model = grok_model()
    if not key or not model:
        if settings.auth_disabled and not key:
            return _json(
                {"error": "Set GROK_API_KEY to the key from console.x.ai and restart the server."},
                503,
            )
        return _json({"error": "chat is not configured"}, 503, key)
    marker = _identity.set(identity)
    try:
        return run_turn(kept, store, sub, key, model)
    finally:
        _identity.reset(marker)
