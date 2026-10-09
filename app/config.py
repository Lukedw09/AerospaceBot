"""Settings read from the environment. Secrets are not given defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


_ssm_client_id = ""


def _client_id() -> str:
    """Prefer the env value. The deployed function reads the id from SSM to avoid a stack cycle."""
    global _ssm_client_id
    direct = os.environ.get("COGNITO_CLIENT_ID", "").strip()
    if direct:
        return direct
    if _ssm_client_id:
        return _ssm_client_id
    name = os.environ.get("COGNITO_CLIENT_ID_PARAMETER", "").strip()
    if not name:
        return ""
    import boto3

    _ssm_client_id = str(boto3.client("ssm").get_parameter(Name=name)["Parameter"]["Value"])
    return _ssm_client_id


@dataclass(frozen=True)
class Settings:
    auth_disabled: bool
    repo_root: str
    usage_table: str
    picture_bucket: str
    daily_tool_cap: int
    tool_timeout_sec: int
    result_link_hours: int
    usage_timezone: str
    cognito_user_pool_id: str
    cognito_client_id: str
    cognito_region: str
    public_base_url: str
    account_site_url: str
    result_link_secret: str = ""


def load_settings(repo_root: str) -> Settings:
    return Settings(
        auth_disabled=_flag("AUTH_DISABLED"),
        repo_root=repo_root,
        usage_table=os.environ.get("USAGE_TABLE", ""),
        picture_bucket=os.environ.get("PICTURE_BUCKET", ""),
        daily_tool_cap=int(os.environ.get("DAILY_TOOL_CAP", "2000")),
        tool_timeout_sec=int(os.environ.get("TOOL_TIMEOUT_SEC", "60")),
        result_link_hours=int(os.environ.get("RESULT_LINK_HOURS", "1")),
        usage_timezone=os.environ.get("USAGE_TIMEZONE", "America/New_York"),
        cognito_user_pool_id=os.environ.get("COGNITO_USER_POOL_ID", ""),
        cognito_client_id=_client_id(),
        cognito_region=os.environ.get("COGNITO_REGION", os.environ.get("AWS_REGION", "us-east-1")),
        public_base_url=os.environ.get("PUBLIC_BASE_URL", "").rstrip("/"),
        account_site_url=os.environ.get("ACCOUNT_SITE_URL", "").rstrip("/"),
        result_link_secret=os.environ.get("RESULT_LINK_SECRET", ""),
    )
