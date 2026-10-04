"""Deploy the aerospace stack from GitHub Actions. Secrets come from the environment."""

from __future__ import annotations

import json
import os
import subprocess
import sys


def run(argv: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(argv, text=True, capture_output=capture)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout if capture else ""


def hosted_zone_id(site_domain: str) -> str:
    payload = json.loads(run(["aws", "route53", "list-hosted-zones", "--output", "json"], capture=True))
    labels = site_domain.strip().strip(".").lower().split(".")
    zones = payload.get("HostedZones", [])
    for take in range(len(labels), 1, -1):
        wanted = ".".join(labels[-take:]) + "."
        for zone in zones:
            if zone.get("Config", {}).get("PrivateZone"):
                continue
            if str(zone.get("Name", "")).lower() == wanted:
                return str(zone["Id"]).rsplit("/", 1)[-1]
    raise SystemExit(f"No public Route 53 zone contains {site_domain}")


def stack_status(stack_name: str) -> str:
    result = subprocess.run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            stack_name,
            "--query",
            "Stacks[0].StackStatus",
            "--output",
            "text",
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def prepare_stack(stack_name: str) -> None:
    status = stack_status(stack_name)
    if not status:
        return
    if status.endswith("_IN_PROGRESS"):
        print(f"Waiting for stack {stack_name} ({status})")
        if status.startswith("DELETE"):
            waiter = "stack-delete-complete"
        elif "ROLLBACK" in status:
            waiter = "stack-rollback-complete"
        elif status.startswith("UPDATE"):
            waiter = "stack-update-complete"
        else:
            waiter = "stack-create-complete"
        run(["aws", "cloudformation", "wait", waiter, "--stack-name", stack_name])
        status = stack_status(stack_name)
    if status in {"ROLLBACK_COMPLETE", "ROLLBACK_FAILED"}:
        print(f"Deleting failed stack {stack_name} ({status})")
        run(["aws", "cloudformation", "delete-stack", "--stack-name", stack_name])
        run(["aws", "cloudformation", "wait", "stack-delete-complete", "--stack-name", stack_name])


def stack_output(stack_name: str, key: str) -> str:
    query = f"Stacks[0].Outputs[?OutputKey=='{key}'].OutputValue"
    value = run(
        [
            "aws",
            "cloudformation",
            "describe-stacks",
            "--stack-name",
            stack_name,
            "--query",
            query,
            "--output",
            "text",
        ],
        capture=True,
    ).strip()
    if not value or value == "None":
        raise SystemExit(f"stack {stack_name} has no output {key}")
    return value


def main() -> None:
    required = [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "META_APP_ID",
        "META_APP_SECRET",
    ]
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise SystemExit("Missing GitHub secrets: " + ", ".join(missing))

    site_domain = os.environ.get("SITE_DOMAIN", "astraeus.de-wet.com").strip()
    stack_name = os.environ.get("STACK_NAME", "aerospace").strip()
    region = os.environ.get("AWS_REGION", "us-east-1").strip()
    zone_id = hosted_zone_id(site_domain)
    overrides = " ".join(
        [
            f"GoogleClientId={os.environ['GOOGLE_CLIENT_ID']}",
            f"GoogleClientSecret={os.environ['GOOGLE_CLIENT_SECRET']}",
            f"MetaAppId={os.environ['META_APP_ID']}",
            f"MetaAppSecret={os.environ['META_APP_SECRET']}",
            f"SiteDomain={site_domain}",
            f"HostedZoneId={zone_id}",
        ]
    )
    prepare_stack(stack_name)
    run(["sam", "build", "--template-file", "app/template.yaml"])
    run(
        [
            "sam",
            "deploy",
            "--template-file",
            ".aws-sam/build/template.yaml",
            "--stack-name",
            stack_name,
            "--region",
            region,
            "--capabilities",
            "CAPABILITY_IAM",
            "--resolve-s3",
            "--resolve-image-repos",
            "--no-confirm-changeset",
            "--no-fail-on-empty-changeset",
            "--parameter-overrides",
            overrides,
        ]
    )
    bucket = stack_output(stack_name, "SiteBucketName")
    distribution = stack_output(stack_name, "AccountDistributionId")
    run(["aws", "s3", "sync", "app/web", f"s3://{bucket}", "--delete"])
    run(
        [
            "aws",
            "cloudfront",
            "create-invalidation",
            "--distribution-id",
            distribution,
            "--paths",
            "/*",
        ]
    )
    print(stack_output(stack_name, "AccountSite"))
    print(stack_output(stack_name, "McpUrl"))
    print("Cognito client id: " + stack_output(stack_name, "CognitoClientId"))


if __name__ == "__main__":
    main()
