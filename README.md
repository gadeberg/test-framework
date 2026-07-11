# test-framework

A thin, spec-traceable test automation framework on top of proven libraries:
**pytest** as the runner, **pytest-bdd** for Gherkin, **pytest-playwright**
for the web, **httpx** for the API. It wraps only the *domain* (API client,
page objects, step vocabulary, reporting) — pytest's own mechanics (fixtures,
assertions, discovery, parametrize, `-n auto`) stay visible and unwrapped.

Tests are written in plain Python (pytest) or Gherkin, both first-class,
sharing one fixture/step library, tagged to requirements (`@REQ-1234`) for
audit traceability.

This is **Repo 1** of a two-repo setup: this package is versioned and tagged
here; test projects live in their own repos and consume it by GitHub tag —
see "Install (as a consumer)" below. The example consumer is
[`test-framework-project`](https://github.com/gadeberg/test-framework-project).

## Install (as a consumer)

No package registry — install straight from GitHub by tag with `uv`:

```toml
# your test project's pyproject.toml
[project]
dependencies = ["test-framework"]

[tool.uv.sources]
test-framework = { git = "https://github.com/gadeberg/test-framework", tag = "v0.1.0" }
```

`uv.lock` pins the exact commit, so a teammate or CI gets byte-identical
sources. Bumping to a new framework version = change the tag, `uv lock`,
commit — never implicit.

## What's in the box

- `api/client.py` — thin httpx wrapper (base URL, auth header, last-response tracking). The one API path; steps/tests never touch raw httpx.
- `ui/pages/base.py` — page-object base. Subclasses declare a `path` and a `locators` map (field name -> CSS selector); the shared web steps and your own tests drive pages by field name only, so selectors never leak into a `.feature` file or a test body.
- `steplog.py` (`step(...)`) + `verify.py` (`verify.*`) — the authoring ergonomics. `with step("..."):` logs to console and to the report; `verify.status(resp, 401)`, `verify.equals(...)`, `verify.contains(...)`, `verify.between(...)`, `verify.is_true(...)` produce a clear message and report evidence on both pass and fail, and never hide pytest's own `AssertionError`. (The module is named `steplog`, not `logging`, to avoid shadowing the stdlib.)
- `report.py` + `reporting/` — the reporting seam (see below). `report.requirement("REQ-1234")` is the Python-side traceability decorator.
- `fixtures.py` — the pytest plugin: `api_client`, `scenario_context` (per-scenario/test scratch space — named to avoid colliding with pytest-playwright's own `context` fixture), `page_registry` (name -> page-object class map a consumer overrides), and the `@REQ-*` <-> `@requirement(...)` tag bridge. It also wires `base_url`: pytest-base-url's fixture is the single definition (the framework deliberately doesn't define a competing one), fed from `--base-url` > the `base_url` ini setting > the `BASE_URL` env var > `http://localhost:8000`.
- UI-failure evidence is pytest-playwright's own capture — put `--screenshot=only-on-failure --tracing=retain-on-failure` in your `addopts` (both repos here do) and every failing UI test *or Gherkin scenario* drops a screenshot + trace under `test-results/`.
- `steps/api.py`, `steps/web.py` — the shared, controlled-vocabulary step library (a few dozen generic, parametrized steps, not one step per value).
- All of the above register as `pytest11` entry points, so a consumer gets fixtures *and* the step library just by installing the package — no `pytest_plugins` wiring needed.

## Reporting is wrapped (pure-Python by default, Allure optional)

Tests never call a reporting library directly — they call `step(...)`,
`verify.*`, and `@requirement(...)`, which all go through `report.py`, the
**only** module that touches a concrete backend.

- **Phase-1 default**: `reporting/pyhtml.py` — human-readable via
  **pytest-html**, machine-readable via **JUnit XML** (`--junitxml`). No JVM.
  pytest-html has no nested-step concept, so steps/checks render as
  formatted log sections + an HTML block in the test row, not a step tree —
  sufficient for audit evidence (what was done, what was checked, pass/fail).
  The requirement label is written into the JUnit XML as a per-test
  `<property name="requirement" .../>`; add `junit_logging = "log"` and
  `log_level = "INFO"` to `[tool.pytest.ini_options]` (as this repo and the
  example consumer do) to copy the step/check evidence lines into the XML too.
- **Optional**: `reporting/allure.py` — behind the `[project.optional-dependencies].allure` extra. Allure's report generator is a **Java CLI**; enabling it adds a JVM to your toolchain, a real qualification/air-gap consideration. Select it via `TEST_FRAMEWORK_REPORT_BACKEND=allure`.
- **Self-tests** run against `reporting/spy.py`, a fake backend, so they need neither pytest-html nor Allure installed to verify behaviour — proof the seam is real.
- The `@REQ-*` Gherkin tag and the Python `@requirement("REQ-...")` decorator both resolve to the same `report.set_requirement(...)` call (via a `pytest_bdd_apply_tag` hook, prioritized with `tryfirst=True` — pytest-bdd's own built-in hook implementation would otherwise win and silently skip the bridge).

Switch backends with the `TEST_FRAMEWORK_REPORT_BACKEND` env var (`pyhtml` default, or `allure`). Swapping changes only `reporting/`, never a test.

## Dependency policy: cool-down + audit

Security and supply-chain trust over latest features:

- **Cool-down**: `[tool.uv] exclude-newer` in `pyproject.toml` holds dependency resolution to versions published before a chosen date (currently `2026-06-06`), giving the community time to surface vulnerabilities before we adopt a release.
- **Audit gate**: `make check` runs `pip-audit` against the lockfile; a known-vuln advisory fails the build unless explicitly reviewed and ignored (see the `IGNORED_VULNS` list in the `Makefile`, and the comment above `exclude-newer` in `pyproject.toml` for the current, dated, reviewed exceptions).
- **Override rule**: a vulnerability fix can be adopted *before* its cool-down window closes — deliberately, reviewed, one dependency at a time (e.g. `pytest` was bumped to `>=9.0.3` here specifically to pull in a security fix).
- Permissive licenses only for dependencies (MIT/Apache-2.0/BSD). `uv.lock` is committed and is law — version bumps are explicit, reviewed diffs.
- This package itself is licensed **Apache-2.0** (see `LICENSE`) — same permissiveness as MIT, plus an explicit patent grant, which some adopting organizations require before approving a dependency.

## Type checking

Strict Pyright on the framework package (`src/`) and its own tests
(`tests/`): full annotations, no implicit `Any`, zero errors. Consumer test
projects use a separate, relaxed profile (see
[`test-framework-project`](https://github.com/gadeberg/test-framework-project)'s
README) — test authors shouldn't fight the type checker over pytest's
loosely-typed fixtures and decorators.

## The step catalog

**API** (`steps/api.py`): `the API is available`; `I GET "{path}"`; `I POST credentials "{email}" / "{password}"`; `the response status is {status:d}`; `the json field "{field}" equals "{value}"`.

**Web** (`steps/web.py`), driven by page-object field name, never a selector: `I am on the "{page_name}" page`; `I fill in "{field}" with "{value}"`; `I click "{field}"`; `the "{field}" is visible`; `the "{field}" has text "{text}"` (both wait via Playwright's own auto-waiting before asserting, so async UI updates aren't a race).

Adding a new scenario is new `.feature` lines or a copied Python test template — not new step code, as long as the action fits the existing vocabulary.

## Self-tests

`tests/unit/` (verify/logging/client/tag-bridge in isolation, against the
`spy` backend) and `tests/contract/` (the shared step library actually
driving `tests/support/mockapp/`, a bundled FastAPI app serving both the
`/login` JSON API and a rendered HTML login page — offline, deterministic).

```bash
uv sync
uv run playwright install chromium
make check   # ruff format --check + ruff check + pyright + pytest + pip-audit
```

## Releasing

```bash
uv run scripts/release.py X.Y.Z
```

Gates on `make check`, bumps the version (`pyproject.toml` + `__init__.py`),
commits, tags `vX.Y.Z`, pushes tag + commit, and prints the tag snippet to
paste into a consumer. Semver: a breaking step phrasing or helper signature
is **major**; new steps/helpers are **minor**; fixes are **patch**. See
`CHANGELOG.md` for what each release actually changed — the framework's
contract self-tests are what tell you whether a change is breaking.

## Co-development with a consumer project

See [`test-framework-project`](https://github.com/gadeberg/test-framework-project)'s
README for the full workflow (side-by-side checkout, `make dev` /
`make test` / `make release-mode`). The short version: the *committed*
`pyproject.toml` in a consumer always pins this repo's
GitHub tag; a local, uncommitted `uv pip install -e ../test-framework` layers
a live edit on top for one working session.
