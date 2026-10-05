"""Deploy the aerospace stack from GitHub Actions. Secrets come from the environment."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)


def run(argv: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(argv, text=True, capture_output=capture)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return result.stdout if capture else ""


def dns_answers(name: str, record_type: str) -> list[str]:
    query = urllib.parse.urlencode({"name": name.rstrip("."), "type": record_type})
    with urllib.request.urlopen(f"https://dns.google/resolve?{query}", timeout=20) as response:
        payload = json.load(response)
    type_code = {"A": 1, "NS": 2, "CNAME": 5}[record_type]
    found = []
    for answer in payload.get("Answer", []):
        if answer.get("type") == type_code:
            found.append(str(answer.get("data", "")).strip().rstrip(".").lower())
    return found


def list_hosted_zones() -> list[dict]:
    zones: list[dict] = []
    marker = None
    while True:
        command = ["aws", "route53", "list-hosted-zones", "--output", "json"]
        if marker:
            command.extend(["--marker", marker])
        payload = json.loads(run(command, capture=True))
        zones.extend(payload.get("HostedZones", []))
        if not payload.get("IsTruncated"):
            return zones
        marker = payload.get("NextMarker")


def zone_nameservers(zone_id: str) -> set[str]:
    payload = json.loads(
        run(
            ["aws", "route53", "get-hosted-zone", "--id", zone_id, "--output", "json"],
            capture=True,
        )
    )
    servers = payload.get("DelegationSet", {}).get("NameServers", [])
    return {str(server).rstrip(".").lower() for server in servers}


def hosted_zone_id(site_domain: str) -> str:
    labels = site_domain.strip().strip(".").lower().split(".")
    zones = list_hosted_zones()
    checked: list[str] = []
    for take in range(len(labels), 1, -1):
        apex = ".".join(labels[-take:])
        wanted = apex + "."
        public = set(dns_answers(apex, "NS"))
        for zone in zones:
            if zone.get("Config", {}).get("PrivateZone"):
                continue
            if str(zone.get("Name", "")).lower() != wanted:
                continue
            zone_id = str(zone["Id"]).rsplit("/", 1)[-1]
            nameservers = zone_nameservers(zone_id)
            checked.append(
                f"{apex} {zone_id} route53={sorted(nameservers)} public={sorted(public)}"
            )
            print(checked[-1])
            if public and nameservers == public:
                return zone_id
    raise SystemExit(
        f"No delegated public Route 53 zone contains {site_domain}. "
        f"Candidates: {'; '.join(checked) or 'none'}"
    )


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


def stack_parameter(stack_name: str, key: str) -> str:
    query = f"Stacks[0].Parameters[?ParameterKey=='{key}'].ParameterValue | [0]"
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
        return ""
    return value


def pending_rows(stack_name: str) -> list[list[str]]:
    text = run(
        [
            "aws",
            "cloudformation",
            "describe-stack-resources",
            "--stack-name",
            stack_name,
            "--query",
            "StackResources[?ResourceStatus!='CREATE_COMPLETE' && ResourceStatus!='UPDATE_COMPLETE'].[LogicalResourceId,ResourceStatus,ResourceStatusReason]",
            "--output",
            "json",
        ],
        capture=True,
    )
    return [[str(cell or "") for cell in row] for row in json.loads(text or "[]")]


def format_pending(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(row) for row in rows)


def certificate_arn(stack_name: str) -> str:
    value = run(
        [
            "aws",
            "cloudformation",
            "describe-stack-resource",
            "--stack-name",
            stack_name,
            "--logical-resource-id",
            "Certificate",
            "--query",
            "StackResourceDetail.PhysicalResourceId",
            "--output",
            "text",
        ],
        capture=True,
    ).strip()
    if not value or value == "None":
        return ""
    return value


def validation_records(arn: str) -> list[tuple[str, str, str, str]]:
    payload = json.loads(
        run(
            ["aws", "acm", "describe-certificate", "--certificate-arn", arn, "--output", "json"],
            capture=True,
        )
    )
    rows = []
    for option in payload.get("Certificate", {}).get("DomainValidationOptions", []):
        record = option.get("ResourceRecord") or {}
        rows.append(
            (
                str(option.get("DomainName", "")),
                str(option.get("ValidationStatus", "")),
                str(record.get("Name", "")),
                str(record.get("Value", "")),
            )
        )
    return rows


def upsert_cname(zone_id: str, name: str, value: str) -> None:
    target = value if value.endswith(".") else value + "."
    change = {
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": name,
                    "Type": "CNAME",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": target}],
                },
            }
        ]
    }
    run(
        [
            "aws",
            "route53",
            "change-resource-record-sets",
            "--hosted-zone-id",
            zone_id,
            "--change-batch",
            json.dumps(change),
        ]
    )


def repair_certificate(stack_name: str, zone_id: str) -> None:
    arn = certificate_arn(stack_name)
    if not arn:
        print("Certificate has no ARN yet")
        return
    print(f"certificate {arn}")
    for domain, validation, name, value in validation_records(arn):
        public = dns_answers(name, "CNAME") if name else []
        print(
            f"validation {domain} {validation} {name} -> {value} "
            f"public={public or '(none)'}"
        )
        expected = value.rstrip(".").lower()
        if name and value and expected not in public:
            print(f"Publishing validation CNAME {name} in zone {zone_id}")
            upsert_cname(zone_id, name, value)


def delete_stack(stack_name: str) -> None:
    run(["aws", "cloudformation", "delete-stack", "--stack-name", stack_name])
    run(["aws", "cloudformation", "wait", "stack-delete-complete", "--stack-name", stack_name])


def wait_for_stack(stack_name: str, minutes: int) -> None:
    deadline = time.time() + minutes * 60
    while time.time() < deadline:
        status = stack_status(stack_name)
        rows = pending_rows(stack_name) if status else []
        print(f"stack status: {status or '(gone)'}")
        print(format_pending(rows) or "(no pending resources)")
        if not status.endswith("_IN_PROGRESS"):
            return
        time.sleep(60)


def prepare_stack(stack_name: str, zone_id: str) -> None:
    status = stack_status(stack_name)
    if not status:
        return
    if status == "CREATE_IN_PROGRESS":
        rows = pending_rows(stack_name)
        print(format_pending(rows) or "(no pending resources)")
        pending_ids = [row[0] for row in rows]
        if pending_ids == ["Certificate"]:
            used = stack_parameter(stack_name, "HostedZoneId")
            print(f"stack HostedZoneId={used} delegated HostedZoneId={zone_id}")
            if used != zone_id:
                print(
                    f"Deleting stack {stack_name}: hosted zone {used} "
                    f"is not the delegated zone {zone_id}"
                )
                delete_stack(stack_name)
                return
            repair_certificate(stack_name, zone_id)
        print(f"Waiting for stack {stack_name} ({status})")
        wait_for_stack(stack_name, minutes=60)
        status = stack_status(stack_name)
    elif status.endswith("_IN_PROGRESS"):
        print(f"Waiting for stack {stack_name} ({status})")
        wait_for_stack(stack_name, minutes=40)
        status = stack_status(stack_name)
    if status in {"ROLLBACK_COMPLETE", "ROLLBACK_FAILED", "CREATE_FAILED"}:
        print(f"Deleting failed stack {stack_name} ({status})")
        delete_stack(stack_name)
        return
    if status.endswith("_IN_PROGRESS") or status.endswith("_FAILED"):
        raise SystemExit(f"stack {stack_name} is still {status}")


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
    prepare_stack(stack_name, zone_id)
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
