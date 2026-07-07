$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = "E:\ecoti-venv\Scripts\python.exe"

Set-Location $Root
& $Python -m ruff check api
& $Python -m pytest
