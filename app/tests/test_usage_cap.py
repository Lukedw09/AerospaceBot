"""Usage cap fails closed, except for the local dev bypass."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from botocore.exceptions import ClientError

from app.auth import Identity
from app.catalog import repo_root_from
from app.config import assert_no_usage_bypass_on_lambda, load_settings
from app.server import _identity, dispatch_calculation, http_app
from app.usage import (
    FAILED_MESSAGE,
    OWNER_EMAIL,
    UNCONFIGURED_MESSAGE,
    UNLIMITED_DAILY_CAP,
    UNLIMITED_PLAN,
    UsageStore,
    owner_emails_for,
)

ROOT = repo_root_from()
SUB = "usage-user"
EMAIL = "pilot@example.com"
IDENTITY = Identity(sub=SUB, email=EMAIL, username="pilot")


def _client_error(operation: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "rate exceeded"}},
        operation,
    )


class BoomTable:
    def get_item(self, Key: dict[str, str]) -> dict[str, object]:
        del Key
        raise _client_error("GetItem")

    def put_item(self, Item: dict[str, object]) -> None:
        del Item
        raise _client_error("PutItem")

    def update_item(self, **kwargs: object) -> None:
        del kwargs
        raise _client_error("UpdateItem")


class CommitBoom:
    """Reads succeed. The usage increment fails after the program has run."""

    def get_item(self, Key: dict[str, str]) -> dict[str, object]:
        pk = Key["pk"]
        if pk.startswith("plan#"):
            return {"Item": {"pk": pk, "sk": "plan", "daily_cap": 50, "pictures": True}}
        if pk.startswith("account#"):
            return {
                "Item": {
                    "pk": pk,
                    "sk": "account",
                    "sub": SUB,
                    "email": EMAIL,
                    "plan": "free",
                }
            }
        return {}

    def put_item(self, Item: dict[str, object]) -> None:
        del Item

    def update_item(self, **kwargs: object) -> None:
        del kwargs
        raise _client_error("UpdateItem")


def _env(**overrides: str) -> dict[str, str]:
    base = {
        "AUTH_DISABLED": "1",
        "USAGE_TABLE": "",
        "USAGE_CAP_DEV_BYPASS": "",
        "OWNER_UNLIMITED_EMAILS": "",
        "DAILY_TOOL_CAP": "50",
    }
    base.update(overrides)
    return base


class UsageCapTests(unittest.TestCase):
    def test_unconfigured_store_refuses(self) -> None:
        with mock.patch.dict(os.environ, _env(), clear=False):
            decision = UsageStore(load_settings(str(ROOT))).check(SUB, EMAIL)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.message, UNCONFIGURED_MESSAGE)

    def test_dev_bypass_allows_an_unconfigured_store(self) -> None:
        with mock.patch.dict(os.environ, _env(USAGE_CAP_DEV_BYPASS="1"), clear=False):
            decision = UsageStore(load_settings(str(ROOT))).check(SUB, EMAIL)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.message, "")

    def test_auth_disabled_does_not_skip_an_unconfigured_store(self) -> None:
        env = _env(AUTH_DISABLED="1", USAGE_TABLE="", USAGE_CAP_DEV_BYPASS="")
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch("app.server.run_tool", side_effect=AssertionError("program ran")):
                text = dispatch_calculation(
                    "throat_sizing",
                    {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
                )
        self.assertEqual(text, UNCONFIGURED_MESSAGE)
        self.assertNotIn("At_m2", text)

    def test_dev_bypass_still_runs_the_program(self) -> None:
        env = _env(AUTH_DISABLED="1", USAGE_CAP_DEV_BYPASS="1")
        with mock.patch.dict(os.environ, env, clear=False):
            text = dispatch_calculation(
                "throat_sizing",
                {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
            )
        self.assertIn("At_m2: 0.0005", text)

    def test_dynamodb_error_refuses_before_the_program(self) -> None:
        env = _env(AUTH_DISABLED="1", USAGE_TABLE="usage-prod", USAGE_CAP_DEV_BYPASS="")
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: BoomTable()):
                with mock.patch("app.server.run_tool", side_effect=AssertionError("program ran")):
                    text = dispatch_calculation(
                        "throat_sizing",
                        {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
                    )
        self.assertEqual(text, FAILED_MESSAGE)
        self.assertNotIn("At_m2", text)

    def test_commit_error_hides_the_result(self) -> None:
        env = _env(AUTH_DISABLED="1", USAGE_TABLE="usage-prod", USAGE_CAP_DEV_BYPASS="")
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: CommitBoom()):
                text = dispatch_calculation(
                    "throat_sizing",
                    {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
                )
        self.assertEqual(text, FAILED_MESSAGE)
        self.assertNotIn("At_m2", text)

    def test_signed_in_chat_refuses_before_grok_when_dynamodb_errors(self) -> None:
        from app.tests.test_chat import SENTINEL, call

        def explode(*_args, **_kwargs):
            raise AssertionError("grok was called")

        env = _env(
            AUTH_DISABLED="",
            USAGE_TABLE="usage-prod",
            USAGE_CAP_DEV_BYPASS="",
            GROK_API_KEY=SENTINEL,
            GROK_MODEL="grok-test",
        )
        app = http_app()
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: BoomTable()):
                with mock.patch("app.server.verify_access_token", return_value=IDENTITY):
                    with mock.patch("app.chat.complete", side_effect=explode):
                        status, data, _text, _headers = call(
                            app,
                            "POST",
                            "/api/chat",
                            {"messages": [{"role": "user", "content": "hello"}]},
                            token="test-token",
                        )
        self.assertEqual(status, 200)
        self.assertEqual(data["answer"], FAILED_MESSAGE)
        self.assertEqual(data["stopped"], "limit")
        self.assertEqual(data["details"], [])

    def test_empty_owner_list_falls_back_to_the_builtin_email(self) -> None:
        with mock.patch.dict(os.environ, _env(OWNER_UNLIMITED_EMAILS=""), clear=False):
            settings = load_settings(str(ROOT))
        self.assertEqual(owner_emails_for(settings), {OWNER_EMAIL})
        self.assertIn("lukedw09@gmail.com", owner_emails_for(settings))

    def test_owner_list_comes_from_the_environment(self) -> None:
        fake = CommitBoom()
        env = _env(
            USAGE_TABLE="usage-prod",
            OWNER_UNLIMITED_EMAILS="other@example.com, lukedw09@gmail.com",
        )
        with mock.patch.dict(os.environ, env, clear=False):
            settings = load_settings(str(ROOT))
            store = UsageStore(settings)
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                owner_name, owner_cap, _pictures = store.plan_cap(SUB, "Other@example.com")
                stranger_name, stranger_cap, _pictures = store.plan_cap(SUB, "pilot@example.com")
        self.assertEqual(owner_emails_for(settings), {"other@example.com", "lukedw09@gmail.com"})
        self.assertEqual(owner_name, UNLIMITED_PLAN)
        self.assertEqual(owner_cap, UNLIMITED_DAILY_CAP)
        self.assertEqual(stranger_name, "free")
        self.assertEqual(stranger_cap, 50)

    def test_template_sets_owner_unlimited_emails(self) -> None:
        text = (ROOT / "app" / "template.yaml").read_text(encoding="utf-8")
        self.assertIn("OWNER_UNLIMITED_EMAILS: lukedw09@gmail.com", text)
        self.assertNotIn("USAGE_CAP_DEV_BYPASS", text)

    def test_lambda_refuses_to_start_with_the_dev_bypass(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"AWS_LAMBDA_FUNCTION_NAME": "aerospace", "USAGE_CAP_DEV_BYPASS": "1"},
            clear=False,
        ):
            with self.assertRaises(SystemExit) as raised:
                assert_no_usage_bypass_on_lambda()
            self.assertIn("USAGE_CAP_DEV_BYPASS", str(raised.exception))
            with self.assertRaises(SystemExit):
                http_app()
        with mock.patch.dict(
            os.environ,
            {"AWS_LAMBDA_FUNCTION_NAME": "aerospace", "USAGE_CAP_DEV_BYPASS": ""},
            clear=False,
        ):
            assert_no_usage_bypass_on_lambda()
        with mock.patch.dict(
            os.environ,
            {"AWS_LAMBDA_FUNCTION_NAME": "", "USAGE_CAP_DEV_BYPASS": "1"},
            clear=False,
        ):
            assert_no_usage_bypass_on_lambda()

    def test_version(self) -> None:
        import app

        self.assertEqual(app.__version__, "11.4.0")
        notes = Path(ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        self.assertIn("11.4.0", notes)
        self.assertIn("calculate", notes)


if __name__ == "__main__":
    unittest.main()
