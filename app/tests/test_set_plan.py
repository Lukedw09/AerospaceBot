"""Admin set_plan: assign free or unlimited with mocked boto3."""

from __future__ import annotations

import io
import os
import sys
import unittest
from unittest import mock

from app.catalog import repo_root_from
from app.config import load_settings
from app.set_plan import SetPlanError, main, set_plan
from app.usage import FREE_PLAN, UNLIMITED_DAILY_CAP, UNLIMITED_PLAN, UsageStore

ROOT = repo_root_from()
EMAIL = "pilot@example.com"
SUB = "user-sub-1"


class FakeTable:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict[str, object]] = {}

    def get_item(self, Key: dict[str, str]) -> dict[str, object]:
        item = self.items.get((Key["pk"], Key["sk"]))
        if item is None:
            return {}
        return {"Item": dict(item)}

    def put_item(self, Item: dict[str, object]) -> None:
        self.items[(str(Item["pk"]), str(Item["sk"]))] = dict(Item)

    def update_item(
        self,
        Key: dict[str, str],
        UpdateExpression: str,
        ExpressionAttributeNames: dict[str, str],
        ExpressionAttributeValues: dict[str, object],
    ) -> None:
        del UpdateExpression
        key = (Key["pk"], Key["sk"])
        item = dict(self.items.get(key) or {"pk": Key["pk"], "sk": Key["sk"]})
        name = ExpressionAttributeNames["#plan"]
        item[name] = ExpressionAttributeValues[":plan"]
        self.items[key] = item


def _settings(**overrides: str):
    env = {
        "USAGE_TABLE": "usage-test",
        "COGNITO_USER_POOL_ID": "pool-test",
        "COGNITO_REGION": "us-east-1",
        "DAILY_TOOL_CAP": "50",
        "AUTH_DISABLED": "1",
    }
    env.update(overrides)
    with mock.patch.dict(os.environ, env, clear=False):
        return load_settings(str(ROOT))


def _cognito_user(email: str = EMAIL, sub: str = SUB) -> dict[str, object]:
    return {
        "Users": [
            {
                "Username": sub,
                "Attributes": [
                    {"Name": "email", "Value": email},
                    {"Name": "sub", "Value": sub},
                ],
            }
        ]
    }


class SetPlanTests(unittest.TestCase):
    def test_set_unlimited(self) -> None:
        fake = FakeTable()
        fake.items[(f"account#{SUB}", "account")] = {
            "pk": f"account#{SUB}",
            "sk": "account",
            "sub": SUB,
            "email": EMAIL,
            "plan": FREE_PLAN,
        }
        settings = _settings()
        cognito = mock.Mock()
        cognito.list_users.return_value = _cognito_user()
        with mock.patch.object(UsageStore, "table", lambda self: fake):
            with mock.patch("app.set_plan._cognito", return_value=cognito):
                old, new = set_plan(EMAIL, UNLIMITED_PLAN, settings)
        self.assertEqual(old, FREE_PLAN)
        self.assertEqual(new, UNLIMITED_PLAN)
        self.assertEqual(fake.items[(f"account#{SUB}", "account")]["plan"], UNLIMITED_PLAN)
        plan = fake.items[(f"plan#{UNLIMITED_PLAN}", "plan")]
        self.assertEqual(plan["daily_cap"], UNLIMITED_DAILY_CAP)
        free = fake.items[(f"plan#{FREE_PLAN}", "plan")]
        self.assertEqual(free["daily_cap"], 50)

    def test_revert_to_free(self) -> None:
        fake = FakeTable()
        fake.items[(f"account#{SUB}", "account")] = {
            "pk": f"account#{SUB}",
            "sk": "account",
            "sub": SUB,
            "email": EMAIL,
            "plan": UNLIMITED_PLAN,
        }
        settings = _settings()
        cognito = mock.Mock()
        cognito.list_users.return_value = _cognito_user()
        with mock.patch.object(UsageStore, "table", lambda self: fake):
            with mock.patch("app.set_plan._cognito", return_value=cognito):
                old, new = set_plan(EMAIL, FREE_PLAN, settings)
        self.assertEqual(old, UNLIMITED_PLAN)
        self.assertEqual(new, FREE_PLAN)
        self.assertEqual(fake.items[(f"account#{SUB}", "account")]["plan"], FREE_PLAN)

    def test_unknown_email(self) -> None:
        fake = FakeTable()
        settings = _settings()
        cognito = mock.Mock()
        cognito.list_users.return_value = {"Users": []}
        with mock.patch.object(UsageStore, "table", lambda self: fake):
            with mock.patch("app.set_plan._cognito", return_value=cognito):
                with self.assertRaises(SetPlanError) as raised:
                    set_plan(EMAIL, UNLIMITED_PLAN, settings)
        self.assertIn(EMAIL, str(raised.exception))
        self.assertIn("No Cognito user", str(raised.exception))

    def test_unknown_plan(self) -> None:
        fake = FakeTable()
        fake.items[(f"account#{SUB}", "account")] = {
            "pk": f"account#{SUB}",
            "sk": "account",
            "sub": SUB,
            "email": EMAIL,
            "plan": FREE_PLAN,
        }
        settings = _settings()
        cognito = mock.Mock()
        cognito.list_users.return_value = _cognito_user()
        with mock.patch.object(UsageStore, "table", lambda self: fake):
            with mock.patch("app.set_plan._cognito", return_value=cognito):
                with self.assertRaises(SetPlanError) as raised:
                    set_plan(EMAIL, "enterprise", settings)
        self.assertIn("Plan not found", str(raised.exception))
        self.assertIn("enterprise", str(raised.exception))
        self.assertEqual(fake.items[(f"account#{SUB}", "account")]["plan"], FREE_PLAN)

    def test_main_prints_old_and_new(self) -> None:
        fake = FakeTable()
        fake.items[(f"account#{SUB}", "account")] = {
            "pk": f"account#{SUB}",
            "sk": "account",
            "sub": SUB,
            "email": EMAIL,
            "plan": FREE_PLAN,
        }
        cognito = mock.Mock()
        cognito.list_users.return_value = _cognito_user()
        env = {
            "USAGE_TABLE": "usage-test",
            "COGNITO_USER_POOL_ID": "pool-test",
            "COGNITO_REGION": "us-east-1",
            "DAILY_TOOL_CAP": "50",
        }
        buffer = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(UsageStore, "table", lambda self: fake):
                with mock.patch("app.set_plan._cognito", return_value=cognito):
                    with mock.patch("sys.stdout", buffer):
                        code = main(["--email", EMAIL, "--plan", "unlimited"])
        self.assertEqual(code, 0)
        text = buffer.getvalue()
        self.assertIn("old plan: free", text)
        self.assertIn("new plan: unlimited", text)
        with mock.patch.object(UsageStore, "table", lambda self: fake):
            name, cap, _pictures = UsageStore(_settings()).plan_cap(SUB)
        self.assertEqual(name, UNLIMITED_PLAN)
        self.assertEqual(cap, UNLIMITED_DAILY_CAP)


if __name__ == "__main__":
    unittest.main()
