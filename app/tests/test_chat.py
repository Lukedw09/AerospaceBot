"""Chat route: auth, quotas, tool rejection, and a mocked Grok loop."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest import mock

from app.auth import Identity
from app.catalog import load_catalog, repo_root_from
from app.config import load_settings
from app.server import http_app, run_tool
from app.usage import UsageStore

ROOT = repo_root_from()
SENTINEL = "sk-test-SENTINEL-do-not-leak"
SUB = "chat-user"
IDENTITY = Identity(sub=SUB, email="pilot@example.com", username="pilot")


class FakeTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {}

    def get_item(self, Key: dict[str, str]) -> dict[str, object]:
        item = self.items.get((Key["pk"], Key["sk"]))
        if item is None:
            return {}
        return {"Item": item}

    def put_item(self, Item: dict[str, object]) -> None:
        self.items[(str(Item["pk"]), str(Item["sk"]))] = dict(Item)

    def update_item(
        self,
        Key: dict[str, str],
        UpdateExpression: str,
        ExpressionAttributeNames: dict[str, str],
        ExpressionAttributeValues: dict[str, int],
    ) -> None:
        del UpdateExpression, ExpressionAttributeNames
        key = (Key["pk"], Key["sk"])
        item = dict(self.items.get(key) or {"pk": Key["pk"], "sk": Key["sk"], "count": 0})
        item["count"] = int(item.get("count", 0)) + int(ExpressionAttributeValues[":one"])
        self.items[key] = item


def _headers(token: str | None, body: bytes) -> list[tuple[bytes, bytes]]:
    headers = [(b"host", b"localhost")]
    if body:
        headers.append((b"content-type", b"application/json"))
    if token:
        headers.append((b"authorization", f"Bearer {token}".encode("utf-8")))
    return headers


def call(app: object, method: str, path: str, payload: dict[str, object] | None = None, token: str | None = None):
    body = b"" if payload is None else json.dumps(payload).encode("utf-8")
    sent: dict[str, object] = {"body": b""}
    delivered = {"done": False}

    async def receive():
        if not delivered["done"]:
            delivered["done"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        if message["type"] == "http.response.start":
            sent["status"] = message["status"]
            sent["headers"] = message.get("headers", [])
        elif message["type"] == "http.response.body":
            sent["body"] = sent["body"] + message.get("body", b"")

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": _headers(token, body),
        "client": ("127.0.0.1", 50000),
        "server": ("127.0.0.1", 8080),
    }
    asyncio.run(app(scope, receive, send))
    raw = sent.get("body", b"")
    text = raw.decode("utf-8") if isinstance(raw, bytes) else ""
    data: object = None
    if text and text[:1] in "{[":
        data = json.loads(text)
    return int(sent["status"]), data, text, sent.get("headers", [])


def tool_call(name: str, arguments: dict[str, object], call_id: str = "call-1") -> dict[str, object]:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": call_id,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(arguments)},
            }
        ],
    }


def final(text: str) -> dict[str, object]:
    return {"role": "assistant", "content": text, "tool_calls": []}


class ChatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = http_app()
        from app.chat import _tools

        cls.tools, _names = _tools()

    def assert_key_hidden(self, text: str, headers: object) -> None:
        self.assertNotIn(SENTINEL, text)
        for key, value in headers:  # type: ignore[union-attr]
            self.assertNotIn(SENTINEL, key.decode("latin1"))
            self.assertNotIn(SENTINEL, value.decode("latin1"))

    def test_example_requests_may_choose_inputs(self) -> None:
        from app.chat import SYSTEM_PROMPT

        self.assertIn("explicitly asks for an example", SYSTEM_PROMPT)
        self.assertIn("random values", SYSTEM_PROMPT)
        self.assertIn("Do not choose inputs unless they asked for an example", SYSTEM_PROMPT)

    def test_chat_page_is_served_at_chat(self) -> None:
        status, _data, text, headers = call(self.app, "GET", "/chat")
        self.assertEqual(status, 200)
        self.assertIn("Sign in to chat", text)
        media = {key.decode("latin1"): value.decode("latin1") for key, value in headers}
        self.assertIn("text/html", media.get("content-type", ""))

    def test_auth_is_required(self) -> None:
        def explode(*_args, **_kwargs):
            raise AssertionError("grok was called")

        env = {"AUTH_DISABLED": "", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=explode):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "hello"}]},
                )
        self.assertEqual(status, 401)
        self.assertEqual(data["error"], "sign-in is required")
        self.assert_key_hidden(text, headers)

    def test_local_status_skips_sign_in(self) -> None:
        env = {"AUTH_DISABLED": "1", "USAGE_TABLE": "", "DAILY_TOOL_CAP": "50", "GROK_API_KEY": SENTINEL}
        with mock.patch.dict(os.environ, env, clear=False):
            status, data, text, headers = call(self.app, "GET", "/api/chat/status")
        self.assertEqual(status, 200)
        self.assertFalse(data["sign_in_required"])
        self.assertEqual(data["daily_cap"], 50)
        self.assertEqual(data["remaining"], 50)
        self.assert_key_hidden(text, headers)

    def test_unknown_tool_is_rejected(self) -> None:
        calls = {"n": 0}

        def grok(*_args, **_kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return tool_call("not_a_real_tool", {})
            return final("No such tool.")

        ran: list[str] = []
        real = run_tool

        def spy(tool, arguments, **kwargs):
            ran.append(tool.name)
            return real(tool, arguments, **kwargs)

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                with mock.patch("app.server.run_tool", side_effect=spy):
                    status, data, text, headers = call(
                        self.app,
                        "POST",
                        "/api/chat",
                        {"messages": [{"role": "user", "content": "run a made up tool"}]},
                    )
        self.assertEqual(status, 200)
        self.assertEqual(data["details"][0]["output"], "that tool is not in the library")
        self.assertEqual(ran, [])
        self.assert_key_hidden(text, headers)

    def test_unknown_argument_is_rejected(self) -> None:
        calls = {"n": 0}

        def grok(*_args, **_kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return tool_call("hohmann_transfer", {"nope": 1})
            return final("Ask for the radii.")

        ran: list[str] = []

        def spy(tool, arguments, **kwargs):
            ran.append(tool.name)
            raise AssertionError("program ran")

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                with mock.patch("app.server.run_tool", side_effect=spy):
                    status, data, text, headers = call(
                        self.app,
                        "POST",
                        "/api/chat",
                        {"messages": [{"role": "user", "content": "transfer"}]},
                    )
        self.assertEqual(status, 200)
        self.assertIn("unknown parameter 'nope'", data["details"][0]["output"])
        self.assertIn("valid parameters:", data["details"][0]["output"])
        self.assertEqual(ran, [])
        self.assert_key_hidden(text, headers)

    def test_cap_blocks_before_grok(self) -> None:
        fake = FakeTable()
        env = {
            "AUTH_DISABLED": "",
            "USAGE_TABLE": "chat-test",
            "DAILY_TOOL_CAP": "2",
            "GROK_API_KEY": SENTINEL,
            "GROK_MODEL": "grok-test",
            "PICTURE_BUCKET": "",
        }

        def explode(*_args, **_kwargs):
            raise AssertionError("grok was called")

        with mock.patch.dict(os.environ, env, clear=False):
            day = UsageStore(load_settings(str(ROOT))).today()
            fake.items[(f"usage#{SUB}", day)] = {"pk": f"usage#{SUB}", "sk": day, "count": 2}
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                with mock.patch("app.server.verify_access_token", return_value=IDENTITY):
                    with mock.patch("app.chat.complete", side_effect=explode):
                        status, data, text, headers = call(
                            self.app,
                            "POST",
                            "/api/chat",
                            {"messages": [{"role": "user", "content": "hello"}]},
                            token="test-token",
                        )
        self.assertEqual(status, 200)
        self.assertTrue(data["answer"].startswith("Daily limit reached"))
        self.assertEqual(data["stopped"], "limit")
        self.assertEqual(data["details"], [])
        self.assert_key_hidden(text, headers)

    def test_cap_stops_mid_loop(self) -> None:
        fake = FakeTable()
        calls = {"n": 0}
        ran: list[str] = []
        real = run_tool

        def grok(*_args, **_kwargs):
            calls["n"] += 1
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "one",
                        "type": "function",
                        "function": {
                            "name": "throat_sizing",
                            "arguments": json.dumps(
                                {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600}
                            ),
                        },
                    },
                    {
                        "id": "two",
                        "type": "function",
                        "function": {
                            "name": "hohmann_transfer",
                            "arguments": json.dumps({"r1": 6774200, "r2": 7374200}),
                        },
                    },
                ],
            }

        def spy(tool, arguments, **kwargs):
            ran.append(tool.name)
            return real(tool, arguments, **kwargs)

        env = {
            "AUTH_DISABLED": "",
            "USAGE_TABLE": "chat-test",
            "DAILY_TOOL_CAP": "2",
            "GROK_API_KEY": SENTINEL,
            "GROK_MODEL": "grok-test",
            "PICTURE_BUCKET": "",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                with mock.patch("app.server.verify_access_token", return_value=IDENTITY):
                    with mock.patch("app.chat.complete", side_effect=grok):
                        with mock.patch("app.server.run_tool", side_effect=spy):
                            status, data, text, headers = call(
                                self.app,
                                "POST",
                                "/api/chat",
                                {"messages": [{"role": "user", "content": "size a throat and transfer"}]},
                                token="test-token",
                            )
        self.assertEqual(status, 200)
        self.assertEqual(calls["n"], 1)
        self.assertEqual(ran, ["throat_sizing"])
        self.assertTrue(data["answer"].startswith("Daily limit reached"))
        self.assertEqual(data["stopped"], "limit")
        self.assertEqual(data["details"][1]["tool"], "hohmann_transfer")
        self.assert_key_hidden(text, headers)

    def test_tool_rounds_stop_at_eight(self) -> None:
        calls = {"n": 0}

        def grok(*_args, **_kwargs):
            calls["n"] += 1
            return tool_call("not_a_real_tool", {}, f"call-{calls['n']}")

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "keep going"}]},
                )
        self.assertEqual(status, 200)
        self.assertEqual(calls["n"], 8)
        self.assertEqual(data["stopped"], "rounds")
        self.assertEqual(data["answer"], "Stopped after 8 tool rounds.")
        self.assertEqual(len(data["details"]), 8)
        self.assert_key_hidden(text, headers)

    def test_placeholder_key_is_not_sent(self) -> None:
        def explode(*_args, **_kwargs):
            raise AssertionError("grok was called")

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": "<your xAI key>", "GROK_MODEL": "grok-4.7"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=explode):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "hello"}]},
                )
        self.assertEqual(status, 503)
        self.assertIn("console.x.ai", data["error"])
        self.assert_key_hidden(text, headers)

    def test_tool_crash_returns_json(self) -> None:
        calls = {"n": 0}

        def grok(*_args, **_kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                return tool_call("hohmann_transfer", {"r1": 1, "r2": 2})
            return final("The tool failed.")

        def boom(*_args, **_kwargs):
            raise RuntimeError("plot exploded")

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                with mock.patch("app.chat._run_tool", side_effect=boom):
                    status, data, text, headers = call(
                        self.app,
                        "POST",
                        "/api/chat",
                        {"messages": [{"role": "user", "content": "show an example"}]},
                    )
        self.assertEqual(status, 200)
        self.assertEqual(data["details"][0]["output"], "that tool failed")
        self.assertEqual(data["answer"], "The tool failed.")
        self.assertNotIn("plot exploded", text)
        self.assert_key_hidden(text, headers)

    def test_tool_followup_sends_empty_content(self) -> None:
        seen: list[list[dict[str, object]]] = []

        def grok(messages, *_args, **_kwargs):
            seen.append(messages)
            if len(seen) == 1:
                return {"role": "assistant", "content": None, "tool_calls": tool_call("not_a_real_tool", {})["tool_calls"]}
            return final("Example ready.")

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "Provide an example."}]},
                )
        self.assertEqual(status, 200)
        self.assertEqual(data["answer"], "Example ready.")
        followup = [item for item in seen[1] if item.get("tool_calls")]
        self.assertEqual(followup[0]["content"], "")
        self.assertIsInstance(followup[0]["content"], str)
        self.assert_key_hidden(text, headers)

    def test_summary_failure_keeps_the_tool_result(self) -> None:
        from app.chat import GrokError

        def grok(messages, *_args, **_kwargs):
            if any(item.get("role") == "tool" for item in messages):
                raise GrokError()
            return tool_call("not_a_real_tool", {})

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "Provide an example and include a png."}]},
                )
        self.assertEqual(status, 200)
        self.assertEqual(data["details"][0]["output"], "that tool is not in the library")
        self.assertIn("summary did not come back", data["answer"])
        self.assertNotIn("did not answer", data.get("error", ""))
        self.assert_key_hidden(text, headers)

    def test_grok_failure_hides_the_key(self) -> None:
        def grok(*_args, **_kwargs):
            raise RuntimeError(SENTINEL)

        env = {"AUTH_DISABLED": "1", "GROK_API_KEY": SENTINEL, "GROK_MODEL": "grok-test"}
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "hello"}]},
                )
        self.assertEqual(status, 502)
        self.assertEqual(data["error"], "The chat service did not answer.")
        self.assert_key_hidden(text, headers)

    def test_hohmann_transfer_end_to_end(self) -> None:
        calls = {"n": 0}
        seen: list[str] = []

        def grok(_messages, tools, _model, _key, timeout=70):
            calls["n"] += 1
            if calls["n"] == 1:
                seen.extend(tool["function"]["name"] for tool in tools)
                return tool_call("hohmann_transfer", {"r1": 6774200, "r2": 7374200})
            return final("Quoted from the tool.")

        env = {
            "AUTH_DISABLED": "1",
            "GROK_API_KEY": SENTINEL,
            "GROK_MODEL": "grok-test",
            "PICTURE_BUCKET": "",
            "USAGE_TABLE": "",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.chat.complete", side_effect=grok):
                status, data, text, headers = call(
                    self.app,
                    "POST",
                    "/api/chat",
                    {"messages": [{"role": "user", "content": "Hohmann from 6774200 m to 7374200 m"}]},
                )
        self.assertEqual(status, 200)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(data["answer"], "Quoted from the tool.")
        self.assertEqual(data["details"][0]["tool"], "hohmann_transfer")
        self.assertIn("dv_m_s:", data["details"][0]["output"])
        self.assertEqual(len(seen), len(load_catalog(ROOT)) + 2)
        self.assertEqual(len(seen), 141)
        self.assertIn("hohmann_transfer", seen)
        self.assertIn("list_tools", seen)
        self.assertIn("lookup_formula", seen)
        plots = data["plots"]
        self.assertTrue(plots)
        self.assertTrue(plots[0]["src"].startswith("data:image/png;base64,"))
        self.assert_key_hidden(text, headers)


if __name__ == "__main__":
    unittest.main()
