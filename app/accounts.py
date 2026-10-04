"""Credential changes for the signed-in Cognito user."""

from __future__ import annotations

import json

from app.auth import Identity, TokenError, verify_id_token
from app.config import Settings
from app.pictures import delete_user_files
from app.usage import UsageStore


def _client(settings: Settings):
    import boto3

    return boto3.client("cognito-idp", region_name=settings.cognito_region)


def _attributes(user: dict) -> dict[str, str]:
    return {item["Name"]: item["Value"] for item in user.get("UserAttributes", [])}


def _identities(attributes: dict[str, str]) -> list[dict[str, str]]:
    raw = attributes.get("identities", "")
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def profile(identity: Identity, settings: Settings, store: UsageStore) -> dict[str, object]:
    user = _client(settings).admin_get_user(
        UserPoolId=settings.cognito_user_pool_id,
        Username=identity.username or identity.sub,
    )
    attributes = _attributes(user)
    linked = [
        {"provider": item.get("providerName", ""), "userId": item.get("userId", "")}
        for item in _identities(attributes)
    ]
    if not linked and identity.username and "_" in identity.username:
        provider, _, user_id = identity.username.partition("_")
        linked = [{"provider": provider, "userId": user_id}]
    snapshot = store.snapshot(identity.sub)
    snapshot["username"] = identity.username
    snapshot["enabled"] = bool(user.get("Enabled", True))
    snapshot["linked"] = linked
    snapshot["email"] = attributes.get("email") or snapshot.get("email") or identity.email
    return snapshot


def link_provider(identity: Identity, id_token: str, settings: Settings) -> str:
    incoming = verify_id_token(id_token, settings)
    if incoming.sub == identity.sub:
        return "That login is already this account."
    provider, user_id = _provider_of(incoming)
    if not provider or not user_id:
        raise TokenError("the new sign-in did not name a Google or Meta account")
    dest_provider, dest_id = _provider_of(identity)
    if dest_provider and dest_id:
        destination = {
            "ProviderName": dest_provider,
            "ProviderAttributeName": "Cognito_Subject",
            "ProviderAttributeValue": dest_id,
        }
    else:
        destination = {
            "ProviderName": "Cognito",
            "ProviderAttributeValue": identity.username or identity.sub,
        }
    client = _client(settings)
    client.admin_link_provider_for_user(
        UserPoolId=settings.cognito_user_pool_id,
        DestinationUser=destination,
        SourceUser={
            "ProviderName": provider,
            "ProviderAttributeName": "Cognito_Subject",
            "ProviderAttributeValue": user_id,
        },
    )
    if incoming.username and incoming.username != identity.username:
        client.admin_delete_user(
            UserPoolId=settings.cognito_user_pool_id,
            Username=incoming.username,
        )
    return f"Linked {provider}."


def unlink_provider(identity: Identity, provider: str, settings: Settings) -> str:
    user = _client(settings).admin_get_user(
        UserPoolId=settings.cognito_user_pool_id,
        Username=identity.username or identity.sub,
    )
    linked = _identities(_attributes(user))
    if len(linked) < 2:
        raise TokenError("the last login cannot be removed; delete the account instead")
    match = next((item for item in linked if item.get("providerName") == provider), None)
    if match is None:
        raise TokenError("that login is not linked to this account")
    _client(settings).admin_disable_provider_for_user(
        UserPoolId=settings.cognito_user_pool_id,
        User={
            "ProviderName": provider,
            "ProviderAttributeName": "Cognito_Subject",
            "ProviderAttributeValue": match.get("userId", ""),
        },
    )
    return f"Removed {provider}."


def sign_out_everywhere(identity: Identity, settings: Settings) -> str:
    _client(settings).admin_user_global_sign_out(
        UserPoolId=settings.cognito_user_pool_id,
        Username=identity.username or identity.sub,
    )
    return "Signed out everywhere. The chat app must sign in again after its token expires."


def delete_account(identity: Identity, settings: Settings, store: UsageStore) -> str:
    delete_user_files(identity.sub, settings)
    store.delete_user(identity.sub)
    _client(settings).admin_delete_user(
        UserPoolId=settings.cognito_user_pool_id,
        Username=identity.username or identity.sub,
    )
    return "Account deleted."


def _provider_of(identity: Identity) -> tuple[str, str]:
    if identity.username and "_" in identity.username:
        provider, _, user_id = identity.username.partition("_")
        if provider in {"Google", "Facebook"} and user_id:
            return provider, user_id
    return "", ""
