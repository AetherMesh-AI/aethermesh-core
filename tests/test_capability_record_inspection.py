import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import httpx

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService


class CapabilityRecordInspectionTests(unittest.TestCase):
    def test_local_records_preserve_provenance_and_degrade_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            initialized = service.initialize_local_node_data()
            directory = Path(temp_dir) / "data" / "capability-records"
            directory.mkdir()
            source = (
                Path(__file__).parents[1]
                / "examples/capabilities/local-echo-worker.json"
            )
            record = json.loads(source.read_text(encoding="utf-8"))
            record["node_id"] = initialized["node_id"]
            record["creator_node_id"] = initialized["node_id"]
            record["contribution_attribution"]["creator_node_id"] = initialized[
                "node_id"
            ]
            record["contribution_attribution"]["maintainer_node_id"] = initialized[
                "node_id"
            ]
            unvalidated = json.loads(json.dumps(record))
            record["validation"] = {
                "status": "passed",
                "receipt_ids": ["receipt.echo-local-01"],
                "receipt_evidence": [
                    {
                        "receipt_id": "receipt.echo-local-01",
                        "capability_name": record["metadata"]["name"],
                        "capability_version": record["capability_version"],
                        "creator_node_id": initialized["node_id"],
                        "manifest_ref": record["lineage"]["source_manifest_ref"],
                        "input_schema": record["metadata"]["supported_input_schemas"][
                            0
                        ],
                        "output_schema": record["metadata"]["supported_output_schemas"][
                            0
                        ],
                    }
                ],
                "last_validated_at": "2026-07-12T00:05:00Z",
                "check_name": "local-echo-check",
            }
            (directory / "echo.json").write_text(json.dumps(record), encoding="utf-8")
            (directory / "unvalidated.json").write_text(
                json.dumps(unvalidated), encoding="utf-8"
            )
            (directory / "broken.json").write_text("{broken", encoding="utf-8")

            async def fetch() -> httpx.Response:
                transport = httpx.ASGITransport(app=create_app(service))
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    return await client.get("/api/capability-records")

            response = asyncio.run(fetch())
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["store_status"], "available")
            self.assertEqual(payload["record_count"], 3)
            self.assertEqual(
                [item["record_ref"] for item in payload["records"]],
                [
                    "data/capability-records/broken.json",
                    "data/capability-records/echo.json",
                    "data/capability-records/unvalidated.json",
                ],
            )
            broken, echo, advertised = payload["records"]
            self.assertEqual(broken["state"], "invalid")
            self.assertEqual(broken["capability_id"], None)
            self.assertEqual(broken["manifest_refs"], [])
            self.assertEqual(echo["state"], "validated")
            self.assertEqual(echo["creator_node_id"], initialized["node_id"])
            self.assertEqual(echo["manifest_refs"], record["manifest_refs"])
            self.assertEqual(
                echo["lineage"]["source_manifest_ref"],
                record["lineage"]["source_manifest_ref"],
            )
            self.assertIsNone(echo["lineage"]["prior_capability_id"])
            self.assertIsNone(echo["lineage"]["local_build_artifact_ref"])
            self.assertEqual(
                echo["contribution_attribution"], record["contribution_attribution"]
            )
            self.assertEqual(echo["validation_receipt_refs"], ["receipt.echo-local-01"])
            self.assertEqual(advertised["state"], "advertised")
            self.assertEqual(advertised["validation_receipt_refs"], [])

    def test_missing_store_returns_an_explicit_empty_local_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = NodeRuntimeService.from_home(
                temp_dir
            ).inspect_capability_records()

            self.assertEqual(payload["store_status"], "missing")
            self.assertEqual(payload["record_count"], 0)
            self.assertEqual(payload["records"], [])

    def test_symlinked_record_is_reported_invalid_without_being_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            service.initialize_local_node_data()
            directory = Path(temp_dir) / "data" / "capability-records"
            directory.mkdir()
            (directory / "linked.json").symlink_to(Path(temp_dir) / "outside.json")

            payload = service.inspect_capability_records()

            self.assertEqual(payload["records"][0]["state"], "invalid")
            self.assertEqual(
                payload["records"][0]["errors"],
                ["capability record must not be a symbolic link"],
            )

    def test_record_without_local_identity_is_reported_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "data" / "capability-records"
            directory.mkdir(parents=True)
            (directory / "record.json").write_text("{}", encoding="utf-8")

            payload = NodeRuntimeService.from_home(
                temp_dir
            ).inspect_capability_records()

            self.assertEqual(payload["records"][0]["state"], "invalid")
            self.assertEqual(
                payload["records"][0]["errors"], ["local node identity is unavailable"]
            )
