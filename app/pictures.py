"""Store plot and viewer files. Local paths stay local; Lambda uploads them.

Published links are capability URLs on this service. They do not carry AWS
credentials. A missing signing secret falls back to a presigned GetObject URL.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from pathlib import Path

from app.config import Settings


def publish(files: list[Path], sub: str, settings: Settings) -> dict[Path, str]:
    if not files:
        return {}
    if not settings.picture_bucket:
        return {path: str(path) for path in files}
    import boto3

    client = boto3.client("s3")
    links: dict[Path, str] = {}
    for path in files:
        key = f"users/{sub}/{path.parent.name}/{path.name}"
        client.upload_file(
            str(path),
            settings.picture_bucket,
            key,
            ExtraArgs={"ContentType": _content_type(path)},
        )
        links[path] = _link_for(key, settings, client)
    return links


def result_token(key: str, settings: Settings, now: float | None = None) -> str:
    if not settings.result_link_secret:
        raise ValueError("result links are not configured")
    expires = int((now if now is not None else time.time()) + _ttl_seconds(settings))
    payload = json.dumps({"k": key, "e": expires}, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(settings.result_link_secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _b64(payload) + "." + _b64(signature)


def verify_result_token(token: str, settings: Settings, now: float | None = None) -> str:
    if not settings.result_link_secret:
        raise ValueError("result links are not configured")
    payload_text, dot, signature_text = token.partition(".")
    if not dot or not payload_text or not signature_text:
        raise ValueError("bad link")
    try:
        payload = _b64decode(payload_text)
        signature = _b64decode(signature_text)
    except ValueError as exc:
        raise ValueError("bad link") from exc
    expected = hmac.new(settings.result_link_secret.encode("utf-8"), payload, hashlib.sha256).digest()
    if len(signature) != len(expected) or not hmac.compare_digest(signature, expected):
        raise ValueError("bad link")
    try:
        decoded = json.loads(payload.decode("utf-8"))
        key = str(decoded["k"])
        expires = int(decoded["e"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("bad link") from exc
    if not key.startswith("users/") or ".." in key:
        raise ValueError("bad link")
    if (now if now is not None else time.time()) >= expires:
        raise ValueError("link expired")
    return key


def read_result(key: str, settings: Settings) -> tuple[bytes, str]:
    if not settings.picture_bucket:
        raise ValueError("not found")
    import boto3

    obj = boto3.client("s3").get_object(Bucket=settings.picture_bucket, Key=key)
    body = obj["Body"].read()
    media = str(obj.get("ContentType") or "application/octet-stream")
    return body, media


def _link_for(key: str, settings: Settings, client: object) -> str:
    if settings.public_base_url and settings.result_link_secret:
        return f"{settings.public_base_url}/results/{result_token(key, settings)}"
    expires = _ttl_seconds(settings)
    return client.generate_presigned_url(  # type: ignore[attr-defined]
        "get_object",
        Params={"Bucket": settings.picture_bucket, "Key": key},
        ExpiresIn=expires,
    )


def _ttl_seconds(settings: Settings) -> int:
    return max(60, settings.result_link_hours * 3600)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + pad)
    except Exception as exc:
        raise ValueError("bad link") from exc


def delete_user_files(sub: str, settings: Settings) -> None:
    if not settings.picture_bucket:
        return
    import boto3

    client = boto3.client("s3")
    prefix = f"users/{sub}/"
    token = None
    while True:
        kwargs: dict[str, object] = {"Bucket": settings.picture_bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        page = client.list_objects_v2(**kwargs)
        objects = [{"Key": item["Key"]} for item in page.get("Contents", [])]
        if objects:
            client.delete_objects(Bucket=settings.picture_bucket, Delete={"Objects": objects})
        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")


def rewrite(text: str, links: dict[Path, str]) -> str:
    for path, url in links.items():
        text = text.replace(str(path), url)
    return text


def _content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix in {".html", ".htm"}:
        return "text/html"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".csv":
        return "text/csv; charset=utf-8"
    if suffix == ".txt":
        return "text/plain; charset=utf-8"
    return "application/octet-stream"
