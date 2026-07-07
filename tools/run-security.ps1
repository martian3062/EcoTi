$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = "E:\ecoti-venv\Scripts\python.exe"

Set-Location $Root
& $Python -m bandit -q -r api -x "api/core/migrations"
& $Python -m pip_audit -r api/requirements.txt
