"""Client chat-share payload: JSON, deflate-raw, base64url. Used by tests and docs."""

from __future__ import annotations

import base64
import json
import zlib
from typing import Any

MAX_SHARE_CHARS = 80_000
MAX_SHARE_MESSAGES = 80


def slice_transcript(messages: list[dict[str, Any]], upto: int) -> list[dict[str, Any]]:
    """Keep messages through ``upto`` (inclusive), share-safe fields only."""
    if upto < 0 or upto >= len(messages):
        raise ValueError("share index is out of range")
    out: list[dict[str, Any]] = []
    for item in messages[: upto + 1]:
        role = item.get("role")
        if role not in {"user", "assistant"}:
            raise ValueError("share message role is invalid")
        content = item.get("content")
        if not isinstance(content, str):
            content = "" if content is None else str(content)
        row: dict[str, Any] = {"role": role, "content": content}
        plots = item.get("plots")
        if isinstance(plots, list):
            kept = []
            for plot in plots:
                if not isinstance(plot, dict):
                    continue
                src = plot.get("src")
                if not isinstance(src, str) or not src.startswith(("http://", "https://")):
                    continue
                entry: dict[str, Any] = {"src": src}
                tool = plot.get("tool")
                if isinstance(tool, str) and tool:
                    entry["tool"] = tool
                kept.append(entry)
            if kept:
                row["plots"] = kept
        out.append(row)
    return out


def _total_chars(messages: list[dict[str, Any]]) -> int:
    return sum(len(str(item.get("content") or "")) for item in messages)


def encode_share(messages: list[dict[str, Any]], upto: int | None = None) -> str:
    """Compress a transcript slice into a URL-safe share token."""
    if not messages:
        raise ValueError("nothing to share")
    end = len(messages) - 1 if upto is None else upto
    payload = slice_transcript(messages, end)
    if len(payload) > MAX_SHARE_MESSAGES:
        raise ValueError("shared chat is too long")
    if _total_chars(payload) > MAX_SHARE_CHARS:
        raise ValueError("shared chat is too long")
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    compressed = zlib.compress(raw, level=9, wbits=-15)
    return base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")


def decode_share(token: str) -> list[dict[str, Any]]:
    """Expand a share token back into a transcript list."""
    if not token or not isinstance(token, str):
        raise ValueError("share link is empty")
    padded = token + "=" * (-len(token) % 4)
    try:
        compressed = base64.urlsafe_b64decode(padded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ValueError("share link is not valid") from exc
    try:
        raw = zlib.decompress(compressed, wbits=-15)
    except zlib.error as exc:
        raise ValueError("share link is not valid") from exc
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("share link is not valid") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("share link is not valid")
    if len(data) > MAX_SHARE_MESSAGES:
        raise ValueError("share link is not valid")
    # Re-validate through the same shape rules as encode.
    return slice_transcript(data, len(data) - 1)


def share_hash(token: str) -> str:
    return "#s=" + token


def parse_share_hash(fragment: str) -> str | None:
    """Return the token from a location.hash-style fragment, or None."""
    if not fragment:
        return None
    text = fragment[1:] if fragment.startswith("#") else fragment
    if text.startswith("s="):
        token = text[2:]
        return token or None
    return None
