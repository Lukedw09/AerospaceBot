"""Assign a usage plan to a Cognito user by email.

  python -m app.set_plan --email user@example.com --plan unlimited
  python -m app.set_plan --email user@example.com --plan free
"""

from __future__ import annotations

import argparse
import sys

from app.catalog import repo_root_from
from app.config import Settings, load_settings
from app.usage import UsageStore


class SetPlanError(Exception):
    """Clear failure for missing email, plan, or account."""


def _cognito(settings: Settings):
    import boto3

    return boto3.client("cognito-idp", region_name=settings.cognito_region)


def sub_for_email(email: str, settings: Settings) -> str:
    if not settings.cognito_user_pool_id:
        raise SetPlanError("COGNITO_USER_POOL_ID is not set")
    response = _cognito(settings).list_users(
        UserPoolId=settings.cognito_user_pool_id,
        Filter=f'email = "{email}"',
        Limit=1,
    )
    users = response.get("Users") or []
    if not users:
        raise SetPlanError(f"No Cognito user with email {email}")
    attributes = {item["Name"]: item["Value"] for item in users[0].get("Attributes", [])}
    sub = attributes.get("sub") or users[0].get("Username") or ""
    if not sub:
        raise SetPlanError(f"Cognito user {email} has no sub")
    return str(sub)


def set_plan(email: str, plan: str, settings: Settings) -> tuple[str, str]:
    if not settings.usage_table:
        raise SetPlanError("USAGE_TABLE is not set")
    store = UsageStore(settings)
    table = store.table()
    if table is None:
        raise SetPlanError("USAGE_TABLE is not set")
    store.ensure_plans()
    plan_item = table.get_item(Key={"pk": f"plan#{plan}", "sk": "plan"}).get("Item")
    if not plan_item:
        raise SetPlanError(f"Plan not found: {plan}")
    sub = sub_for_email(email, settings)
    key = {"pk": f"account#{sub}", "sk": "account"}
    account = table.get_item(Key=key).get("Item")
    if not account:
        raise SetPlanError(
            f"No usage account for {email} (sub {sub}). Sign in once so the account row exists."
        )
    old = str(account.get("plan") or "")
    table.update_item(
        Key=key,
        UpdateExpression="SET #plan = :plan",
        ExpressionAttributeNames={"#plan": "plan"},
        ExpressionAttributeValues={":plan": plan},
    )
    return old, plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Assign a usage plan by Cognito email.")
    parser.add_argument("--email", required=True, help="Cognito user email")
    parser.add_argument("--plan", required=True, help="Plan name (free or unlimited)")
    args = parser.parse_args(argv)
    settings = load_settings(str(repo_root_from()))
    try:
        old, new = set_plan(args.email.strip(), args.plan.strip(), settings)
    except SetPlanError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"old plan: {old}")
    print(f"new plan: {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
