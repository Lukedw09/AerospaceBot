"""Site chat. Grok calls the same aerospace programs the MCP server runs."""

from __future__ import annotations

import base64
import json
import re
import sys
import time
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

GROK_URL = "https://api.x.ai/v1/responses"
GROK_TIMEOUT_SEC = 70
TURN_BUDGET_SEC = 100
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
    """The chat provider failed. detail is safe to show; it never contains the key."""

    def __init__(self, reason: str = "", status: int = 0, detail: str = "") -> None:
        super().__init__()
        self.reason = reason
        self.status = status
        self.detail = detail


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


def _drop_additional_properties(node: Any) -> None:
    """xAI rejects additionalProperties: false. Object schemas are already closed."""
    if isinstance(node, dict):
        if node.get("additionalProperties") is False:
            node.pop("additionalProperties", None)
        for value in node.values():
            _drop_additional_properties(value)
    elif isinstance(node, list):
        for item in node:
            _drop_additional_properties(item)


def _parameters(schema: dict[str, Any]) -> dict[str, Any]:
    """Copy a tool schema into a form the Responses API can compile."""
    copied = json.loads(json.dumps(schema))
    if not isinstance(copied, dict):
        copied = {"type": "object", "properties": {}}
    copied.setdefault("type", "object")
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
    _drop_additional_properties(copied)
    return copied


def _source_catalog() -> dict[str, dict[str, str]]:
    global _source_rows
    if _source_rows is not None:
        return _source_rows
    path = repo_root_from() / "sources.md"
    if not path.is_file():
        _source_rows = {}
        return _source_rows
    text = path.read_text(encoding="utf-8")
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


def _error_text(raw: str) -> str:
    message = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            message = str(err.get("error") or err.get("message") or "")
        elif isinstance(err, str):
            message = err
        elif isinstance(data.get("message"), str):
            message = str(data["message"])
    return " ".join(message.split())[:300]


def _log_provider(exc: BaseException, key: str) -> tuple[str, str]:
    """Log a provider failure. Returns (key_reason, public_detail)."""
    reason = ""
    public = type(exc).__name__
    if isinstance(exc, urllib.error.HTTPError):
        try:
            raw = exc.read().decode("utf-8", errors="replace")
        except OSError:
            raw = ""
        if "Incorrect API key" in raw:
            reason = "key"
        if key:
            raw = raw.replace(key, "[redacted]")
        public = _error_text(raw)
        logged = f"HTTP {exc.code} {raw[:400]}"
    else:
        logged = f"{type(exc).__name__}: {exc}"
    if key:
        logged = logged.replace(key, "[redacted]")
    print("chat provider failed: " + logged[:500], file=sys.stderr)
    return reason, public


def _failure_message(exc: GrokError) -> str:
    detail = " ".join((exc.detail or "").split())
    if exc.status and detail:
        return f"The chat service did not answer (HTTP {exc.status}): {detail}"
    if exc.status:
        return f"The chat service did not answer (HTTP {exc.status})."
    if detail:
        return f"The chat service did not answer: {detail}"
    return "The chat service did not answer."


def _responses_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """grok-4.7 function tools put name and parameters on the tool itself."""
    converted: list[dict[str, Any]] = []
    for tool in tools:
        function = tool.get("function") if isinstance(tool, dict) else None
        if not isinstance(function, dict):
            continue
        converted.append(
            {
                "type": "function",
                "name": function.get("name") or "",
                "description": function.get("description") or "",
                "parameters": function.get("parameters") or {"type": "object", "properties": {}},
            }
        )
    return converted


def _request_body(messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """Build a Responses API body. A tool round continues the stored response."""
    response_id = ""
    outputs: list[dict[str, str]] = []
    for item in messages:
        if item.get("role") == "assistant" and item.get("response_id"):
            response_id = str(item["response_id"])
        if item.get("role") != "tool":
            continue
        text = item.get("content")
        if not isinstance(text, str) or not text:
            text = " "
        outputs.append(
            {
                "type": "function_call_output",
                "call_id": str(item.get("tool_call_id") or ""),
                "output": text,
            }
        )
    body: dict[str, Any] = {
        "model": model,
        "tools": _responses_tools(tools),
        "tool_choice": "auto",
        "reasoning": {"effort": "low"},
    }
    if response_id and outputs:
        body["previous_response_id"] = response_id
        body["input"] = outputs
        return body
    conversation: list[dict[str, str]] = []
    for item in messages:
        role = item.get("role")
        if role not in {"system", "user", "assistant"} or item.get("tool_calls"):
            continue
        content = item.get("content")
        if not isinstance(content, str) or not content:
            continue
        conversation.append({"role": role, "content": content})
    body["input"] = conversation
    return body


def _message_from_response(data: dict[str, Any]) -> dict[str, Any]:
    output = data.get("output")
    if isinstance(output, list):
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for index, item in enumerate(output):
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "function_call":
                arguments = item.get("arguments")
                if not isinstance(arguments, str):
                    arguments = json.dumps(arguments if isinstance(arguments, dict) else {})
                tool_calls.append(
                    {
                        "id": str(item.get("call_id") or item.get("id") or f"call_{index}"),
                        "type": "function",
                        "function": {"name": str(item.get("name") or ""), "arguments": arguments},
                    }
                )
                continue
            if kind != "message":
                continue
            content = item.get("content")
            if isinstance(content, str):
                text_parts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        text_parts.append(part)
                    elif isinstance(part, dict) and part.get("type") in {"output_text", "text"}:
                        text_parts.append(str(part.get("text") or ""))
        return {
            "role": "assistant",
            "content": "".join(text_parts),
            "tool_calls": tool_calls,
            "response_id": str(data.get("id") or ""),
        }
    message = data["choices"][0]["message"]
    if not isinstance(message, dict):
        raise TypeError("chat response had no message")
    copied = dict(message)
    copied["response_id"] = str(data.get("id") or "")
    return copied


def complete(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    model: str,
    key: str,
    timeout: float = GROK_TIMEOUT_SEC,
) -> dict[str, Any]:
    payload = json.dumps(_request_body(messages, tools, model)).encode("utf-8")
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
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise TypeError("chat response was not an object")
        failed = data.get("error")
        if str(data.get("status") or "") == "failed" or (failed and not data.get("output")):
            text = failed if isinstance(failed, str) else ""
            if isinstance(failed, dict):
                text = str(failed.get("message") or failed.get("error") or "")
            raise GrokError(detail=_error_text(text or "the provider failed"))
        message = _message_from_response(data)
    except urllib.error.HTTPError as exc:
        reason, detail = _log_provider(exc, key)
        raise GrokError(reason, status=int(exc.code), detail=detail) from None
    except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        _reason, detail = _log_provider(exc, key)
        raise GrokError(detail=detail) from None
    if not isinstance(message, dict):
        _reason, detail = _log_provider(TypeError("chat response had no message"), key)
        raise GrokError(detail=detail)
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
    content = ""
    deadline = time.monotonic() + TURN_BUDGET_SEC
    while True:
        left = deadline - time.monotonic()
        if left < 15:
            if not answer:
                answer = content.strip()
            if not answer and details:
                answer = "The tool ran, but there was not enough time left to summarize it."
            if not answer:
                answer = "That request took too long. Ask for one calculation at a time."
            stopped = stopped or "time"
            break
        try:
            message = complete(grok_messages, tools, model, key, timeout=min(GROK_TIMEOUT_SEC, max(5.0, left - 8)))
        except GrokError as exc:
            if exc.reason == "key":
                return _json({"error": "The xAI API key was rejected."}, 502, key)
            if details:
                answer = "The tool ran, but the summary did not come back."
                break
            return _json({"error": _failure_message(exc)}, 502, key)
        except Exception as exc:
            _reason, detail = _log_provider(exc, key)
            if details:
                answer = "The tool ran, but the summary did not come back."
                break
            return _json({"error": _failure_message(GrokError(detail=detail))}, 502, key)
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
                try:
                    output = _run_tool(str(item["name"]), item["arguments"])
                except Exception as exc:
                    _log_provider(exc, key)
                    output = "that tool failed"
            finished.append((item, output))
            sources: list[dict[str, str]] = []
            if not item["error"]:
                try:
                    sources = sources_for(str(item["name"]))
                except OSError:
                    sources = []
            details.append(
                {
                    "tool": item["name"],
                    "arguments": item["arguments"],
                    "output": output,
                    "sources": sources,
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
        # xAI rejects a tool-call turn when content is null or omitted.
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": item["id"],
                    "type": "function",
                    "function": {"name": item["name"], "arguments": item["raw"]},
                }
                for item, _output in finished
            ],
        }
        if message.get("response_id"):
            assistant_message["response_id"] = str(message["response_id"])
        grok_messages.append(assistant_message)
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
    except Exception as exc:
        _reason, detail = _log_provider(exc, key)
        return _json({"error": _failure_message(GrokError(detail=detail))}, 502, key)
    finally:
        _identity.reset(marker)
