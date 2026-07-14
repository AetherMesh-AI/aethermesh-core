from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import threading
import time
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FULL_TEST_PATH = ROOT / "scripts" / "full_test.py"


def load_full_test_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "aethermesh_full_test", FULL_TEST_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load scripts/full_test.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FullTestRunnerTests(unittest.TestCase):
    def test_gate_inventory_and_commands_match_serial_baseline(self) -> None:
        module = load_full_test_module()
        python = sys.executable
        expected_fast = [
            ("pytest", (python, "-m", "pytest", "-q", "tests")),
            (
                "branch coverage",
                (
                    python,
                    "-m",
                    "pytest",
                    "-q",
                    "--cov=aethermesh_core",
                    "--cov-branch",
                    "--cov-report=term-missing",
                    "--cov-fail-under=100",
                    "tests",
                ),
            ),
            ("ruff check", ("ruff", "check", "src", "tests", "scripts")),
            (
                "ruff format",
                ("ruff", "format", "--check", "src", "tests", "scripts"),
            ),
            ("mypy", ("mypy", "--strict", "src", "scripts")),
            ("desktop tests", ("npm", "run", "test:desktop")),
            (
                "test integrity",
                (python, "scripts/ci_quality_gates.py", "test-integrity"),
            ),
            (
                "dependency review",
                (
                    python,
                    "scripts/ci_quality_gates.py",
                    "dependency-review",
                    "--base",
                    "chosen/base",
                ),
            ),
            (
                "workflow security",
                (python, "scripts/ci_quality_gates.py", "workflow-security"),
            ),
            (
                "PR size",
                (
                    python,
                    "scripts/ci_quality_gates.py",
                    "pr-size",
                    "--base",
                    "chosen/base",
                    "--max-files",
                    "80",
                    "--max-lines",
                    "10000",
                    "--max-binary-files",
                    "0",
                    "--exclude-path-prefix",
                    "graphify-out/",
                    "--exclude-path-prefix",
                    "wordlists/node-names/",
                ),
            ),
        ]
        expected_full_extra = [
            (
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
            ("complexity", ("radon", "cc", "src", "tests", "scripts", "-s", "-n", "E")),
            (
                "dead code",
                ("vulture", "src", "tests", "scripts", "--min-confidence", "100"),
            ),
            ("bandit", ("bandit", "-q", "-r", "src")),
            (
                "pip audit",
                (python, "scripts/ci_quality_gates.py", "dependency-audit"),
            ),
            ("build", (python, "-m", "build")),
            (
                "mutation",
                (python, "scripts/mutmut_early_fail.py", "--max-children", "4"),
            ),
            (
                "mutation score",
                (
                    python,
                    "scripts/ci_quality_gates.py",
                    "mutation-score",
                    "--minimum",
                    "95",
                ),
            ),
        ]

        fast = module._checks_for_mode("fast", "chosen/base")
        full = module._checks_for_mode("full", "chosen/base")

        self.assertEqual([(check.name, check.command) for check in fast], expected_fast)
        self.assertEqual(
            [(check.name, check.command) for check in full],
            expected_fast + expected_full_extra,
        )

    def test_dag_declares_required_dependencies_and_resource_conflicts(self) -> None:
        module = load_full_test_module()
        checks = {
            check.name: check for check in module._checks_for_mode("full", "base")
        }

        self.assertEqual(checks["mutation"].dependencies, ("pytest", "branch coverage"))
        self.assertEqual(checks["mutation score"].dependencies, ("mutation",))
        self.assertFalse(
            checks["pytest"].resources & checks["branch coverage"].resources
        )
        self.assertIsNotNone(checks["pytest"].env)
        self.assertIsNotNone(checks["branch coverage"].env)
        assert checks["pytest"].env is not None
        assert checks["branch coverage"].env is not None
        self.assertNotEqual(
            checks["pytest"].env["PYTEST_ADDOPTS"],
            checks["branch coverage"].env["PYTEST_ADDOPTS"],
        )
        self.assertIn("COVERAGE_FILE", checks["branch coverage"].env)
        self.assertTrue(
            checks["desktop tests"].resources & checks["duplicate code"].resources
        )
        self.assertTrue(
            checks["ruff check"].resources & checks["ruff format"].resources
        )
        self.assertIn("build-dist", checks["build"].resources)

    def test_missing_required_tools_are_reported_before_running(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check("missing", ("definitely-not-a-real-aethermesh-tool", "--x"))
        ]

        with mock.patch.object(module.shutil, "which", return_value=None):
            exit_code = module.run_checks(checks, keep_going=True, jobs=2)

        self.assertEqual(exit_code, 127)

    def test_scheduler_bounds_concurrency_and_respects_dependencies(self) -> None:
        module = load_full_test_module()
        lock = threading.Lock()
        active = 0
        maximum = 0
        finished: set[str] = set()
        dependency_seen = False
        checks = [
            module.Check("first", (sys.executable,), resources=frozenset({"a"})),
            module.Check("second", (sys.executable,), resources=frozenset({"b"})),
            module.Check("third", (sys.executable,), dependencies=("first",)),
        ]

        def runner(check: object, _: threading.Event) -> object:
            nonlocal active, maximum, dependency_seen
            name = check.name
            with lock:
                if name == "third":
                    dependency_seen = "first" in finished
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.03)
            with lock:
                active -= 1
                finished.add(name)
            return module.CheckResult(check, 0, f"output {name}\n")

        exit_code = module.run_checks(checks, keep_going=True, jobs=2, runner=runner)

        self.assertEqual(exit_code, 0)
        self.assertEqual(maximum, 2)
        self.assertTrue(dependency_seen)

    def test_conflicting_resources_never_overlap(self) -> None:
        module = load_full_test_module()
        lock = threading.Lock()
        active_resources: set[str] = set()
        overlap = False
        checks = [
            module.Check("one", (sys.executable,), resources=frozenset({"shared"})),
            module.Check("two", (sys.executable,), resources=frozenset({"shared"})),
            module.Check("free", (sys.executable,), resources=frozenset({"other"})),
        ]

        def runner(check: object, _: threading.Event) -> object:
            nonlocal overlap
            with lock:
                overlap = overlap or bool(active_resources & check.resources)
                active_resources.update(check.resources)
            time.sleep(0.03)
            with lock:
                active_resources.difference_update(check.resources)
            return module.CheckResult(check, 0, "")

        self.assertEqual(
            module.run_checks(checks, keep_going=True, jobs=3, runner=runner), 0
        )
        self.assertFalse(overlap)

    def test_failure_cancels_pending_work_without_keep_going(self) -> None:
        module = load_full_test_module()
        started: list[str] = []
        checks = [
            module.Check("fail", (sys.executable,), resources=frozenset({"serial"})),
            module.Check("pending", (sys.executable,), resources=frozenset({"serial"})),
        ]

        def runner(check: object, _: threading.Event) -> object:
            started.append(check.name)
            return module.CheckResult(check, 7 if check.name == "fail" else 0, "")

        self.assertEqual(
            module.run_checks(checks, keep_going=False, jobs=2, runner=runner), 1
        )
        self.assertEqual(started, ["fail"])

    def test_keep_going_runs_all_checks_and_collects_failures(self) -> None:
        module = load_full_test_module()
        started: list[str] = []
        checks = [
            module.Check("fail", (sys.executable,)),
            module.Check("pass", (sys.executable,)),
        ]

        def runner(check: object, _: threading.Event) -> object:
            started.append(check.name)
            return module.CheckResult(check, 5 if check.name == "fail" else 0, "")

        self.assertEqual(
            module.run_checks(checks, keep_going=True, jobs=2, runner=runner), 1
        )
        self.assertCountEqual(started, ["fail", "pass"])

    def test_fail_fast_terminates_active_subprocess_groups(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check(
                "fail",
                (
                    sys.executable,
                    "-c",
                    "import time; time.sleep(0.1); raise SystemExit(9)",
                ),
            ),
            module.Check(
                "sleeper",
                (sys.executable, "-c", "import time; time.sleep(30)"),
            ),
        ]
        stdout = io.StringIO()
        started = time.monotonic()

        with contextlib.redirect_stdout(stdout):
            exit_code = module.run_checks(checks, keep_going=False, jobs=2)

        self.assertEqual(exit_code, 1)
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("CANCELLED: sleeper", stdout.getvalue())

    def test_reporting_is_buffered_in_configured_order(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check("slow", (sys.executable,)),
            module.Check("fast", (sys.executable,)),
        ]

        def runner(check: object, _: threading.Event) -> object:
            if check.name == "slow":
                time.sleep(0.03)
            return module.CheckResult(check, 0, f"log-{check.name}\n")

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = module.run_checks(
                checks, keep_going=True, jobs=2, runner=runner
            )

        output = stdout.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertLess(output.index("==> slow"), output.index("==> fast"))
        self.assertLess(output.index("log-slow"), output.index("log-fast"))

    def test_jobs_one_is_exact_serial_fallback(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check("first", (sys.executable,)),
            module.Check("second", (sys.executable,)),
            module.Check("third", (sys.executable,)),
        ]
        order: list[str] = []
        active = 0
        maximum = 0

        def runner(check: object, _: threading.Event) -> object:
            nonlocal active, maximum
            order.append(check.name)
            active += 1
            maximum = max(maximum, active)
            time.sleep(0.01)
            active -= 1
            return module.CheckResult(check, 0, "")

        self.assertEqual(
            module.run_checks(checks, keep_going=True, jobs=1, runner=runner), 0
        )
        self.assertEqual(order, ["first", "second", "third"])
        self.assertEqual(maximum, 1)

    def test_cli_has_safe_jobs_default_and_rejects_zero(self) -> None:
        module = load_full_test_module()
        parser = module.build_parser()

        self.assertGreaterEqual(parser.parse_args([]).jobs, 1)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--jobs", "0"])

    def test_list_mode_prints_commands_without_running(self) -> None:
        module = load_full_test_module()

        with mock.patch.object(module, "run_checks") as run_checks:
            exit_code = module.main(
                ["--mode", "fast", "--base", "origin/main", "--list"]
            )

        self.assertEqual(exit_code, 0)
        run_checks.assert_not_called()


if __name__ == "__main__":
    unittest.main()
