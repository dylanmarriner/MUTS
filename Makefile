.PHONY: setup run test lint format type check

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pre-commit install

run:
	python -m muts

test:
	pytest -q

lint:
	ruff check src

format:
	black src tests

type:
	mypy src

check: lint type test
