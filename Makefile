.PHONY: deploy stop logs ps build

build:
	docker build -t ghcr.io/byronmoreno/productividad:latest .

deploy:
	set -a && . ./.env && set +a && docker stack deploy -c stack.yml productividad

stop:
	docker stack rm productividad

logs:
	docker service logs -f productividad_web

logs-celery:
	docker service logs -f productividad_celery_worker

ps:
	docker stack services productividad

