.PHONY: sync lint format typecheck test check

sync:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

test:
	uv run pytest --cov --cov-report html

check: lint typecheck test
