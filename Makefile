dev:
	uv run uvicorn main:app --reload

run:
	uv run uvicorn main:app

format:
	uv run ruff format .

lint:
	uv run ruff check .