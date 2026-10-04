"""Daily tool-call counter. DynamoDB when configured, otherwise no limit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import Settings

FREE_PLAN = "free"


@dataclass
class Decision:
    allowed: bool
    message: str
    sub: str
    email: str


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

    def plan_cap(self, sub: str) -> tuple[str, int, bool]:
        table = self.table()
        plan_name = FREE_PLAN
        if table is not None:
            account = table.get_item(Key={"pk": f"account#{sub}", "sk": "account"}).get("Item")
            if account:
                plan_name = str(account.get("plan") or FREE_PLAN)
            plan = table.get_item(Key={"pk": f"plan#{plan_name}", "sk": "plan"}).get("Item")
            if plan:
                return (
                    plan_name,
                    int(plan.get("daily_cap", self.settings.daily_tool_cap)),
                    bool(plan.get("pictures", True)),
                )
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
        if not self.settings.usage_table:
            return Decision(True, "", sub, email)
        self.ensure_account(sub, email)
        _plan, cap, _pictures = self.plan_cap(sub)
        used = self.used_today(sub)
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
        table = self.table()
        if table is None:
            return
        table.update_item(
            Key={"pk": f"usage#{sub}", "sk": self.today()},
            UpdateExpression="ADD #count :one",
            ExpressionAttributeNames={"#count": "count"},
            ExpressionAttributeValues={":one": 1},
        )

    def snapshot(self, sub: str) -> dict[str, object]:
        table = self.table()
        account = {}
        if table is not None:
            account = table.get_item(Key={"pk": f"account#{sub}", "sk": "account"}).get("Item") or {}
        plan_name, cap, pictures = self.plan_cap(sub)
        return {
            "sub": sub,
            "email": account.get("email", ""),
            "plan": plan_name,
            "used_today": self.used_today(sub),
            "daily_cap": cap,
            "pictures": pictures,
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
