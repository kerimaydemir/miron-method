.PHONY: init bootstrap build up down format lint typecheck test test-api test-web verify-docker quality

init:
	docker compose --env-file .env.example run --rm init-env

bootstrap: build up

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

format:
	docker compose --profile tools run --rm toolbox format

lint:
	docker compose --profile tools run --rm toolbox lint

typecheck:
	docker compose --profile tools run --rm toolbox typecheck

test: test-api test-web

test-api:
	docker compose --profile test run --rm test-api

test-web:
	docker compose --profile test run --rm test-web

verify-docker:
	docker compose --profile tools run --rm toolbox verify-docker

quality: format lint typecheck test verify-docker
