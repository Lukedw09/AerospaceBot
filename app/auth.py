"""Check a Cognito access token. Local stdio sets AUTH_DISABLED and skips this."""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from app.config import Settings


@dataclass
class Identity:
    sub: str
    email: str
    username: str


class TokenError(Exception):
    pass


_jwks: dict[str, tuple[float, PyJWKClient]] = {}


def _client(settings: Settings) -> PyJWKClient:
    url = (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    cached = _jwks.get(url)
    now = time.time()
    if cached and now - cached[0] < 3600:
        return cached[1]
    client = PyJWKClient(url)
    _jwks[url] = (now, client)
    return client


def _decode(token: str, settings: Settings) -> dict:
    if not settings.cognito_user_pool_id or not settings.cognito_client_id:
        raise TokenError("sign-in is not configured")
    try:
        signing = _client(settings).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.PyJWTError as exc:
        raise TokenError("token is not valid") from exc
    issuer = (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}"
    )
    if claims.get("iss") != issuer:
        raise TokenError("token is not from this account list")
    if not isinstance(claims, dict):
        raise TokenError("token is not valid")
    return claims


def verify_id_token(token: str, settings: Settings) -> Identity:
    claims = _decode(token, settings)
    if claims.get("token_use") != "id":
        raise TokenError("token is not an id token")
    audience = claims.get("aud")
    if audience != settings.cognito_client_id:
        raise TokenError("token is not for this plugin")
    username = str(claims.get("cognito:username") or "")
    return Identity(
        sub=str(claims["sub"]),
        email=str(claims.get("email") or ""),
        username=username,
    )


def verify_access_token(token: str, settings: Settings) -> Identity:
    claims = _decode(token, settings)
    if claims.get("token_use") != "access":
        raise TokenError("token is not an access token")
    if claims.get("client_id") != settings.cognito_client_id:
        raise TokenError("token is not for this plugin")
    username = str(claims.get("username") or claims.get("cognito:username") or "")
    if username and not _user_enabled(settings, username):
        raise TokenError("account is disabled")
    email = str(claims.get("email") or "")
    if not email and username:
        email = _user_email(settings, username)
    return Identity(sub=str(claims["sub"]), email=email, username=username)


def _user_enabled(settings: Settings, username: str) -> bool:
    import boto3

    client = boto3.client("cognito-idp", region_name=settings.cognito_region)
    try:
        user = client.admin_get_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username,
        )
    except client.exceptions.UserNotFoundException:
        return False
    return bool(user.get("Enabled", True))


def _user_email(settings: Settings, username: str) -> str:
    import boto3

    client = boto3.client("cognito-idp", region_name=settings.cognito_region)
    try:
        user = client.admin_get_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=username,
        )
    except client.exceptions.UserNotFoundException:
        return ""
    for attr in user.get("UserAttributes", []):
        if attr.get("Name") == "email":
            return str(attr.get("Value") or "")
    return ""


def protected_resource_metadata(settings: Settings) -> dict[str, object]:
    resource = (settings.public_base_url or "http://127.0.0.1") + "/mcp"
    server = settings.public_base_url or settings.account_site_url
    return {
        "resource": resource,
        "authorization_servers": [server] if server else [],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
    }


def authorization_server_metadata(settings: Settings) -> dict[str, object]:
    import os

    domain = os.environ.get("COGNITO_DOMAIN", "").rstrip("/")
    issuer = settings.public_base_url or domain
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{domain}/oauth2/authorize" if domain else "",
        "token_endpoint": f"{domain}/oauth2/token" if domain else "",
        "scopes_supported": ["openid", "email", "profile"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["none"],
    }


def fetch_openid(settings: Settings) -> dict[str, object]:
    if not settings.cognito_user_pool_id:
        return {}
    url = (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com/"
        f"{settings.cognito_user_pool_id}/.well-known/openid-configuration"
    )
    with urllib.request.urlopen(url, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload if isinstance(payload, dict) else {}
