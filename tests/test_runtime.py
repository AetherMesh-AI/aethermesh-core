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
