#!/usr/bin/env python3
"""Release helper: gate -> bump version -> tag vX.Y.Z -> push.

Usage: uv run scripts/release.py <X.Y.Z>
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"


def run(*cmd: str) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=REPO_ROOT, check=True)


def run_gate() -> None:
    run("make", "check")


def current_version() -> str:
    data = tomllib.loads(PYPROJECT.read_text())
    return str(data["project"]["version"])


def current_branch() -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def parse_version(version: str) -> tuple[int, ...]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
    if match is None:
        print(f"error: version must be X.Y.Z, got {version!r}", file=sys.stderr)
        sys.exit(1)
    return tuple(int(part) for part in match.groups())


def bump_version(new_version: str) -> None:
    text = PYPROJECT.read_text()
    updated = re.sub(r'(?m)^version = "[^"]+"', f'version = "{new_version}"', text, count=1)
    if updated == text:
        raise RuntimeError("version field not found/updated in pyproject.toml")
    PYPROJECT.write_text(updated)

    init_file = REPO_ROOT / "src" / "test_framework" / "__init__.py"
    init_text = init_file.read_text()
    init_updated = re.sub(
        r'(?m)^__version__ = "[^"]+"', f'__version__ = "{new_version}"', init_text, count=1
    )
    if init_updated == init_text:
        raise RuntimeError("__version__ not found/updated in src/test_framework/__init__.py")
    init_file.write_text(init_updated)


def git_status() -> str:
    return subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <X.Y.Z>", file=sys.stderr)
        sys.exit(2)
    new_version = sys.argv[1]

    branch = current_branch()
    if branch != "main":
        print(f"error: releases are cut from a clean main branch, not {branch!r}", file=sys.stderr)
        sys.exit(1)

    if parse_version(new_version) <= parse_version(current_version()):
        print(
            f"error: new version {new_version} must be greater than {current_version()}",
            file=sys.stderr,
        )
        sys.exit(1)

    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    if f"## v{new_version}" not in changelog:
        print(
            f"error: CHANGELOG.md has no '## v{new_version}' entry - write it before tagging",
            file=sys.stderr,
        )
        sys.exit(1)

    # `uv run` itself may resync the editable package and touch uv.lock's
    # recorded self-version before our own code even runs. Self-heal that one
    # narrow case rather than block release on it; anything else still aborts.
    status = git_status()
    if status.strip() == "M uv.lock":
        run("git", "add", "uv.lock")
        run("git", "commit", "-m", "Sync uv.lock")
        status = git_status()

    if status.strip():
        print("error: working tree is not clean", file=sys.stderr)
        sys.exit(1)

    print(f"Current version: {current_version()}")
    run_gate()

    bump_version(new_version)
    run("uv", "lock")  # keeps uv.lock's recorded package version in sync with pyproject.toml
    tag = f"v{new_version}"
    run("git", "add", "pyproject.toml", "src/test_framework/__init__.py", "uv.lock")
    run("git", "commit", "-m", f"Release {tag}")
    run("git", "tag", "-a", tag, "-m", f"Release {tag}")
    run("git", "push", "origin", "HEAD")
    run("git", "push", "origin", tag)

    print(f'\nDone. In a consumer: tag = "{tag}"')


if __name__ == "__main__":
    main()
