.PHONY: help install dev test format lint type-check clean run example

help: ## Show this help message
	@echo "RELAY: Universal Desktop Assistant"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Install development dependencies
	uv sync --extra dev

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=relay --cov-report=html --cov-report=term-missing

format: ## Format code with black and isort
	uv run black .
	uv run isort .

lint: ## Run linting with flake8
	uv run flake8 relay/

type-check: ## Run type checking with mypy
	uv run mypy relay/

check: format lint type-check test ## Run all checks (format, lint, type-check, test)

run: ## Run RELAY
	uv run python main.py

example: ## Run example script
	uv run python examples/basic_usage.py

clean: ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

install-script: ## Make install script executable
	chmod +x install.sh

setup: install-script install ## Setup the project (make install script executable and install deps)

all: setup dev ## Setup everything including development dependencies 