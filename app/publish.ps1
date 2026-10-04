# Deploy the function and copy the account pages into the site bucket.
# Requires an AWS login, the SAM CLI, Docker, a Google OAuth client, and a Meta Facebook Login app.
param(
    [Parameter(Mandatory = $true)][string]$GoogleClientId,
    [Parameter(Mandatory = $true)][string]$GoogleClientSecret,
    [Parameter(Mandatory = $true)][string]$MetaAppId,
    [Parameter(Mandatory = $true)][string]$MetaAppSecret,
    [string]$SiteDomain = "astraeus.de-wet.com",
    [string]$StackName = "aerospace",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))

function Get-HostedZoneId([string]$Name) {
    $zones = aws route53 list-hosted-zones --output json | ConvertFrom-Json
    $labels = $Name.Trim().TrimEnd(".").ToLower().Split(".")
    for ($take = $labels.Length; $take -ge 2; $take--) {
        $wanted = (($labels[($labels.Length - $take)..($labels.Length - 1)] -join ".") + ".")
        $match = @($zones.HostedZones) | Where-Object {
            -not $_.Config.PrivateZone -and $_.Name.ToLower() -eq $wanted
        } | Select-Object -First 1
        if ($match) {
            return ($match.Id -replace "^/hostedzone/", "")
        }
    }
    throw "No public Route 53 zone contains $Name"
}

$zoneId = Get-HostedZoneId $SiteDomain

sam deploy --template-file app/template.yaml --stack-name $StackName --region $Region --capabilities CAPABILITY_IAM --resolve-s3 --no-confirm-changeset `
    --parameter-overrides `
    "GoogleClientId=$GoogleClientId" `
    "GoogleClientSecret=$GoogleClientSecret" `
    "MetaAppId=$MetaAppId" `
    "MetaAppSecret=$MetaAppSecret" `
    "SiteDomain=$SiteDomain" `
    "HostedZoneId=$zoneId"

$bucket = aws cloudformation describe-stacks --stack-name $StackName --query "Stacks[0].Outputs[?OutputKey=='SiteBucketName'].OutputValue" --output text
aws s3 sync app/web "s3://$bucket" --delete
