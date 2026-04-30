.PHONY: back front db

back:
	cd alert-monitoring-back-web-api && poetry run uvicorn alert_monitoring.api.boot.main:app --host 127.0.0.1 --port 8080 --reload --env-file .env

front:
	cd alert-monitoring-front && ng serve

db:
	cd alert-monitoring-back-web-api/alert_monitoring/api/boot/docker && docker compose up -d