run:
	uv run python app.py

format:
	uv run ruff format

test:
	uv run pytest 

docker/build:
	docker build -t p1-reader .

docker/run:
	docker compose up -d
