"""Store plot and viewer files. Local paths stay local; Lambda uploads them."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings


def publish(files: list[Path], sub: str, settings: Settings) -> dict[Path, str]:
    if not files:
        return {}
    if not settings.picture_bucket:
        return {path: str(path) for path in files}
    import boto3

    client = boto3.client("s3")
    expires = max(60, settings.result_link_hours * 3600)
    links: dict[Path, str] = {}
    for path in files:
        key = f"users/{sub}/{path.parent.name}/{path.name}"
        client.upload_file(
            str(path),
            settings.picture_bucket,
            key,
            ExtraArgs={"ContentType": _content_type(path)},
        )
        links[path] = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.picture_bucket, "Key": key},
            ExpiresIn=expires,
        )
    return links


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
    return "application/octet-stream"
