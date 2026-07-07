$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Schemathesis = "E:\ecoti-venv\Scripts\schemathesis.exe"
$BaseUrl = if ($env:ECOTI_BASE_URL) { $env:ECOTI_BASE_URL } else { "http://localhost:8001" }

Set-Location $Root
$env:PYTHONIOENCODING = "utf-8"
& $Schemathesis run "$BaseUrl/api/schema?format=json" --url $BaseUrl --checks all --max-examples 20
