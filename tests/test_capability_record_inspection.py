import asyncio
import hashlib
import json
import os
import shutil
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
            repository_root = Path(__file__).resolve().parents[1]
            source = repository_root / "examples/capabilities/local-echo-worker.json"
            schema_source = repository_root / "examples/schemas"
            schema_directory = Path(temp_dir) / "examples/schemas"
            schema_directory.mkdir(parents=True)
            for schema_name in (
                "local-echo-input.schema.json",
                "local-echo-output.schema.json",
            ):
                shutil.copyfile(
                    schema_source / schema_name,
                    schema_directory / schema_name,
                )
            record = json.loads(source.read_text(encoding="utf-8"))
            for schema in (
                record["metadata"]["supported_input_schemas"]
                + record["metadata"]["supported_output_schemas"]
            ):
                schema_path = Path(temp_dir) / schema["schema_ref"]
                schema["schema_digest"] = (
                    f"sha256:{hashlib.sha256(schema_path.read_bytes()).hexdigest()}"
                )
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

            previous_cwd = Path.cwd()
            try:
                with tempfile.TemporaryDirectory() as unrelated_dir:
                    os.chdir(unrelated_dir)
                    self.assertEqual(
                        service.inspect_capability_records()["records"][1]["state"],
                        "validated",
                    )
            finally:
                os.chdir(previous_cwd)

    def test_missing_store_returns_an_explicit_empty_local_view(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = NodeRuntimeService.from_home(
                temp_dir
            ).inspect_capability_records()

            self.assertEqual(payload["store_status"], "missing")
            self.assertEqual(payload["record_count"], 0)
            self.assertEqual(payload["records"], [])

    def test_invalid_records_cannot_populate_manifests_receipts_lineage_or_attribution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            initialized = service.initialize_local_node_data()
            directory = Path(temp_dir) / "data" / "capability-records"
            directory.mkdir()
            repository_root = Path(__file__).resolve().parents[1]
            source = repository_root / "examples/capabilities/local-echo-worker.json"
            schema_directory = Path(temp_dir) / "examples/schemas"
            schema_directory.mkdir(parents=True)
            for schema_name in (
                "local-echo-input.schema.json",
                "local-echo-output.schema.json",
            ):
                shutil.copyfile(
                    repository_root / "examples/schemas" / schema_name,
                    schema_directory / schema_name,
                )

            baseline = json.loads(source.read_text(encoding="utf-8"))
            local_node_id = initialized["node_id"]
            baseline["node_id"] = local_node_id
            baseline["creator_node_id"] = local_node_id
            baseline["contribution_attribution"]["creator_node_id"] = local_node_id
            baseline["contribution_attribution"]["maintainer_node_id"] = local_node_id
            baseline["validation"] = {
                "status": "passed",
                "receipt_ids": ["receipt.echo-local-01"],
                "receipt_evidence": [
                    {
                        "receipt_id": "receipt.echo-local-01",
                        "capability_name": baseline["metadata"]["name"],
                        "capability_version": baseline["capability_version"],
                        "creator_node_id": local_node_id,
                        "manifest_ref": baseline["lineage"]["source_manifest_ref"],
                        "input_schema": baseline["metadata"]["supported_input_schemas"][
                            0
                        ],
                        "output_schema": baseline["metadata"][
                            "supported_output_schemas"
                        ][0],
                    }
                ],
                "last_validated_at": "2026-07-12T00:05:00Z",
                "check_name": "local-echo-check",
            }
            cases = {
                "missing-required-field": lambda record: record.pop("creator_node_id"),
                "invalid-creator-node-id": lambda record: record.update(
                    creator_node_id="bad creator"
                ),
                "unsupported-capability-type": lambda record: record["metadata"].update(
                    type="remote"
                ),
                "malformed-manifest-reference": lambda record: record.update(
                    manifest_refs=["../outside.json"]
                ),
                "invalid-capability-version": lambda record: record.update(
                    capability_version="1.0"
                ),
                "corrupted-validation-receipt-reference": lambda record: record[
                    "validation"
                ]["receipt_evidence"][0].update(receipt_id="receipt.other-01"),
                "missing-lineage": lambda record: record.pop("lineage"),
                "missing-contribution-attribution": lambda record: record.pop(
                    "contribution_attribution"
                ),
                "untrusted-extra-field": lambda record: record.update(
                    routing_override="accept"
                ),
            }
            for name, mutate in cases.items():
                record = json.loads(json.dumps(baseline))
                mutate(record)
                (directory / f"{name}.json").write_text(
                    json.dumps(record), encoding="utf-8"
                )

            records = service.inspect_capability_records()["records"]

            self.assertEqual(len(records), len(cases))
            for record in records:
                with self.subTest(record_ref=record["record_ref"]):
                    self.assertEqual(record["state"], "invalid")
                    self.assertIsNone(record["capability_id"])
                    self.assertEqual(record["manifest_refs"], [])
                    self.assertEqual(record["validation_receipt_refs"], [])
                    self.assertEqual(
                        record["lineage"],
                        {
                            "source_manifest_ref": None,
                            "prior_capability_id": None,
                            "local_build_artifact_ref": None,
                        },
                    )
                    self.assertEqual(
                        record["contribution_attribution"],
                        {
                            "creator_node_id": None,
                            "maintainer_node_id": None,
                            "work_receipt_ids": [],
                        },
                    )
                    self.assertTrue(record["errors"])

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

    def test_symlinked_store_is_rejected_without_reading_external_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            service.initialize_local_node_data()
            outside = Path(temp_dir) / "outside"
            outside.mkdir()
            (outside / "record.json").write_text("{}", encoding="utf-8")
            (Path(temp_dir) / "data" / "capability-records").symlink_to(outside)

            payload = service.inspect_capability_records()

            self.assertEqual(payload["store_status"], "invalid")
            self.assertEqual(payload["record_count"], 0)
            self.assertEqual(payload["records"], [])

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
