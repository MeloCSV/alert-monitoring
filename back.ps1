Set-Location "$PSScriptRoot\alert-monitoring-back-web-api"
poetry run uvicorn alert_monitoring.api.boot.main:app --host 127.0.0.1 --port 8080 --reload --env-file .env
