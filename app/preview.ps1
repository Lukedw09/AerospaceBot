# Serve the account site locally. Does not deploy.
param(
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "web")

Write-Host "Preview http://127.0.0.1:$Port/  (Ctrl+C to stop)"
Write-Host "Sign-in and /account* stay on https://astraeus.de-wet.com/; this server only shows the static pages and the looping demo."
python -m http.server $Port
