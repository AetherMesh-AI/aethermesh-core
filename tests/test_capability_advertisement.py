import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aethermesh_core.runtime_service import NodeRuntimeService, RuntimeServiceError


class CapabilityAdvertisementTests(unittest.TestCase):
    def test_emits_deterministic_manifest_linked_local_advertisement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            initialized = service.initialize_local_node_data()
            config = service.load_config()
            config["capabilities"]["enabled_work_types"] = ["echo"]
            Path(temp_dir, "config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )

            advertisement = service.emit_capability_advertisement()
            artifact_path = Path(temp_dir, "data", "capability-advertisement.json")
            first_bytes = artifact_path.read_bytes()
            repeated = service.emit_capability_advertisement()

            self.assertEqual(advertisement, repeated)
            self.assertEqual(first_bytes, artifact_path.read_bytes())
            self.assertEqual(advertisement["creator_node_id"], initialized["node_id"])
            self.assertEqual(advertisement["scope"], "local-only-no-p2p")
            self.assertEqual(
                advertisement["prototype_status"], "prototype-local-validation-required"
            )
            self.assertEqual(advertisement["node_manifest_ref"], "config.json")
            self.assertEqual(len(advertisement["capabilities"]), 1)
            capability = advertisement["capabilities"][0]
            self.assertEqual(capability["capability_id"], "work.echo")
            self.assertEqual(capability["task_types"], ["echo"])
            self.assertEqual(
                capability["contribution_attribution"]["creator_node_id"],
                initialized["node_id"],
            )
            self.assertTrue(capability["validation_requirements"]["required"])
            self.assertEqual(
                capability["lineage"]["result_manifest_template"],
                "data/job-status/{job_id}.json",
            )
            manifest_path = Path(
                temp_dir, capability["lineage"]["capability_manifest_ref"]
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["creator_node_id"], initialized["node_id"])
            self.assertEqual(manifest["task_type"], "echo")
            self.assertEqual(
                manifest["validation"]["receipt_format"],
                capability["validation_requirements"]["receipt_format"],
            )

    def test_omits_disabled_and_unsupported_configured_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            service.initialize_local_node_data()
            config = service.load_config()
            config["capabilities"]["enabled_work_types"] = ["not-an-executor"]
            Path(temp_dir, "config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )

            advertisement = service.emit_capability_advertisement()

            self.assertEqual(advertisement["capabilities"], [])
            self.assertFalse(Path(temp_dir, "data", "capability-manifests").exists())

    def test_omits_a_configured_capability_when_local_validation_is_degraded(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            service.initialize_local_node_data()
            config = service.load_config()
            config["capabilities"]["enabled_work_types"] = ["echo"]
            Path(temp_dir, "config.json").write_text(
                json.dumps(config), encoding="utf-8"
            )

            with patch.object(
                service,
                "_work_capability_availability",
                return_value={"status": "degraded"},
            ):
                advertisement = service.emit_capability_advertisement()

            self.assertEqual(advertisement["capabilities"], [])

    def test_requires_a_local_node_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)

            with self.assertRaisesRegex(
                RuntimeServiceError, "initialized local node identity"
            ):
                service.emit_capability_advertisement()


if __name__ == "__main__":
    unittest.main()
