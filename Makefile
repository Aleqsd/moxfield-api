.PHONY: install run test openapi mongo-up mongo-down mongo-logs

install:
	python3 -m venv .venv
	./.venv/bin/pip install --upgrade pip
	./.venv/bin/pip install -r requirements.txt

run:
	./.venv/bin/uvicorn app.main:app --reload

test:
	./.venv/bin/pytest

openapi:
	./.venv/bin/python scripts/generate_openapi.py

mongo-up:
	docker compose up -d mongodb

mongo-down:
	docker compose down

mongo-logs:
	docker compose logs -f mongodb
