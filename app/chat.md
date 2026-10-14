# Chat development

Local runs and the deploy secret. Visitors use the site at `/chat`.

Close anything else on port 8080, including `app/preview.ps1`. From the repository root in PowerShell:

```powershell
Remove-Item Env:USAGE_TABLE, Env:PICTURE_BUCKET, Env:GROK_API_KEY_PARAMETER -ErrorAction SilentlyContinue
$env:AEROSPACE_HTTP = "1"
$env:AUTH_DISABLED = "1"
$env:USAGE_CAP_DEV_BYPASS = "1"
$env:GROK_API_KEY = "paste-the-key-from-console.x.ai"
$env:GROK_MODEL = "grok-4.7"
python -m app.server
```

Open http://localhost:8080/chat. The page does not ask you to sign in. `USAGE_CAP_DEV_BYPASS=1` is the only way to call tools without a usage table. `AUTH_DISABLED` skips sign-in and does not skip the cap. Do not set the bypass on Lambda; the process refuses to start if that variable is set there. The counter stays at 50 because calls are not stored without a usage table. `GROK_API_KEY` must be the key from [console.x.ai](https://console.x.ai), the same value stored as the GitHub secret `XAI_APIKEY`. Press Ctrl+C to stop.

A push to `main` stores the GitHub secret `XAI_APIKEY` as the SecureString `/astraeus/grok-api-key`. The function reads that parameter. The key is not written into the stack or the site.
