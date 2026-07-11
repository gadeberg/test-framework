.PHONY: check test lint typecheck audit release

# Vulnerability advisories reviewed and accepted (dev-only transitive deps, not
# shipped to consumers, fix released after our cool-down cutoff) - see pyproject.toml.
IGNORED_VULNS = --ignore-vuln GHSA-6v7p-g79w-8964 --ignore-vuln PYSEC-2026-249 --ignore-vuln PYSEC-2026-248

check: lint typecheck test audit

lint:
	uv run ruff format --check .
	uv run ruff check .

typecheck:
	uv run pyright

test:
	uv run pytest

audit:
	uv run pip-audit $(IGNORED_VULNS)

release:
	uv run scripts/release.py $(VERSION)
