import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from aethermesh_core.cli import main
from aethermesh_core.local_runtime_config import LOCAL_RUNTIME_CONFIG_PATH
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
                "identity/creator-node.json",
                "manifests/local-node-manifest.json",
                "contributions",
                "receipts",
                "lineage",
                "logs/startup.log",
                "work/inputs",
                "work/outputs",
            ):
                self.assertTrue((runtime / relative_path).exists(), relative_path)
            config = self._load(runtime / LOCAL_RUNTIME_CONFIG_PATH)
            self.assertEqual(config["node"]["node_id"], first["node_id"])
            self.assertEqual(
                config["node"]["creator_node_id"], first["creator_node_id"]
            )
            self.assertIn(
                "do not regenerate",
                config["node"]["creator_node_id_stability"],
            )
            self.assertEqual(
                config["paths"],
                {
                    "identity": "identity/creator-node.json",
                    "manifest": "manifests/local-node-manifest.json",
                    "validation_receipts": "receipts",
                    "lineage": "lineage",
                    "contribution_attribution": "contributions",
                    "log": "logs/startup.log",
                    "work_inputs": "work/inputs",
                    "work_outputs": "work/outputs",
                },
            )
            self.assertNotIn("token", json.dumps(config).lower())
            self.assertNotIn("reward", json.dumps(config).lower())
            self.assertNotIn("dashboard", json.dumps(config).lower())
            self.assertNotIn(
                "p2p", config["network_mode"].lower().replace("no-p2p", "")
            )
            first_dirs = first["runtime_directories"]
            self.assertIsInstance(first_dirs, dict)
            assert isinstance(first_dirs, dict)
            self.assertEqual(first_dirs["receipts"], "receipts")
            self.assertEqual(first_dirs["lineage"], "lineage")
            self.assertEqual(
                config["paths"]["contribution_attribution"], "contributions"
            )
            receipt = self._load(runtime / str(first["validation_receipt_path"]))
            lineage = self._load(runtime / str(first["lineage_path"]))
            self.assertEqual(receipt["receipt_type"], "startup_validation")
            self.assertEqual(receipt["node_id"], first["node_id"])
            self.assertEqual(receipt["creator_node_id"], first["creator_node_id"])
            self.assertEqual(receipt["manifest_hash"], first["manifest_hash"])
            self.assertEqual(receipt["validation_result"]["status"], "passed")
            self.assertFalse(receipt["contribution_attribution"]["scoring_applied"])
            self.assertNotIn("private", json.dumps(receipt).lower())
            self.assertEqual(lineage["lineage_type"], "local_node_startup")
            self.assertEqual(lineage["inputs"]["manifest_hash"], first["manifest_hash"])
            self.assertFalse(lineage["contribution_attribution"]["scoring_applied"])

    def test_existing_identity_missing_manifest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            (runtime / "manifests" / "local-node-manifest.json").unlink()

            with self.assertRaisesRegex(LocalStartupError, "required startup manifest"):
                start_local_node(runtime)

    def test_existing_config_missing_identity_fails_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            first = start_local_node(runtime)
            identity_path = runtime / first.identity_path
            identity_path.unlink()
            receipt_count = len(tuple((runtime / "receipts").iterdir()))
            lineage_count = len(tuple((runtime / "lineage").iterdir()))

            with self.assertRaisesRegex(
                LocalStartupError, "required creator node identity is missing"
            ):
                start_local_node(runtime)

            self.assertFalse(identity_path.exists())
            self.assertEqual(
                len(tuple((runtime / "receipts").iterdir())), receipt_count
            )
            self.assertEqual(len(tuple((runtime / "lineage").iterdir())), lineage_count)

    def test_missing_required_runtime_config_fields_fail_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            for field in (
                "identity",
                "manifest",
                "validation_receipts",
                "lineage",
                "contribution_attribution",
                "log",
                "work_inputs",
                "work_outputs",
            ):
                with self.subTest(field=field):
                    candidate = json.loads(json.dumps(config))
                    paths = candidate["paths"]
                    self.assertIsInstance(paths, dict)
                    assert isinstance(paths, dict)
                    paths.pop(field)
                    config_path.write_text(json.dumps(candidate), encoding="utf-8")

                    with self.assertRaisesRegex(
                        LocalStartupError,
                        f"local runtime config paths.{field} must be a non-empty local path",
                    ):
                        start_local_node(runtime)

    def test_runtime_config_rejects_malformed_version_and_identity_stability(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            cases = (
                ({"version": True}, "must contain version 1"),
                (
                    {"node.creator_node_id_stability": None},
                    "must preserve local identity",
                ),
            )
            for updates, message in cases:
                with self.subTest(updates=updates):
                    candidate = json.loads(json.dumps(config))
                    for key, value in updates.items():
                        if key.startswith("node."):
                            candidate["node"][key.removeprefix("node.")] = value
                        else:
                            candidate[key] = value
                    config_path.write_text(json.dumps(candidate), encoding="utf-8")

                    with self.assertRaisesRegex(LocalStartupError, message):
                        start_local_node(runtime)

    def test_runtime_uses_configured_local_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            first = start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            manifest = self._load(runtime / first.manifest_path)
            config_paths = config["paths"]
            self.assertIsInstance(config_paths, dict)
            assert isinstance(config_paths, dict)
            config_paths.update(
                {
                    "manifest": "configured/manifests/node-manifest.json",
                    "validation_receipts": "configured/receipts",
                    "lineage": "configured/lineage",
                    "contribution_attribution": "configured/contributions",
                    "log": "configured/logs/startup.log",
                    "work_inputs": "configured/work/inputs",
                    "work_outputs": "configured/work/outputs",
                }
            )
            manifest["work_directories"] = {
                "manifests": "configured/manifests",
                "receipts": "configured/receipts",
                "logs": "configured/logs",
                "work_inputs": "configured/work/inputs",
                "work_outputs": "configured/work/outputs",
                "lineage": "configured/lineage",
                "contribution_attribution": "configured/contributions",
            }
            custom_manifest = runtime / str(config_paths["manifest"])
            custom_manifest.parent.mkdir(parents=True)
            custom_manifest.write_text(json.dumps(manifest), encoding="utf-8")
            config_path.write_text(json.dumps(config), encoding="utf-8")

            second = start_local_node(runtime)

            self.assertEqual(second.creator_node_id, first.creator_node_id)
            self.assertEqual(
                second.manifest_path, "configured/manifests/node-manifest.json"
            )
            self.assertTrue(
                second.validation_receipt_path.startswith("configured/receipts/")
            )
            self.assertTrue(second.lineage_path.startswith("configured/lineage/"))
            self.assertEqual(second.log_path, "configured/logs/startup.log")
            self.assertEqual(
                config_paths["contribution_attribution"], "configured/contributions"
            )

    def test_runtime_config_rejects_unsupported_fields_and_nonlocal_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)

            for field_name in ("tokenomics", "reward_policy", "dashboard"):
                with self.subTest(field=field_name):
                    candidate = dict(config)
                    candidate[field_name] = {"enabled": True}
                    config_path.write_text(json.dumps(candidate), encoding="utf-8")
                    with self.assertRaisesRegex(
                        LocalStartupError, "unsupported fields"
                    ):
                        start_local_node(runtime)

            config_path.write_text(json.dumps(config), encoding="utf-8")
            for bad_path in (
                "~/aethermesh",
                "C:/Users/trevoroler/aethermesh",
                "https://example.invalid/config.json",
            ):
                with self.subTest(path=bad_path):
                    candidate = json.loads(json.dumps(config))
                    candidate["paths"]["lineage"] = bad_path
                    config_path.write_text(json.dumps(candidate), encoding="utf-8")
                    with self.assertRaisesRegex(
                        LocalStartupError, "relative local path"
                    ):
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

    def test_overlapping_runtime_paths_fail_before_identity_or_receipt_writes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            identity_path = runtime / "identity" / "creator-node.json"
            identity_before = identity_path.read_bytes()
            receipt_count = len(
                tuple((runtime / "receipts").glob("startup-validation-*.json"))
            )
            lineage_count = len(
                tuple((runtime / "lineage").glob("startup-lineage-*.json"))
            )
            cases = (
                ({"lineage": "receipts/lineage"}, "artifact directories"),
                ({"log": "runtime-config.json"}, "file paths"),
                (
                    {"identity": "records", "manifest": "records/manifest.json"},
                    "file paths",
                ),
                ({"log": "work"}, "must not overlap"),
                ({"work_outputs": "logs"}, "must not overlap"),
            )
            for updates, message in cases:
                with self.subTest(updates=updates):
                    candidate = json.loads(json.dumps(config))
                    candidate["paths"].update(updates)
                    config_path.write_text(json.dumps(candidate), encoding="utf-8")

                    with self.assertRaisesRegex(LocalStartupError, message):
                        start_local_node(runtime)

                    self.assertEqual(identity_path.read_bytes(), identity_before)
                    self.assertEqual(
                        len(
                            tuple(
                                (runtime / "receipts").glob("startup-validation-*.json")
                            )
                        ),
                        receipt_count,
                    )
                    self.assertEqual(
                        len(
                            tuple((runtime / "lineage").glob("startup-lineage-*.json"))
                        ),
                        lineage_count,
                    )

    def test_runtime_paths_cannot_escape_root_through_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            runtime = parent / "runtime"
            outside = parent / "outside"
            runtime.mkdir()
            outside.mkdir()
            (runtime / "work").symlink_to(outside, target_is_directory=True)

            with self.assertRaisesRegex(
                LocalStartupError,
                "paths.work_inputs must stay within the runtime directory",
            ):
                start_local_node(runtime)

            self.assertFalse((runtime / "identity" / "creator-node.json").exists())
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_configured_symlink_escape_fails_before_preserved_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            runtime = parent / "runtime"
            outside = parent / "outside"
            first = start_local_node(runtime)
            outside.mkdir()
            (runtime / "escape").symlink_to(outside, target_is_directory=True)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            config["paths"]["lineage"] = "escape/lineage"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            identity_path = runtime / first.identity_path
            identity_before = identity_path.read_bytes()
            receipt_count = len(tuple((runtime / "receipts").iterdir()))

            with self.assertRaisesRegex(
                LocalStartupError,
                "paths.lineage must stay within the runtime directory",
            ):
                start_local_node(runtime)

            self.assertEqual(identity_path.read_bytes(), identity_before)
            self.assertEqual(
                len(tuple((runtime / "receipts").iterdir())), receipt_count
            )
            self.assertEqual(tuple(outside.iterdir()), ())

    def test_runtime_config_symlink_cannot_escape_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            runtime = parent / "runtime"
            outside_config = parent / "outside-config.json"
            runtime.mkdir()
            outside_config.write_text("not read", encoding="utf-8")
            (runtime / LOCAL_RUNTIME_CONFIG_PATH).symlink_to(outside_config)

            with self.assertRaisesRegex(
                LocalStartupError,
                "local runtime config must stay within the runtime directory",
            ):
                start_local_node(runtime)

            self.assertFalse((runtime / "identity").exists())

    def test_resolved_runtime_paths_cannot_alias_preserved_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            first = start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            identity_path = runtime / first.identity_path
            identity_before = identity_path.read_bytes()
            (runtime / "alias").symlink_to(
                runtime / "receipts", target_is_directory=True
            )
            config["paths"]["lineage"] = "alias"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(
                LocalStartupError,
                "artifact directories must be separate",
            ):
                start_local_node(runtime)

            self.assertEqual(identity_path.read_bytes(), identity_before)

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
            self.assertEqual(first.node_id, reset.node_id)
            self.assertEqual(reset.node_id, reset.creator_node_id)
            self.assertTrue((runtime / "identity" / "identity-quarantine").exists())

            (runtime / LOCAL_RUNTIME_CONFIG_PATH).unlink()
            identity_path = runtime / reset.identity_path
            identity_before = identity_path.read_bytes()
            receipt_count = len(tuple((runtime / "receipts").iterdir()))

            with self.assertRaisesRegex(
                LocalStartupError, "required local runtime config is missing"
            ):
                start_local_node(runtime, reset_creator_identity=True)

            self.assertEqual(identity_path.read_bytes(), identity_before)
            self.assertEqual(
                len(tuple((runtime / "receipts").iterdir())), receipt_count
            )

    def test_reset_uses_configured_identity_and_receipt_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = Path(temp_dir)
            first = start_local_node(runtime)
            config_path = runtime / LOCAL_RUNTIME_CONFIG_PATH
            config = self._load(config_path)
            manifest = self._load(runtime / first.manifest_path)
            custom_identity = runtime / "configured" / "identity" / "creator.json"
            custom_identity.parent.mkdir(parents=True)
            (runtime / first.identity_path).replace(custom_identity)
            config["paths"]["identity"] = "configured/identity/creator.json"
            config["paths"]["validation_receipts"] = "configured/receipts"
            manifest["work_directories"]["receipts"] = "configured/receipts"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            (runtime / first.manifest_path).write_text(
                json.dumps(manifest), encoding="utf-8"
            )

            reset = start_local_node(runtime, reset_creator_identity=True)

            self.assertEqual(reset.identity_path, "configured/identity/creator.json")
            self.assertTrue(
                (runtime / "configured" / "identity" / "identity-quarantine").is_dir()
            )
            self.assertTrue(
                (
                    runtime / "configured" / "receipts" / "identity-reset-receipts.json"
                ).is_file()
            )
            self.assertFalse(
                (runtime / "receipts" / "identity-reset-receipts.json").exists()
            )

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
