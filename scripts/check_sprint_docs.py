"""Fail code pull requests that omit either canonical sprint document.

GitHub workflow supplies the exact PR base/head SHAs; checking the diff rather
than file presence prevents stale documentation from satisfying the gate.
"""
from __future__ import annotations

import argparse
import subprocess
import sys

REQUIRED = frozenset({"docs/DEVELOPMENT_PLAN.md", "docs/SPRINT_LOG.md"})
CODE_PREFIXES = ("mellowstudio/", "tests/", "scripts/", ".github/workflows/")
CODE_FILES = frozenset({"run.py", "dev.ps1", "start_windows.bat", "pyproject.toml", "requirements.txt", "requirements-dev.txt"})


def is_code_path(path: str) -> bool:
    return path.startswith(CODE_PREFIXES) or path in CODE_FILES


def missing_docs(changed_paths: set[str]) -> set[str]:
    if not any(is_code_path(path) for path in changed_paths):
        return set()
    return REQUIRED - changed_paths


def read_git_diff(base: str, head: str) -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACDMRT", base, head],
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def self_test() -> None:
    assert not missing_docs({"README.md"})
    assert not missing_docs(set(REQUIRED))
    assert missing_docs({"mellowstudio/model.py"}) == set(REQUIRED)
    assert missing_docs({"mellowstudio/model.py", "docs/SPRINT_LOG.md"}) == {"docs/DEVELOPMENT_PLAN.md"}
    assert not missing_docs({"mellowstudio/model.py", *REQUIRED})
    assert missing_docs({"tests/test_engine.py"}) == set(REQUIRED)
    assert missing_docs({".github/workflows/tests.yml"}) == set(REQUIRED)
    print("Sprint documentation gate self-tests passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="PR base commit SHA")
    parser.add_argument("--head", help="PR head commit SHA")
    parser.add_argument("--self-test", action="store_true", help="Run local policy checks")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.base or not args.head:
        parser.error("--base and --head are required without --self-test")
    try:
        changed = read_git_diff(args.base, args.head)
    except subprocess.CalledProcessError as exc:
        print(f"Cannot inspect PR diff: {exc.stderr}", file=sys.stderr)
        return 2
    missing = missing_docs(changed)
    if missing:
        print("CODE PR REQUIRES BOTH canonical documentation updates:", file=sys.stderr)
        for path in sorted(missing):
            print(f"  MISSING in PR diff: {path}", file=sys.stderr)
        print("Update planned/actual status and evidence; do not make no-op changes.", file=sys.stderr)
        return 1
    print(f"Sprint documentation gate passed for {len(changed)} changed paths.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
