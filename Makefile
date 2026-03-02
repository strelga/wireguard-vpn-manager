.PHONY: lint lint-fix format typecheck test test-cov check-all fix-all help install install-dev

# Path to pipx venv
VENV_BIN = $(HOME)/.local/pipx/venvs/wireguard-vpn-manager/bin

help:
	@echo "Available targets:"
	@echo "  install    	- Install WireGuard VPN Manager (production mode)"
	@echo "  install-dev	- Install WireGuard VPN Manager with dev dependencies"
	@echo "  lint       	- Run ruff linter"
	@echo "  lint-fix   	- Run ruff linter with auto-fix"
	@echo "  format     	- Run ruff formatter"
	@echo "  typecheck  	- Run mypy type checker"
	@echo "  test       	- Run pytest"
	@echo "  test-cov   	- Run pytest with coverage"
	@echo "  check-all  	- Run lint and typecheck"
	@echo "  fix-all    	- Run lint-fix and format"

install:
	@./setup.sh --no-dev

install-dev:
	@./setup.sh --dev

lint:
	$(VENV_BIN)/ruff check .

lint-fix:
	$(VENV_BIN)/ruff check . --fix

format:
	$(VENV_BIN)/ruff format .

typecheck:
	$(VENV_BIN)/mypy . --exclude build

test:
	$(VENV_BIN)/pytest tests/

test-cov:
	$(VENV_BIN)/pytest tests/ --cov=. --cov-report=html --cov-report=term

check-all: lint typecheck

fix-all: lint-fix format