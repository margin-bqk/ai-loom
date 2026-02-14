.PHONY: ci-local format lint type-check test security fix multiversion-test help

ci-local: format lint type-check test security
	@echo "All CI checks passed!"
	@echo ""
	@echo "Note: Local tests run on current Python version only."
	@echo "For multi-version testing (3.10, 3.11, 3.12), run:"
	@echo "  make multiversion-test"
	@echo "or use: tox"

format:
	@echo "1. Formatting check..."
	black --check src/ tests/

lint:
	@echo "2. Code style check..."
	flake8 src/ tests/
	@echo "3. Import sorting check..."
	isort --check-only --diff src/ tests/

type-check:
	@echo "4. Type checking..."
	mypy src/loom --ignore-missing-imports

test:
	@echo "5. Running tests (current Python version)..."
	pytest tests/ -v

multiversion-test:
	@echo "Running multi-version tests with tox (3.10, 3.11, 3.12)..."
	@echo "Note: This requires multiple Python versions installed"
	tox

security:
	@echo "6. Security scan..."
	bandit -r src/ -c pyproject.toml

fix:
	@echo "Fixing formatting and imports..."
	black src/ tests/
	isort src/ tests/

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install

pre-commit-run:
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

ci-full: ci-local multiversion-test
	@echo "Full CI with multi-version testing completed!"

help:
	@echo "Available targets:"
	@echo "  ci-local         - Run all CI checks locally (current Python version)"
	@echo "  ci-full          - Run full CI with multi-version testing"
	@echo "  format           - Check code formatting"
	@echo "  lint             - Check code style and imports"
	@echo "  type-check       - Run type checking"
	@echo "  test             - Run tests (current Python version)"
	@echo "  multiversion-test - Run tests on multiple Python versions (3.10, 3.11, 3.12)"
	@echo "  security         - Run security scan"
	@echo "  fix              - Fix formatting and imports"
	@echo "  pre-commit-install - Install pre-commit hooks"
	@echo "  pre-commit-run   - Run pre-commit on all files"
