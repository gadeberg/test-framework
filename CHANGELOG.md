# Changelog

All notable changes to `test-framework` are documented here. Versions follow
semver: a breaking step phrasing or helper signature is a **major** bump, new
steps/helpers are **minor**, fixes are **patch**.

## v0.1.0

Initial release.

- `api/client.py`: thin httpx wrapper (base URL, auth header, last-response tracking) — the
  one API path; steps and tests never touch raw httpx.
- `ui/pages/base.py`: page-object base with field-name-based `locators` (never raw selectors
  in tests); `locators` is copied per instance, and unknown page names / locator fields raise
  a `LookupError` listing what *is* registered.
- Reporting seam: `report.py` (the only module that touches a concrete backend) + `reporting/`
  backends — `pyhtml` (default, no JVM), `allure` (optional extra; its report generator needs
  a Java CLI), and `spy` (used by the self-tests, proving the seam is real). The
  `ReportingBackend` protocol covers `start_step`/`end_step`/`attach`/`attach_file`/
  `set_requirement`/`record_check`. Selected via `TEST_FRAMEWORK_REPORT_BACKEND`.
- Authoring ergonomics: `steplog.py`'s `step(...)` context manager (named `steplog`, not
  `logging`, to avoid shadowing the stdlib) and `verify.py`'s `verify.*` checks. Evidence is
  recorded on pass **and** fail, and pytest's real `AssertionError` is never swallowed.
- `fixtures.py`: the pytest plugin — `api_client`, `scenario_context` (named to avoid
  pytest-playwright's `context` fixture), `page_registry`, and `base_url` wiring that seeds
  `config.option.base_url` from the `BASE_URL` env var instead of racing pytest-base-url's own
  fixture (precedence: CLI > ini > `BASE_URL` env > `http://localhost:8000`). Registers the
  `requirement` marker and writes the requirement label into JUnit XML as a per-test
  `<property name="requirement" .../>`.
- The `@REQ-*` <-> `@requirement(...)` tag bridge (`pytest_bdd_apply_tag`, `tryfirst=True` so
  pytest-bdd's own `firstresult` hookimpl doesn't win), so Gherkin scenarios and Python tests
  carry the same requirement label in the report.
- Shared step library (`steps/api.py`, `steps/web.py`) registered as separate `pytest11`
  entry points, so a consumer gets the full controlled vocabulary just by installing the
  package. Web assertion steps wait via Playwright's auto-waiting `expect(...)` before
  asserting, so async DOM updates aren't a race.
- UI-failure evidence via pytest-playwright's built-in capture
  (`--screenshot=only-on-failure --tracing=retain-on-failure` in `addopts`) — identical
  artifacts for plain-Python tests and Gherkin scenarios under `test-results/`.
- Framework self-tests: `tests/unit/` + `tests/contract/` against a bundled FastAPI mock,
  asserting against the `spy` backend (`TEST_FRAMEWORK_REPORT_BACKEND=spy` forced).
- `scripts/release.py`: gate (`make check`) -> bump version -> tag `vX.Y.Z` -> push; refuses
  to run off `main`, rejects non-`X.Y.Z` or non-increasing versions, and requires a matching
  `## vX.Y.Z` changelog entry.
- Dependency cool-down (`exclude-newer`) + `pip-audit` gate, with two reviewed, documented
  exceptions (dev-only transitive deps whose fixes post-date the cutoff — see
  `pyproject.toml`). `pytest` pinned `>=9.0.3` as a deliberate cool-down override for a CVE fix.
- Licensed Apache-2.0.
