$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Otel = "E:\ecoti-venv\Scripts\opentelemetry-instrument.exe"
$Port = if ($env:ECOTI_PORT) { $env:ECOTI_PORT } else { "8001" }

Set-Location "$Root\api"
$env:OTEL_SERVICE_NAME = "ecoti-api"
$env:OTEL_TRACES_EXPORTER = "console"
$env:OTEL_METRICS_EXPORTER = "none"
$env:OTEL_LOGS_EXPORTER = "none"
& $Otel python manage.py runserver "127.0.0.1:$Port"
