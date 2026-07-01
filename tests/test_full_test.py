from __future__ import annotations

import importlib.util
import sys
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
    def test_fast_mode_lists_core_checks_only(self) -> None:
        module = load_full_test_module()

        checks = module._checks_for_mode("fast", "origin/main")

        self.assertEqual(
            [check.name for check in checks],
            [
                "pytest",
                "branch coverage",
                "ruff check",
                "ruff format",
                "mypy",
                "desktop tests",
                "test integrity",
                "dependency review",
                "workflow security",
                "PR size",
            ],
        )
        self.assertEqual(checks[7].command[-2:], ("--base", "origin/main"))

    def test_full_mode_appends_slow_parity_checks(self) -> None:
        module = load_full_test_module()

        checks = module._checks_for_mode("full", "upstream/main")

        self.assertIn("mutation", [check.name for check in checks])
        self.assertIn("mutation score", [check.name for check in checks])
        self.assertEqual(checks[7].command[-2:], ("--base", "upstream/main"))

    def test_missing_required_tools_are_reported_before_running(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check("missing", ("definitely-not-a-real-aethermesh-tool", "--x"))
        ]

        with mock.patch.object(module.shutil, "which", return_value=None):
            exit_code = module.run_checks(checks, keep_going=True)

        self.assertEqual(exit_code, 127)

    def test_run_checks_stops_on_first_failure_by_default(self) -> None:
        module = load_full_test_module()
        checks = [
            module.Check("first", (sys.executable, "-c", "raise SystemExit(3)")),
            module.Check("second", (sys.executable, "-c", "raise SystemExit(0)")),
        ]
        calls: list[tuple[str, ...]] = []

        def fake_run(command: tuple[str, ...], **_: object) -> object:
            calls.append(command)
            return mock.Mock(returncode=3)

        with mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            exit_code = module.run_checks(checks, keep_going=False)

        self.assertEqual(exit_code, 1)
        self.assertEqual(calls, [checks[0].command])

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
