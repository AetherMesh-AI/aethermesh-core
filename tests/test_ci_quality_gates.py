from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import ModuleType
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
QUALITY_GATES_PATH = ROOT / "scripts" / "ci_quality_gates.py"


def load_quality_gates_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "aethermesh_ci_quality_gates", QUALITY_GATES_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load scripts/ci_quality_gates.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WorkflowSecurityTests(unittest.TestCase):
    def test_push_only_release_workflow_can_request_contents_write(self) -> None:
        module = load_quality_gates_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_dir = root / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "release.yml").write_text(
                """
name: Main Alpha Release
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
""".lstrip(),
                encoding="utf-8",
            )

            with mock.patch.object(module, "ROOT", root):
                exit_code = module.command_workflow_security(Namespace())

        self.assertEqual(exit_code, 0)

    def test_pull_request_workflow_cannot_request_contents_write(self) -> None:
        module = load_quality_gates_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workflow_dir = root / ".github" / "workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "unsafe.yml").write_text(
                """
name: Unsafe PR Workflow
on:
  pull_request:
permissions:
  contents: write
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
""".lstrip(),
                encoding="utf-8",
            )

            with mock.patch.object(module, "ROOT", root):
                exit_code = module.command_workflow_security(Namespace())

        self.assertEqual(exit_code, 1)


class DesktopReleaseWorkflowTests(unittest.TestCase):
    def test_stage_step_normalizes_release_asset_names(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "desktop-release.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("artifact_system=MacOS", workflow)
        self.assertIn("artifact_system=Windows", workflow)
        self.assertIn("artifact_system=Linux", workflow)
        self.assertIn("artifact_extension=dmg", workflow)
        self.assertIn("artifact_extension=exe", workflow)
        self.assertIn("artifact_extension=deb", workflow)
        self.assertIn(
            'release_asset="dist/release-upload/'
            "AetherMesh-${RELEASE_VERSION}-${artifact_system}-"
            '${AETHERMESH_TARGET_ARCH}.${artifact_extension}"',
            workflow,
        )
        self.assertIn('cp "$artifact" "$release_asset"', workflow)
        self.assertNotIn('cp "$artifact" dist/release-upload/', workflow)


if __name__ == "__main__":
    unittest.main()
