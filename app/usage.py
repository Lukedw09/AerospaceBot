"""Daily tool-call counter. DynamoDB when configured. Unconfigured or broken stores refuse."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import Settings

FREE_PLAN = "free"
UNLIMITED_PLAN = "unlimited"
UNLIMITED_DAILY_CAP = 1_000_000
OWNER_EMAIL = "lukedw09@gmail.com"
UNCONFIGURED_MESSAGE = "Usage tracking is not configured, so this tool call was refused."
FAILED_MESSAGE = "Usage tracking failed, so this tool call was refused."


@dataclass
class Decision:
    allowed: bool
    message: str
    sub: str
    email: str


class UsageError(Exception):
    """The usage store could not be read or updated. Callers must refuse the tool."""


def owner_emails_for(settings: Settings) -> set[str]:
    """Emails on the unlimited plan. An empty setting keeps the built-in owner."""
    raw = settings.owner_unlimited_emails.strip()
    if not raw:
        return {OWNER_EMAIL}
    found = {part.strip().lower() for part in raw.split(",") if part.strip()}
    return found or {OWNER_EMAIL}


class UsageStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._table = None

    def table(self):
        if self._table is None and self.settings.usage_table:
            import boto3

            self._table = boto3.resource("dynamodb").Table(self.settings.usage_table)
        return self._table

    def today(self) -> str:
        zone = ZoneInfo(self.settings.usage_timezone)
        return datetime.now(zone).date().isoformat()

    def _owner(self, email: str) -> bool:
        return email.strip().lower() in owner_emails_for(self.settings)

    def ensure_plans(self) -> None:
        """Create plan rows when missing. Free stays at the configured daily cap."""
        table = self.table()
        if table is None:
            return
        for name, cap in (
            (FREE_PLAN, self.settings.daily_tool_cap),
            (UNLIMITED_PLAN, UNLIMITED_DAILY_CAP),
        ):
            key = {"pk": f"plan#{name}", "sk": "plan"}
            if table.get_item(Key=key).get("Item"):
                continue
            table.put_item(
                Item={
                    "pk": f"plan#{name}",
                    "sk": "plan",
                    "daily_cap": cap,
                    "pictures": True,
                }
            )

    def ensure_account(self, sub: str, email: str) -> None:
        table = self.table()
        if table is None:
            return
        existing = table.get_item(Key={"pk": f"account#{sub}", "sk": "account"}).get("Item")
        if existing:
            return
        table.put_item(
            Item={
                "pk": f"account#{sub}",
                "sk": "account",
                "sub": sub,
                "email": email,
                "plan": FREE_PLAN,
                "created": datetime.now(ZoneInfo("UTC")).isoformat(),
            }
        )

    def plan_cap(self, sub: str, email: str = "") -> tuple[str, int, bool]:
        table = self.table()
        plan_name = FREE_PLAN
        account_email = ""
        if table is not None:
            self.ensure_plans()
            account = table.get_item(Key={"pk": f"account#{sub}", "sk": "account"}).get("Item")
            if account:
                account_email = str(account.get("email") or "")
                plan_name = str(account.get("plan") or FREE_PLAN)
            if self._owner(email) or self._owner(account_email):
                return UNLIMITED_PLAN, UNLIMITED_DAILY_CAP, True
            plan = table.get_item(Key={"pk": f"plan#{plan_name}", "sk": "plan"}).get("Item")
            if plan:
                return (
                    plan_name,
                    int(plan.get("daily_cap", self.settings.daily_tool_cap)),
                    bool(plan.get("pictures", True)),
                )
        if self._owner(email):
            return UNLIMITED_PLAN, UNLIMITED_DAILY_CAP, True
        return plan_name, self.settings.daily_tool_cap, True

    def used_today(self, sub: str) -> int:
        table = self.table()
        if table is None:
            return 0
        item = table.get_item(Key={"pk": f"usage#{sub}", "sk": self.today()}).get("Item")
        if not item:
            return 0
        return int(item.get("count", 0))

    def check(self, sub: str, email: str) -> Decision:
        if self.settings.usage_cap_dev_bypass:
            return Decision(True, "", sub, email)
        if not self.settings.usage_table:
            return Decision(False, UNCONFIGURED_MESSAGE, sub, email)
        try:
            self.ensure_account(sub, email)
            _plan, cap, _pictures = self.plan_cap(sub, email)
            used = self.used_today(sub)
        except Exception as exc:
            _log_usage_error(exc)
            return Decision(False, FAILED_MESSAGE, sub, email)
        if used >= cap:
            return Decision(
                False,
                (
                    f"Daily limit reached ({used} of {cap} tool calls). "
                    f"The count resets at midnight {self.settings.usage_timezone}."
                ),
                sub,
                email,
            )
        return Decision(True, "", sub, email)

    def commit(self, sub: str) -> None:
        if self.settings.usage_cap_dev_bypass:
            return
        if not self.settings.usage_table:
            raise UsageError(UNCONFIGURED_MESSAGE)
        try:
            table = self.table()
            if table is None:
                raise UsageError(UNCONFIGURED_MESSAGE)
            table.update_item(
                Key={"pk": f"usage#{sub}", "sk": self.today()},
                UpdateExpression="ADD #count :one",
                ExpressionAttributeNames={"#count": "count"},
                ExpressionAttributeValues={":one": 1},
            )
        except UsageError:
            raise
        except Exception as exc:
            _log_usage_error(exc)
            raise UsageError(FAILED_MESSAGE) from exc

    def snapshot(self, sub: str, email: str = "") -> dict[str, object]:
        try:
            table = self.table()
            account = {}
            if table is not None:
                account = table.get_item(Key={"pk": f"account#{sub}", "sk": "account"}).get("Item") or {}
            plan_name, cap, pictures = self.plan_cap(sub, email or str(account.get("email") or ""))
            return {
                "sub": sub,
                "email": account.get("email", ""),
                "plan": plan_name,
                "used_today": self.used_today(sub),
                "daily_cap": cap,
                "pictures": pictures,
            }
        except Exception as exc:
            _log_usage_error(exc)
            return {
                "sub": sub,
                "email": email,
                "plan": FREE_PLAN,
                "used_today": 0,
                "daily_cap": 0,
                "pictures": False,
            }

    def delete_user(self, sub: str) -> None:
        table = self.table()
        if table is None:
            return
        from boto3.dynamodb.conditions import Key

        table.delete_item(Key={"pk": f"account#{sub}", "sk": "account"})
        query_key = Key("pk").eq(f"usage#{sub}")
        pages = table.query(KeyConditionExpression=query_key)
        items = list(pages.get("Items", []))
        while pages.get("LastEvaluatedKey"):
            pages = table.query(
                KeyConditionExpression=query_key,
                ExclusiveStartKey=pages["LastEvaluatedKey"],
            )
            items.extend(pages.get("Items", []))
        for item in items:
            table.delete_item(Key={"pk": item["pk"], "sk": item["sk"]})


def _log_usage_error(exc: Exception) -> None:
    print(f"usage store error: {type(exc).__name__}: {exc}", file=sys.stderr)
