#!/usr/bin/env python3
"""Small CI guardrails that are easier to keep correct in Python than shell."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
FORBIDDEN_SUPPRESSION_RE = re.compile(
    r"(pytest\.mark\.skip|pytest\.mark\.xfail|unittest\.skip|\bskip\(|\bxfail\(|type:\s*ignore|#\s*noqa|pragma:\s*no cover|coverage:\s*ignore)",
    re.IGNORECASE,
)


def run(
    args: list[str], *, cwd: Path = ROOT, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def load_pyproject(path: Path = PYPROJECT) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def project_dependencies(pyproject: dict[str, Any]) -> set[str]:
    project = pyproject.get("project", {})
    deps = project.get("dependencies", [])
    if not isinstance(deps, list):
        raise SystemExit("[project].dependencies must be a list")
    return {str(dep).strip() for dep in deps if str(dep).strip()}


def dependency_justifications(pyproject: dict[str, Any]) -> dict[str, str]:
    table = (
        pyproject.get("tool", {})
        .get("aethermesh", {})
        .get("dependency_justifications", {})
    )
    if not isinstance(table, dict):
        raise SystemExit("[tool.aethermesh.dependency_justifications] must be a table")
    return {str(key): str(value).strip() for key, value in table.items()}


def changed_pyproject_from_base(base_ref: str) -> dict[str, Any] | None:
    result = run(["git", "show", f"{base_ref}:pyproject.toml"])
    if result.returncode != 0:
        return None
    return tomllib.loads(result.stdout)


def command_test_integrity(_: argparse.Namespace) -> int:
    violations: list[str] = []
    for directory in (ROOT / "src", ROOT / "tests"):
        for path in sorted(directory.rglob("*.py")):
            rel = path.relative_to(ROOT)
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                if (
                    FORBIDDEN_SUPPRESSION_RE.search(line)
                    and "justification:" not in line.lower()
                ):
                    violations.append(
                        f"{rel}:{line_number}: suppression requires inline justification: {line.strip()}"
                    )
    if violations:
        print("Unjustified test/type/lint/coverage suppressions found:")
        print("\n".join(violations))
        return 1
    print(
        "No unjustified skip/xfail/type-ignore/noqa/coverage-ignore suppressions found."
    )
    return 0


def command_dependency_review(args: argparse.Namespace) -> int:
    current = load_pyproject()
    previous = changed_pyproject_from_base(args.base)
    if previous is None:
        print(
            f"Base pyproject not found at {args.base}; validating current dependencies only."
        )
        previous_deps: set[str] = set()
    else:
        previous_deps = project_dependencies(previous)
    current_deps = project_dependencies(current)
    additions = sorted(current_deps - previous_deps)
    justifications = dependency_justifications(current)
    missing = [dep for dep in additions if not justifications.get(dep)]
    if missing:
        print(
            "New runtime dependencies require [tool.aethermesh.dependency_justifications] entries:"
        )
        print("\n".join(f"- {dep}" for dep in missing))
        return 1
    if additions:
        print("New runtime dependencies are justified:")
        for dep in additions:
            print(f"- {dep}: {justifications[dep]}")
    else:
        print("No new runtime dependencies detected.")
    return 0


def command_dependency_audit(_: argparse.Namespace) -> int:
    deps = sorted(project_dependencies(load_pyproject()))
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".txt", delete=False
    ) as handle:
        req_path = Path(handle.name)
        handle.write("\n".join(deps))
        if deps:
            handle.write("\n")
    try:
        result = run(
            [sys.executable, "-m", "pip_audit", "--strict", "-r", str(req_path)]
        )
        print(result.stdout, end="")
        return result.returncode
    finally:
        req_path.unlink(missing_ok=True)


def command_mutation_score(args: argparse.Namespace) -> int:
    result = run(["mutmut", "results", "--all", "true"])
    print(result.stdout, end="")
    text = result.stdout.lower()
    killed = len(re.findall(r"\bkilled\b", text))
    survived = len(re.findall(r"\bsurvived\b", text))
    timeout = len(re.findall(r"\btimeout\b", text))
    suspicious = len(re.findall(r"\bsuspicious\b", text))
    total = killed + survived + timeout + suspicious
    if total == 0:
        print("Could not parse mutmut results; no mutants found in output.")
        return 1
    score = killed / total * 100.0
    print(f"Mutation score: {score:.2f}% ({killed}/{total} killed)")
    if score < args.minimum:
        print(
            f"Mutation score below required threshold: {score:.2f}% < {args.minimum:.2f}%"
        )
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    test_integrity = sub.add_parser("test-integrity")
    test_integrity.set_defaults(func=command_test_integrity)

    dep_review = sub.add_parser("dependency-review")
    dep_review.add_argument("--base", default="origin/main")
    dep_review.set_defaults(func=command_dependency_review)

    dep_audit = sub.add_parser("dependency-audit")
    dep_audit.set_defaults(func=command_dependency_audit)

    mutation = sub.add_parser("mutation-score")
    mutation.add_argument("--minimum", type=float, default=95.0)
    mutation.set_defaults(func=command_mutation_score)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
