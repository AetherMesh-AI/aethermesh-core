#!/usr/bin/env python3
"""Portable local validation runner for AetherMesh Core.

The automation loop uses this script before opening a PR so local validation
matches the repository's GitHub quality gates closely enough to catch failures
early.  ``fast`` is intended for normal autonomous-loop cycles; ``full`` adds
slower parity checks such as mutation testing and packaging.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    """One validation command to run."""

    name: str
    command: tuple[str, ...]
    required: bool = True
    env: dict[str, str] | None = None


def _python(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def _base_checks(base: str) -> list[Check]:
    return [
        Check("pytest", _python("-m", "pytest", "-q", "tests"), env=_quiet_py_env()),
        Check(
            "branch coverage",
            _python(
                "-m",
                "pytest",
                "-q",
                "--cov=aethermesh_core",
                "--cov-branch",
                "--cov-report=term-missing",
                "--cov-fail-under=100",
                "tests",
            ),
            env=_quiet_py_env(),
        ),
        Check("ruff check", ("ruff", "check", "src", "tests", "scripts")),
        Check("ruff format", ("ruff", "format", "--check", "src", "tests", "scripts")),
        Check("mypy", ("mypy", "--strict", "src", "scripts")),
        Check("desktop tests", ("npm", "run", "test:desktop")),
        Check(
            "test integrity",
            _python("scripts/ci_quality_gates.py", "test-integrity"),
        ),
        Check(
            "dependency review",
            _python("scripts/ci_quality_gates.py", "dependency-review", "--base", base),
        ),
        Check(
            "workflow security",
            _python("scripts/ci_quality_gates.py", "workflow-security"),
        ),
        Check(
            "PR size",
            _python(
                "scripts/ci_quality_gates.py",
                "pr-size",
                "--base",
                base,
                "--max-files",
                "80",
                "--max-lines",
                "10000",
                "--max-binary-files",
                "0",
                "--exclude-path-prefix",
                "graphify-out/",
            ),
        ),
    ]


def _full_extra_checks() -> list[Check]:
    return [
        Check(
            "duplicate code",
            (
                "npx",
                "--yes",
                "jscpd@5.0.11",
                "src",
                "--format",
                "python",
                "--threshold",
                "0",
                "--reporters",
                "console",
                "--ignore",
                "**/__pycache__/**",
                "--no-tips",
            ),
        ),
        Check(
            "complexity", ("radon", "cc", "src", "tests", "scripts", "-s", "-n", "E")
        ),
        Check(
            "dead code",
            ("vulture", "src", "tests", "scripts", "--min-confidence", "100"),
        ),
        Check("bandit", ("bandit", "-q", "-r", "src")),
        Check("pip audit", _python("scripts/ci_quality_gates.py", "dependency-audit")),
        Check("build", _python("-m", "build")),
        Check(
            "mutation", _python("scripts/mutmut_early_fail.py", "--max-children", "4")
        ),
        Check(
            "mutation score",
            _python("scripts/ci_quality_gates.py", "mutation-score", "--minimum", "95"),
        ),
    ]


def _quiet_py_env() -> dict[str, str]:
    return {"PYTHONDONTWRITEBYTECODE": "1"}


def _command_available(command: str) -> bool:
    if command == sys.executable:
        return True
    return shutil.which(command) is not None


def _missing_required_tools(checks: Iterable[Check]) -> list[str]:
    missing: list[str] = []
    for check in checks:
        executable = check.command[0]
        if check.required and not _command_available(executable):
            missing.append(f"{check.name}: {executable}")
    return missing


def _merged_env(overrides: dict[str, str] | None) -> dict[str, str]:
    env = os.environ.copy()
    if overrides:
        env.update(overrides)
    return env


def _run_check(check: Check) -> int:
    print(f"\n==> {check.name}", flush=True)
    print("$ " + " ".join(check.command), flush=True)
    completed = subprocess.run(
        check.command,
        cwd=ROOT,
        env=_merged_env(check.env),
        check=False,
    )
    if completed.returncode == 0:
        print(f"PASS: {check.name}", flush=True)
    else:
        print(f"FAIL: {check.name} exited {completed.returncode}", flush=True)
    return int(completed.returncode)


def _checks_for_mode(mode: str, base: str) -> list[Check]:
    checks = _base_checks(base)
    if mode == "full":
        checks.extend(_full_extra_checks())
    return checks


def run_checks(checks: Sequence[Check], *, keep_going: bool) -> int:
    missing = _missing_required_tools(checks)
    if missing:
        print("Missing required validation tools:", file=sys.stderr)
        for item in missing:
            print(f"- {item}", file=sys.stderr)
        return 127

    failures: list[tuple[str, int]] = []
    for check in checks:
        returncode = _run_check(check)
        if returncode != 0:
            failures.append((check.name, returncode))
            if not keep_going:
                break

    if failures:
        print("\nValidation failed:", file=sys.stderr)
        for name, returncode in failures:
            print(f"- {name}: exit {returncode}", file=sys.stderr)
        return 1

    print("\nValidation passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("fast", "full"),
        default="fast",
        help="Validation set to run. fast omits slow parity checks; full includes them.",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref for diff-aware checks such as dependency review and PR size.",
    )
    parser.add_argument(
        "--keep-going",
        action="store_true",
        help="Run remaining checks after a failure and report all failures at the end.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print the checks that would run, then exit.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    checks = _checks_for_mode(args.mode, args.base)
    if args.list:
        for check in checks:
            print(f"{check.name}: {' '.join(check.command)}")
        return 0
    return run_checks(checks, keep_going=args.keep_going)


if __name__ == "__main__":
    raise SystemExit(main())
