.PHONY: lint format typecheck test build all clean

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck:
	mypy src/deja_claude/

test:
	pytest -v --cov=deja_claude --cov-report=term-missing

build:
	python -m build

all: lint typecheck test

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info .mypy_cache .pytest_cache .ruff_cache .coverage coverage.xml
