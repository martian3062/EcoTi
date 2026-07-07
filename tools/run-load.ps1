$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = "E:\ecoti-venv\Scripts\python.exe"
$HostUrl = if ($env:ECOTI_BASE_URL) { $env:ECOTI_BASE_URL } else { "http://localhost:8001" }

Set-Location $Root
& $Python -m locust -f locustfile.py --host $HostUrl --headless -u 10 -r 2 -t 30s
