# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`test-framework` is **Repo 1** of a two-repo test-automation setup: a thin, spec-traceable
package that wraps pytest + pytest-bdd + pytest-playwright + httpx behind a domain layer (API
client, page objects, step vocabulary, reporting) — pytest's own mechanics (fixtures,
assertions, discovery, parametrize, `-n auto`) stay unwrapped. Tests are written in plain
Python or Gherkin, both first-class, tagged to requirements (`@REQ-1234`) for audit
traceability. **Repo 2** is
[`test-framework-project`](https://github.com/gadeberg/test-framework-project) (a sibling
checkout at `../test-framework-project`), which consumes this package from GitHub by tag —
never a local path dependency in its committed `pyproject.toml`.

## Priorities (in order — higher wins on conflict)

1. **Security / supply-chain trust** over latest features (cool-down, pins, audit).
2. **Simplicity and best-practice defaults** over cleverness.
3. **Traceability / audit-readiness** — every test maps to a requirement, readable in the report.
4. **Frictionless authoring** — adding a test or helper is copy-paste-and-edit.

## Commands

```bash
uv sync                        # install deps (dev group + main)
uv run playwright install chromium   # browser binary, separate from uv sync

uv run pytest                  # all self-tests (tests/unit + tests/contract)
uv run pytest tests/unit/test_verify.py::test_equals_passes_and_records_check  # single test
uv run pytest -k "tag_bridge"  # by keyword
uv run pyright                 # strict on src/ and tests/, must be 0 errors
uv run ruff format --check .   # or `uv run ruff format .` to fix
uv run ruff check .            # or `--fix`

make check                     # the full gate: ruff format --check + ruff check + pyright + pytest + pip-audit
uv run scripts/release.py X.Y.Z   # gate -> bump version -> commit -> tag vX.Y.Z -> push
```

**Update `CHANGELOG.md` as part of the same change, before running the release script** —
`release.py` bumps the version and tags but does not touch the changelog itself. Add the new
`## vX.Y.Z` entry (what changed, whether it's breaking) before you tag, not after; it's easy to
forget and end up with tagged releases the changelog doesn't account for.

`make check`'s `pip-audit` call passes `--ignore-vuln` for two dated, reviewed exceptions
(dev-only transitive deps whose fixes post-date the `exclude-newer` cool-down cutoff) — see the
`IGNORED_VULNS` var in `Makefile` and the comment above `exclude-newer` in `pyproject.toml`.
Don't add more `--ignore-vuln` entries without the same treatment: dated, reasoned, and only for
genuinely dev-only/unshipped exposure.

## Versioning (semver) and releasing

- Breaking a step phrasing or a public helper signature = **major**. New steps/helpers = **minor**. Fixes = **patch**.
- The contract self-tests (`tests/contract/`) are the arbiter of "breaking" — if they need changes, it's breaking.
- **Before tagging, verify against the consumer:** in `../test-framework-project`, run
  `make dev` (`uv sync` + `uv pip install -e ../test-framework`) then `uv run --no-sync pytest`
  (`--no-sync` is required — a plain `uv run` resyncs and drops the editable shadow). Then tag
  here, then bump the tag in the consumer.

## Architecture

**The reporting seam is the load-bearing abstraction.** No test, step, or helper ever imports a
reporting library directly. Call chain: `steplog.step(...)` / `verify.*` / `report.requirement(...)`
→ all go through `report.py` (the only module allowed to touch a concrete backend) → one of
`reporting/{pyhtml,allure,spy}.py`, selected via `TEST_FRAMEWORK_REPORT_BACKEND` env var
(default `pyhtml`). (The step-logging module is named `steplog`, not `logging` — that name
would shadow the stdlib.) `reporting/base.py` defines the `ReportingBackend` protocol
(`start_step`/`end_step`/`attach`/`attach_file`/`set_requirement`/`record_check`). Self-tests assert against
`spy` so they need neither pytest-html nor Allure installed — that's the proof the seam is real.
If you add a new reporting capability, it goes in `report.py` + a backend method, never as a
new import scattered through `steps/` or a test.

**The `pyhtml` backend stays the default.** The Allure backend is an optional extra whose report
generation requires a **Java CLI (JVM)** — a qualification/air-gap burden. Never promote it to
default or move `allure-pytest` into core deps.

**`step`/`verify` contract:** helpers never swallow pytest's assert — on failure the real
assertion error surfaces. Evidence is recorded on **pass and fail** (passing checks are audit
evidence too). Any new `verify.*` function must honor both rules.

**Everything is a `pytest11` entry point** (see `[project.entry-points.pytest11]` in
`pyproject.toml`): `fixtures.py` (the plugin: `base_url` config wiring, `api_client`,
`scenario_context`, `page_registry`, the `@REQ-*` tag bridge, the JUnit-XML requirement
property) plus `steps/api.py` and
`steps/web.py` **each as their own separate entry point**. This isn't cosmetic: pytest-bdd's
`given`/`when`/`then` decorators bind the generated step-fixture into the *defining* module's
namespace via frame inspection at import time. Merely `import`ing `steps.api` from `fixtures.py`
and re-exporting the names does **not** make pytest discover the step fixtures — each step
module must itself be registered as a plugin so pytest scans its namespace directly. If you add
a third step module, it needs its own entry point too.

**Step vocabulary is controlled, not free-form.** Steps are generic and parametrized
(`the response status is {status:d}`) — never one step per value, never two phrasings for one
action (`I log in` vs `the user signs in`: pick one canonical form). A few dozen steps should
express hundreds of scenarios; if a new scenario needs new Python, first check whether an
existing step parametrizes to cover it.

**The `@REQ-*` <-> `@requirement(...)` tag bridge** lives in `fixtures.py`'s
`pytest_bdd_apply_tag` hookimpl, decorated `@pytest.hookimpl(tryfirst=True)`. This is required,
not decorative: `pytest_bdd_apply_tag` is a `firstresult=True` hook, and pytest-bdd's own
built-in implementation unconditionally applies `pytest.mark.<tag>` and returns non-None. Without
`tryfirst`, the built-in wins and the bridge silently never runs — `tests/unit/test_tag_bridge.py`
covers this.

**Page objects are field-name-indexed, not selector-indexed, from the test's perspective.**
`ui/pages/base.py`'s `BasePage` declares a `locators: dict[str, str]` (field name -> CSS
selector); `steps/web.py`'s shared steps and any Python test call `.locator(field_name)`, never
a raw selector. This is what keeps `.feature` files and test bodies POM-compliant. Web assertions
(`the "{field}" has text "..."`, `the "{field}" is visible`) assert via Playwright's own
auto-waiting `expect(...)` — without that wait, they race async DOM updates — recording a check
through the reporting seam on pass *and* fail and re-raising `expect`'s real `AssertionError`
(never swallow-and-reprobe: that produces a raw 36s `TimeoutError` with no evidence).

**Fixture-naming collisions with pytest-playwright are a real hazard.** It ships (via
pytest-base-url) a session-scoped `base_url` fixture registered as its own `pytest11` entry
point — which is why the framework does **not** define a competing `base_url` fixture (it would
lose the registration race and silently never run).
Instead `fixtures.py`'s `pytest_configure` seeds `config.option.base_url` from `BASE_URL` when
neither `--base-url` nor the ini setting is given, and pytest-base-url's fixture is the single
definition. A consumer conftest may still override `base_url` (session-scoped — a
function-scoped override causes a `ScopeMismatch`). pytest-playwright also ships a fixture
literally named `context` (the `BrowserContext`); the framework's per-scenario/test scratch
space is named `scenario_context` specifically to avoid silently shadowing it.

**UI-failure evidence is pytest-playwright's built-in capture** (`--screenshot=only-on-failure
--tracing=retain-on-failure` in `addopts`), *not* a custom hook: a hand-rolled
`pytest_runtest_makereport` screenshot never fired for Gherkin scenarios (pytest-bdd resolves
`page` via `getfixturevalue`, so it isn't in `item.fixturenames` at report time).
The built-ins hook the `page`/`context` fixtures themselves, so both authoring styles
produce identical artifacts under `test-results/`.

**Two type-checking tiers by design.** This package (`src/` and its own `tests/`) is Pyright
`strict` — full annotations, no implicit `Any`, zero errors, since as a published package its
types are part of the contract. Consumer projects (like `test-framework-project`) use a relaxed
`standard` profile in their own `pyproject.toml` — don't try to make consumer test code pass
strict mode.

**Dependency cool-down + audit is enforced, not just documented.** `[tool.uv] exclude-newer` in
`pyproject.toml` holds resolution to versions published before a chosen date. A real vuln can be
adopted before its cool-down window closes (that's why `pytest` is pinned `>=9.0.3` — CVE fix,
deliberately pulled forward). Bumping any dependency version is a reviewed, explicit
`uv.lock` diff, never implicit.

## Rejected decisions (do not re-litigate or reinvent)

- **Declarative `test("name", action, check, expected)` tuple style** — rejected: breaks on
  multiple checks, value extraction, and UI flows; duplicates Gherkin + `parametrize`.
  Data-driven tests use `pytest.mark.parametrize`; the imperative form is `with step(...):` + `verify.*`.
- **Robot Framework** — out: not pytest, its BDD is keyword sugar.
- **Wrapping pytest internals** (assertions, fixtures, parametrize, discovery) — never; wrap domain only.
- **A second API client beside httpx** (e.g. Playwright's `APIRequestContext`) — httpx is the
  only API path; Playwright is UI-only.
- **GitHub-specific features** (Actions, template repos) — hosting moves on-prem; keep everything
  plain-git and CI-agnostic (checks are CLI commands any runner can call).

## Release gotcha

`scripts/release.py` self-heals one specific case: `uv run` itself can resync the editable
package and touch `uv.lock`'s recorded self-version as a side effect *before* the script's own
git-status "clean tree" check runs. If the only diff is `M uv.lock`, the script auto-commits it
as a small housekeeping commit rather than hard-failing — don't remove that special case, it
will make releases spuriously fail.
