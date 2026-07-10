import json
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aethermesh_core.cli import main
from aethermesh_core.runtime import (
    _string_list,
    inspect_local_node_runtime,
    restart_local_node_runtime,
    start_local_node_runtime,
    stop_local_node_runtime,
    validate_local_node_results,
)


class LocalRuntimeBoundaryTests(unittest.TestCase):
    def test_runtime_reference_helper_treats_absent_refs_as_empty(self) -> None:
        self.assertEqual(_string_list(None), [])

    def test_runtime_start_stop_restart_and_inspect_preserve_local_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            startup = start_local_node_runtime(root)
            inspected = inspect_local_node_runtime(root)
            stopped = stop_local_node_runtime(root)
            restarted = restart_local_node_runtime(root)
            inspected_after_restart = inspect_local_node_runtime(root)
            receipt_refs = cast(list[str], inspected["validation_receipt_refs"])
            lineage_refs = cast(list[str], inspected["lineage_refs"])
            restarted_receipt_refs = cast(
                list[str], inspected_after_restart["validation_receipt_refs"]
            )

            self.assertEqual(startup.node_id, inspected["node_id"])
            self.assertEqual(startup.creator_node_id, inspected["creator_node_id"])
            self.assertTrue(inspected["manifest_matches_identity"])
            self.assertEqual(
                inspected["manifest_path"], "manifests/local-node-manifest.json"
            )
            self.assertIn(startup.validation_receipt_path, receipt_refs)
            self.assertIn(startup.lineage_path, lineage_refs)
            self.assertEqual(inspected["contribution_refs"], [])
            self.assertEqual(
                inspected["attribution_creator_node_id"], startup.creator_node_id
            )
            self.assertEqual(inspected["attribution_node_id"], startup.node_id)
            self.assertEqual(stopped.node_id, startup.node_id)
            self.assertEqual(stopped.creator_node_id, startup.creator_node_id)
            self.assertEqual(restarted.node_id, startup.node_id)
            self.assertEqual(restarted.creator_node_id, startup.creator_node_id)
            self.assertTrue(inspected_after_restart["manifest_matches_identity"])
            self.assertIn(
                restarted.restart_receipt_path,
                restarted_receipt_refs,
            )

    def test_runtime_lifecycle_uses_configured_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            startup = start_local_node_runtime(root)
            config_path = root / "runtime-config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            manifest = json.loads((root / startup.manifest_path).read_text())
            config["paths"].update(
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
            custom_manifest = root / "configured" / "manifests" / "node-manifest.json"
            custom_manifest.parent.mkdir(parents=True)
            custom_manifest.write_text(json.dumps(manifest), encoding="utf-8")
            config_path.write_text(json.dumps(config), encoding="utf-8")

            configured_startup = start_local_node_runtime(root)
            contribution_dir = root / "configured" / "contributions"
            contribution_dir.mkdir(parents=True, exist_ok=True)
            (contribution_dir / "contribution-0001.json").write_text(
                json.dumps({"node_id": startup.node_id}), encoding="utf-8"
            )
            queued_work = root / "configured" / "work" / "inputs" / "queued.json"
            queued_work.parent.mkdir(parents=True, exist_ok=True)
            queued_work.write_text("{}", encoding="utf-8")

            inspected = inspect_local_node_runtime(root)
            stopped = stop_local_node_runtime(root)
            restarted = restart_local_node_runtime(root)

            self.assertEqual(
                inspected["manifest_path"], "configured/manifests/node-manifest.json"
            )
            self.assertIn(
                configured_startup.validation_receipt_path,
                cast(list[str], inspected["validation_receipt_refs"]),
            )
            self.assertEqual(
                inspected["contribution_refs"],
                ["configured/contributions/contribution-0001.json"],
            )
            self.assertEqual(stopped.contribution_record_count, 1)
            self.assertEqual(stopped.interrupted_work_count, 1)
            self.assertTrue(
                restarted.restart_receipt_path.startswith("configured/receipts/")
            )

    def test_runtime_inspect_supports_legacy_default_paths_without_config(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            startup = start_local_node_runtime(root)
            (root / "runtime-config.json").unlink()
            (root / "contributions").rmdir()

            inspected = inspect_local_node_runtime(root)

            self.assertEqual(inspected["node_id"], startup.node_id)
            self.assertEqual(
                inspected["manifest_path"], "manifests/local-node-manifest.json"
            )
            self.assertEqual(inspected["contribution_refs"], [])

    def test_runtime_validation_wrapper_delegates_to_validation_boundary(
        self,
    ) -> None:
        with patch(
            "aethermesh_core.runtime._validate_local_results",
            return_value={"validation_result": "passed"},
        ) as validate:
            result = validate_local_node_results(
                assignment_log_path="assignments.jsonl",
                result_log_path="results.jsonl",
                validation_log_path="validation.jsonl",
            )

        self.assertEqual(result, {"validation_result": "passed"})
        validate.assert_called_once_with(
            assignment_log_path="assignments.jsonl",
            result_log_path="results.jsonl",
            validation_log_path="validation.jsonl",
        )

    def test_cli_lifecycle_uses_structured_runtime_result_without_owning_logic(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            structured_payload = {"node_id": "node-from-runtime", "ok": True}

            class FakeStartup:
                def to_dict(self) -> dict[str, object]:
                    return structured_payload

            with patch(
                "aethermesh_core.cli.start_local_node",
                return_value=FakeStartup(),
            ) as runtime_start:
                with patch("builtins.print") as printed:
                    exit_code = main(["start-local-node", "--runtime-dir", temp_dir])

            self.assertEqual(exit_code, 0)
            runtime_start.assert_called_once_with(
                temp_dir, reset_creator_identity=False
            )
            printed.assert_called_once()
            self.assertEqual(
                json.loads(str(printed.call_args.args[0])), structured_payload
            )


if __name__ == "__main__":
    unittest.main()
