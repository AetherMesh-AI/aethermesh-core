import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from aethermesh_core.cli import main
from aethermesh_core.local_startup import LocalStartupError, start_local_node
from aethermesh_core.version_metadata import capture_version_metadata


class LocalNodeStartupTests(unittest.TestCase):
    def test_clean_startup_creates_auditable_artifacts_and_preserves_identity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)

            first = start_local_node(runtime).to_dict()
            second = start_local_node(runtime).to_dict()

            self.assertEqual(first["node_id"], second["node_id"])
            self.assertEqual(first["creator_node_id"], second["creator_node_id"])
            self.assertEqual(first["network_mode"], "local-only-no-p2p")
            for relative_path in (
                "local-runtime-config.json",
                "identity/creator-node.json",
                "manifests/local-node-manifest.json",
                "logs/startup.log",
                "work/inputs",
                "work/outputs",
                "contributions",
            ):
                self.assertTrue((runtime / relative_path).exists(), relative_path)
            config = self._load(runtime / "local-runtime-config.json")
            self.assertEqual(config["creator_node_id"], first["creator_node_id"])
            self.assertEqual(config["identity_path"], first["identity_path"])
            self.assertEqual(config["manifest_path"], first["manifest_path"])
            self.assertEqual(config["validation_receipts_dir"], "receipts")
            self.assertEqual(config["lineage_dir"], "lineage")
            self.assertEqual(config["contribution_attribution_dir"], "contributions")
            runtime_directories = first["runtime_directories"]
            self.assertIsInstance(runtime_directories, dict)
            if not isinstance(runtime_directories, dict):
                raise AssertionError("runtime_directories must be a dict")
            self.assertEqual(runtime_directories["receipts"], "receipts")
            self.assertEqual(runtime_directories["lineage"], "lineage")
            self.assertEqual(
                runtime_directories["contribution_attribution"], "contributions"
            )
            receipt = self._load(runtime / str(first["validation_receipt_path"]))
            lineage = self._load(runtime / str(first["lineage_path"]))
            manifest = self._load(runtime / str(first["manifest_path"]))
            self.assertEqual(
                manifest["work_directories"]["contribution_attribution"],
                "contributions",
            )
            self.assertEqual(receipt["receipt_type"], "startup_validation")
            self.assertEqual(receipt["node_id"], first["node_id"])
            self.assertEqual(receipt["creator_node_id"], first["creator_node_id"])
            self.assertEqual(receipt["manifest_hash"], first["manifest_hash"])
            self.assertEqual(receipt["validation_result"]["status"], "passed")
            self.assertFalse(receipt["contribution_attribution"]["scoring_applied"])
            self.assertNotIn("private", json.dumps(receipt).lower())
            self.assertEqual(lineage["lineage_type"], "local_node_startup")
            self.assertEqual(lineage["inputs"]["manifest_hash"], first["manifest_hash"])
            self.assertEqual(
                lineage["inputs"]["configuration"], "local-runtime-config.json"
            )
            self.assertFalse(lineage["contribution_attribution"]["scoring_applied"])

    def test_existing_config_missing_required_field_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            runtime.mkdir(parents=True, exist_ok=True)
            (runtime / "local-runtime-config.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "runtime_mode": "local_only",
                        "creator_node_id": "creator",
                        "identity_path": "identity/creator-node.json",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                LocalStartupError, "missing required field 'manifest_path'"
            ):
                start_local_node(runtime)

    def test_existing_identity_missing_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            (runtime / "manifests" / "local-node-manifest.json").unlink()

            with self.assertRaisesRegex(LocalStartupError, "required startup manifest"):
                start_local_node(runtime)

    def test_corrupt_manifest_fails_before_new_receipt_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            receipt_count = len(
                tuple((runtime / "receipts").glob("startup-validation-*.json"))
            )
            (runtime / "manifests" / "local-node-manifest.json").write_text(
                "{not json", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                LocalStartupError, "startup manifest JSON is malformed"
            ):
                start_local_node(runtime)
            self.assertEqual(
                len(tuple((runtime / "receipts").glob("startup-validation-*.json"))),
                receipt_count,
            )

    def test_invalid_manifest_fields_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            manifest_path = runtime / "manifests" / "local-node-manifest.json"
            manifest = self._load(manifest_path)
            manifest["validation"]["external_services_required"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(
                LocalStartupError, "validation.external_services_required"
            ):
                start_local_node(runtime)

    def test_reset_creator_identity_requires_explicit_flag_and_rotates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            first = start_local_node(runtime)
            second = start_local_node(runtime)
            self.assertEqual(first.node_id, second.node_id)
            reset = start_local_node(runtime, reset_creator_identity=True)
            self.assertNotEqual(first.node_id, reset.node_id)
            self.assertEqual(reset.node_id, reset.creator_node_id)
            self.assertTrue((runtime / "identity" / "identity-quarantine").exists())

    def test_cli_starts_local_node_and_reports_startup_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["start-local-node", "--runtime-dir", temp_dir])
            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["validation_result"], "passed")

            stderr = io.StringIO()
            with patch(
                "aethermesh_core.cli.start_local_node",
                side_effect=LocalStartupError("manifest bad"),
            ):
                with contextlib.redirect_stderr(stderr):
                    exit_code = main(["start-local-node", "--runtime-dir", temp_dir])
            self.assertEqual(exit_code, 1)
            self.assertIn("manifest bad", stderr.getvalue())

    def test_manifest_validation_rejects_bad_shapes(self) -> None:
        cases = (
            ("version", 2, "version 1"),
            ("manifest_type", "other", "manifest_type"),
            ("node", "bad", "node must be an object"),
            ("capabilities", [], "capabilities"),
            ("runtime_version", {"bad": True}, "version metadata"),
            ("validation", "bad", "validation must be an object"),
            ("work_directories", [], "work_directories must be an object"),
        )
        for key, value, message in cases:
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as temp_dir:
                    runtime = Path(temp_dir)
                    start_local_node(runtime)
                    manifest_path = runtime / "manifests" / "local-node-manifest.json"
                    manifest = self._load(manifest_path)
                    manifest[key] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(LocalStartupError, message):
                        start_local_node(runtime)

    def test_manifest_validation_rejects_identity_and_directory_mismatches(
        self,
    ) -> None:
        cases = (
            (("node", "node_id"), "other", "node_id does not match"),
            (("node", "creator_node_id"), "other", "creator_node_id does not match"),
            (("work_directories", "logs"), "elsewhere", "work_directories.logs"),
        )
        for path, value, message in cases:
            with self.subTest(path=path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    runtime = Path(temp_dir)
                    start_local_node(runtime)
                    manifest_path = runtime / "manifests" / "local-node-manifest.json"
                    manifest = self._load(manifest_path)
                    section, field = path
                    manifest[section][field] = value
                    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                    with self.assertRaisesRegex(LocalStartupError, message):
                        start_local_node(runtime)

    def test_low_level_startup_errors_are_reported_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            identity_path = runtime / "identity" / "creator-node.json"
            identity = self._load(identity_path)
            identity["node"].pop("creator_node_id")
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaisesRegex(LocalStartupError, "creator_node_id"):
                start_local_node(runtime)

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            (runtime / "logs").parent.mkdir(parents=True, exist_ok=True)
            (runtime / "logs").write_text("not a directory", encoding="utf-8")
            with self.assertRaisesRegex(
                LocalStartupError, "required runtime directory"
            ):
                start_local_node(runtime)

        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            manifest_dir = runtime / "manifests"
            manifest_dir.mkdir(parents=True)
            manifest_path = manifest_dir / "local-node-manifest.json"
            manifest_path.write_text(json.dumps({"version": 1}), encoding="utf-8")
            with patch(
                "aethermesh_core.local_startup.load_or_create_identity",
                side_effect=ValueError("identity backend failed"),
            ):
                with self.assertRaises(ValueError):
                    start_local_node(runtime)

    def test_default_manifest_uses_current_runtime_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            metadata = capture_version_metadata(captured_at="2026-01-01T00:00:00+00:00")
            with patch(
                "aethermesh_core.local_startup.capture_version_metadata",
                return_value=metadata,
            ):
                result = start_local_node(runtime)
            manifest = self._load(runtime / result.manifest_path)
            self.assertEqual(manifest["runtime_version"], metadata)

    @staticmethod
    def _load(path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
        if not isinstance(document, dict):
            raise AssertionError("expected object")
        return document


if __name__ == "__main__":
    unittest.main()
