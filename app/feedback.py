"""Store thumbs-down chat notes in the usage table. Thumbs-up is not recorded."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import Settings
from app.usage import UsageStore

PK = "feedback"
MAX_REASON = 2000
MAX_TURN_CHARS = 8000
MAX_HISTORY_MESSAGES = 80
MAX_HISTORY_CHARS = 100_000


class FeedbackError(Exception):
    """A feedback write or read that should not be stored."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


def _clip(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[:limit]


def history_from_payload(payload: dict[str, object]) -> list[dict[str, str]]:
    raw = payload.get("history")
    if not isinstance(raw, list) or not raw:
        raise FeedbackError("send the chat")
    turns: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        if role not in {"user", "assistant"}:
            continue
        turns.append({"role": str(role), "content": _clip(item.get("content"), MAX_TURN_CHARS)})
    if not turns:
        raise FeedbackError("send the chat")
    if len(turns) > MAX_HISTORY_MESSAGES:
        turns = turns[-MAX_HISTORY_MESSAGES:]
    while sum(len(turn["content"]) for turn in turns) > MAX_HISTORY_CHARS and len(turns) > 1:
        turns.pop(0)
    if len(turns[0]["content"]) > MAX_HISTORY_CHARS:
        turns[0]["content"] = turns[0]["content"][:MAX_HISTORY_CHARS]
    return turns


def _snippets(history: list[dict[str, str]]) -> tuple[str, str]:
    user_message = ""
    message = ""
    for turn in history:
        if turn["role"] == "user":
            user_message = turn["content"]
        else:
            message = turn["content"]
    return message, user_message


def fields_from_payload(payload: object) -> tuple[str, str, str, list[dict[str, str]]]:
    if not isinstance(payload, dict):
        raise FeedbackError("send a reason")
    reason = _clip(payload.get("reason"), MAX_REASON)
    if not reason:
        raise FeedbackError("say why")
    history = history_from_payload(payload)
    message, user_message = _snippets(history)
    return reason, message, user_message, history


def save_feedback(
    settings: Settings,
    *,
    reason: str,
    message: str,
    user_message: str,
    history: list[dict[str, str]],
    sub: str,
    email: str,
) -> dict[str, object]:
    table = UsageStore(settings).table()
    if table is None:
        raise FeedbackError("feedback is not stored", 503)
    created = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    item: dict[str, object] = {
        "pk": PK,
        "sk": f"{created}#{uuid.uuid4().hex}",
        "reason": reason,
        "message": message,
        "user_message": user_message,
        "history": history,
        "sub": sub,
        "email": email,
        "created": created,
    }
    table.put_item(Item=item)
    return item


def list_feedback(settings: Settings, limit: int = 50) -> list[dict[str, object]]:
    table = UsageStore(settings).table()
    if table is None:
        raise FeedbackError("USAGE_TABLE is not set", 503)
    bounded = max(1, min(int(limit), 200))
    from boto3.dynamodb.conditions import Key

    pages = table.query(
        KeyConditionExpression=Key("pk").eq(PK),
        ScanIndexForward=False,
        Limit=bounded,
    )
    items = list(pages.get("Items", []))
    return items


def format_feedback(items: list[dict[str, object]]) -> str:
    if not items:
        return "No feedback."
    blocks: list[str] = []
    for item in items:
        who = str(item.get("email") or item.get("sub") or "anonymous")
        lines = [f"{item.get('created', '')}  {who}", str(item.get("reason") or "")]
        history = item.get("history")
        if isinstance(history, list) and history:
            lines.append("chat:")
            for turn in history:
                if not isinstance(turn, dict):
                    continue
                role = "user" if turn.get("role") == "user" else "Astraeus"
                lines.append(f"{role}: {turn.get('content') or ''}")
        else:
            user_message = str(item.get("user_message") or "")
            message = str(item.get("message") or "")
            if user_message:
                lines.append(f"user: {user_message}")
            if message:
                lines.append(f"reply: {message}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


async def handle_post(request) -> object:
    import json

    from starlette.responses import JSONResponse

    from app.auth import TokenError
    from app.server import _identity_from_request, _settings

    settings = _settings()
    sub = ""
    email = ""
    if not settings.auth_disabled:
        try:
            identity = _identity_from_request(request)
        except TokenError as exc:
            return JSONResponse({"error": str(exc)}, status_code=401)
        sub = identity.sub
        email = identity.email
    try:
        payload = await request.json()
    except (json.JSONDecodeError, ValueError):
        return JSONResponse({"error": "send a reason"}, status_code=400)
    try:
        reason, message, user_message, history = fields_from_payload(payload)
        save_feedback(
            settings,
            reason=reason,
            message=message,
            user_message=user_message,
            history=history,
            sub=sub,
            email=email,
        )
    except FeedbackError as exc:
        return JSONResponse({"error": exc.message}, status_code=exc.status)
    return JSONResponse({"ok": True})
