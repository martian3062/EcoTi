$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Set-Location $Root
npx promptfoo@latest eval -c redteam/promptfooconfig.yaml
