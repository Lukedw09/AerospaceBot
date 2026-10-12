"""Thumbs-down feedback: auth, chat history, DynamoDB write, and the list CLI."""

from __future__ import annotations

import io
import os
import unittest
from unittest import mock

from app.catalog import repo_root_from
from app.config import load_settings
from app.feedback import FeedbackError, fields_from_payload, format_feedback, history_from_payload
from app.list_feedback import main
from app.server import http_app
from app.tests.test_chat import call
from app.usage import UsageStore

ROOT = repo_root_from()
HISTORY = [
    {"role": "user", "content": "density at 10 km"},
    {"role": "assistant", "content": "0.41 kg/m^3"},
    {"role": "user", "content": "and at 20 km?"},
    {"role": "assistant", "content": "0.088 kg/m^3"},
]


class FakeTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {}

    def put_item(self, Item: dict[str, object]) -> None:
        self.items[(str(Item["pk"]), str(Item["sk"]))] = dict(Item)

    def query(self, KeyConditionExpression: object = None, ScanIndexForward: bool = True, Limit: int | None = None, **kwargs: object):
        del KeyConditionExpression, kwargs
        rows = [item for item in self.items.values() if item.get("pk") == "feedback"]
        rows.sort(key=lambda item: str(item.get("sk")), reverse=not ScanIndexForward)
        if Limit is not None:
            rows = rows[:Limit]
        return {"Items": rows}


def _settings(**overrides: str):
    env = {"USAGE_TABLE": "usage-test", "AUTH_DISABLED": "1", "DAILY_TOOL_CAP": "50"}
    env.update(overrides)
    with mock.patch.dict(os.environ, env, clear=False):
        return load_settings(str(ROOT))


class FeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = http_app()

    def test_requires_sign_in(self) -> None:
        env = {"AUTH_DISABLED": "", "USAGE_TABLE": "usage-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            status, data, _text, _headers = call(
                self.app,
                "POST",
                "/api/chat/feedback",
                {"reason": "wrong number", "history": HISTORY},
            )
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "sign-in is required")

    def test_rejects_empty_reason_and_missing_chat(self) -> None:
        with self.assertRaises(FeedbackError) as empty:
            fields_from_payload({"reason": "   ", "history": HISTORY})
        self.assertEqual(empty.exception.message, "say why")
        with self.assertRaises(FeedbackError) as missing:
            fields_from_payload({"reason": "wrong"})
        self.assertEqual(missing.exception.message, "send the chat")

    def test_keeps_the_chat_through_the_voted_reply(self) -> None:
        reason, message, user_message, history = fields_from_payload(
            {"reason": " units look off ", "history": HISTORY}
        )
        self.assertEqual(reason, "units look off")
        self.assertEqual(message, "0.088 kg/m^3")
        self.assertEqual(user_message, "and at 20 km?")
        self.assertEqual(len(history), 4)
        self.assertEqual(history[0]["content"], "density at 10 km")

    def test_drops_oldest_turns_when_the_chat_is_too_long(self) -> None:
        huge = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 8000} for i in range(20)]
        kept = history_from_payload({"history": huge})
        self.assertLessEqual(sum(len(turn["content"]) for turn in kept), 100_000)
        self.assertEqual(kept[-1]["content"], "x" * 8000)
        self.assertLess(len(kept), len(huge))

    def test_post_writes_history(self) -> None:
        fake = FakeTable()
        env = {"AUTH_DISABLED": "1", "USAGE_TABLE": "usage-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                status, data, _text, _headers = call(
                    self.app,
                    "POST",
                    "/api/chat/feedback",
                    {"reason": "the density is high", "history": HISTORY},
                )
        self.assertEqual(status, 200)
        self.assertEqual(data, {"ok": True})
        self.assertEqual(len(fake.items), 1)
        item = next(iter(fake.items.values()))
        self.assertEqual(item["pk"], "feedback")
        self.assertEqual(item["reason"], "the density is high")
        self.assertEqual(item["history"], HISTORY)
        self.assertEqual(item["message"], "0.088 kg/m^3")
        self.assertEqual(item["email"], "")

    def test_cli_prints_newest_chat(self) -> None:
        fake = FakeTable()
        fake.put_item(
            Item={
                "pk": "feedback",
                "sk": "2026-10-12T11:00:00.000000Z#a",
                "created": "2026-10-12T11:00:00.000000Z",
                "email": "pilot@example.com",
                "reason": "older",
                "history": [{"role": "user", "content": "first"}],
            }
        )
        fake.put_item(
            Item={
                "pk": "feedback",
                "sk": "2026-10-12T12:00:00.000000Z#b",
                "created": "2026-10-12T12:00:00.000000Z",
                "email": "pilot@example.com",
                "reason": "newer",
                "history": HISTORY,
            }
        )
        settings = _settings()
        with mock.patch("app.list_feedback.load_settings", return_value=settings):
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                output = io.StringIO()
                with mock.patch("sys.stdout", output):
                    code = main(["--limit", "1"])
        self.assertEqual(code, 0)
        text = output.getvalue()
        self.assertIn("newer", text)
        self.assertNotIn("older", text)
        self.assertIn("user: density at 10 km", text)
        self.assertIn("Astraeus: 0.088 kg/m^3", text)
        self.assertIn("pilot@example.com", text)

    def test_format_empty(self) -> None:
        self.assertEqual(format_feedback([]), "No feedback.")

    def test_chat_page_wires_votes(self) -> None:
        chat_js = (ROOT / "app" / "web" / "js" / "chat.js").read_text(encoding="utf-8")
        self.assertIn("Thumbs up", chat_js)
        self.assertIn("Thumbs down", chat_js)
        self.assertIn("/api/chat/feedback", chat_js)
        self.assertIn("history: historyThrough(index)", chat_js)
        html = (ROOT / "app" / "web" / "chat.html").read_text(encoding="utf-8")
        self.assertIn("/js/chat.js", html)


if __name__ == "__main__":
    unittest.main()
