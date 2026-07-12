import copy
import unittest
from typing import Any

from aethermesh_core.capability_record import (
    CapabilityRecordError,
    validate_capability_record,
)
from aethermesh_core.identity import load_or_create_identity


class CapabilityRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = {
            "schema_version": 1,
            "capability_id": "capability.echo-v1",
            "capability_version": "1.0.0",
            "node_id": "node.local-01",
            "creator_node_id": "node.local-01",
            "created_at": "2026-07-11T12:00:00Z",
            "updated_at": "2026-07-11T12:05:00Z",
            "metadata": {
                "name": "Local echo worker",
                "description": "Returns a local input message.",
                "type": "worker",
                "supported_input_formats": ["application/json"],
                "supported_input_schemas": [
                    {
                        "schema_ref": "examples/schemas/local-echo-input.schema.json",
                        "schema_id": "local-echo-input",
                        "schema_version": "1.0.0",
                        "schema_digest": "sha256:f25619d3f165bd8802258148a37ab97f62fee632354fd9c29765d253cefb4790",
                    }
                ],
                "supported_output_formats": ["application/json"],
                "supported_output_schemas": [
                    {
                        "schema_ref": "examples/schemas/local-echo-output.schema.json",
                        "schema_id": "local-echo-output",
                        "schema_version": "1.0.0",
                        "schema_digest": "sha256:13c661c1f26b58c74a0c5c165b602408e9f8e408b217b171aff2798fe2ccc073",
                    }
                ],
                "constraints": {"network_mode": "local-only-no-p2p"},
                "local_execution_requirements": ["python>=3.11"],
            },
            "manifest_refs": ["manifests/local-echo-worker.json"],
            "validation": {
                "status": "passed",
                "receipt_ids": ["receipt.echo-smoke-01"],
                "receipt_evidence": [
                    {
                        "receipt_id": "receipt.echo-smoke-01",
                        "capability_name": "Local echo worker",
                        "capability_version": "1.0.0",
                        "creator_node_id": "node.local-01",
                        "manifest_ref": "manifests/local-echo-worker.json",
                        "input_schema": {
                            "schema_ref": "examples/schemas/local-echo-input.schema.json",
                            "schema_id": "local-echo-input",
                            "schema_version": "1.0.0",
                            "schema_digest": "sha256:f25619d3f165bd8802258148a37ab97f62fee632354fd9c29765d253cefb4790",
                        },
                        "output_schema": {
                            "schema_ref": "examples/schemas/local-echo-output.schema.json",
                            "schema_id": "local-echo-output",
                            "schema_version": "1.0.0",
                            "schema_digest": "sha256:13c661c1f26b58c74a0c5c165b602408e9f8e408b217b171aff2798fe2ccc073",
                        },
                    }
                ],
                "last_validated_at": "2026-07-11T12:05:00Z",
                "check_name": "echo-smoke-test",
            },
            "lineage": {
                "source_manifest_ref": "manifests/local-echo-worker.json",
                "prior_capability_id": None,
                "local_build_artifact_ref": "artifacts/echo-worker-v1.whl",
            },
            "contribution_attribution": {
                "creator_node_id": "node.local-01",
                "maintainer_node_id": "node.local-01",
                "work_receipt_ids": ["work.echo-0001"],
            },
        }

    def validate(
        self, document: object, *, local_node_id: str = "node.local-01"
    ) -> dict[str, Any]:
        return validate_capability_record(document, local_node_id=local_node_id)

    def test_accepts_complete_passed_record(self) -> None:
        self.assertIs(self.validate(self.record), self.record)

    def test_accepts_explicitly_unvalidated_record_without_trust_evidence(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"] = {
            "status": "unvalidated",
            "receipt_ids": [],
            "receipt_evidence": [],
        }
        record["lineage"].pop("prior_capability_id")
        record["lineage"].pop("local_build_artifact_ref")

        self.assertIs(self.validate(record), record)

    def test_accepts_failed_record_with_reason(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"] = {
            "status": "failed",
            "receipt_ids": [],
            "receipt_evidence": [],
            "last_validated_at": "2026-07-11T12:05:00Z",
            "check_name": "echo-smoke-test",
            "failure_reason": "expected echo output was absent",
        }

        self.assertIs(self.validate(record), record)

    def test_rejects_required_identity_manifest_and_validation_fields(self) -> None:
        for field, expected in (
            ("capability_version", "capability_version"),
            ("node_id", "node_id"),
            ("creator_node_id", "creator_node_id"),
            ("manifest_refs", "manifest_refs"),
            ("validation", "validation"),
        ):
            with self.subTest(field=field):
                record = copy.deepcopy(self.record)
                record.pop(field)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_blank_node_id(self) -> None:
        record = copy.deepcopy(self.record)
        record["node_id"] = ""

        with self.assertRaisesRegex(CapabilityRecordError, "node_id"):
            self.validate(record)

    def test_validates_node_id_against_persisted_local_identity(self) -> None:
        with self.assertRaisesRegex(CapabilityRecordError, "local node identity"):
            self.validate(self.record, local_node_id="node.other-01")

        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory:
            identity = load_or_create_identity(
                f"{directory}/identity.json",
                node_id_factory=lambda: "node.local-01",
            )
            self.assertEqual(identity.node_id, self.record["node_id"])
            self.assertIs(
                self.validate(self.record, local_node_id=identity.node_id),
                self.record,
            )

    def test_rejects_unknown_type_malformed_receipt_and_unsafe_reference(self) -> None:
        cases = (
            (
                "type",
                lambda record: record["metadata"].update({"type": "remote"}),
                "not allowed",
            ),
            (
                "receipt",
                lambda record: record["validation"].update(receipt_ids=["bad receipt"]),
                "receipt_ids",
            ),
            (
                "reference",
                lambda record: record.update(manifest_refs=["../secrets.json"]),
                "safe local",
            ),
        )
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_nonportable_or_nonlocal_references(self) -> None:
        for reference in (
            "file:/tmp/manifest.json",
            "urn:aethermesh:manifest",
            "C:\\secrets\\manifest.json",
            "manifests\\..\\secrets.json",
        ):
            with self.subTest(reference=reference):
                record = copy.deepcopy(self.record)
                record["manifest_refs"] = [reference]
                with self.assertRaisesRegex(CapabilityRecordError, "safe local"):
                    self.validate(record)

    def test_rejects_dishonest_validation_combinations(self) -> None:
        cases = (
            ({"status": "passed", "receipt_ids": []}, "requires a receipt"),
            ({"status": "failed", "receipt_ids": []}, "last_validated_at"),
            (
                {"status": "unvalidated", "receipt_ids": ["receipt.echo-01"]},
                "must not claim",
            ),
            ({"status": "trusted", "receipt_ids": []}, "not allowed"),
            (
                {
                    "status": "passed",
                    "receipt_ids": ["receipt.echo-01"],
                    "last_validated_at": "2026-07-11T12:05:00Z",
                    "check_name": "echo-smoke-test",
                    "failure_reason": "contradictory failure",
                },
                "must not include failure_reason",
            ),
            (
                {
                    "status": "unvalidated",
                    "receipt_ids": [],
                    "check_name": "unperformed-check",
                },
                "must not include check_name",
            ),
        )
        for validation, expected in cases:
            with self.subTest(validation=validation):
                record = copy.deepcopy(self.record)
                record["validation"] = validation
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_invalid_stable_and_attribution_fields(self) -> None:
        cases = (
            (
                lambda record: record.update(capability_version="1.0"),
                "semantic version",
            ),
            (
                lambda record: record.update(capability_version="1.0.0-01"),
                "semantic version",
            ),
            (
                lambda record: record["validation"]["receipt_evidence"][0].update(
                    capability_version="2.0.0"
                ),
                "capability name, version",
            ),
            (
                lambda record: record["validation"]["receipt_evidence"][0].update(
                    manifest_ref="manifests/other.json"
                ),
                "manifest reference",
            ),
            (lambda record: record.update(schema_version=True), "schema_version"),
            (lambda record: record.update(capability_id="Bad"), "capability_id"),
            (lambda record: record.update(created_at="2026-07-11"), "created_at"),
            (
                lambda record: record.update(created_at="2026-99-11T12:00:00Z"),
                "created_at",
            ),
            (
                lambda record: record["contribution_attribution"].update(
                    creator_node_id="node.other-01"
                ),
                "must match",
            ),
            (
                lambda record: record["contribution_attribution"].update(
                    maintainer_node_id="bad maintainer"
                ),
                "maintainer_node_id",
            ),
            (
                lambda record: record["contribution_attribution"].update(
                    work_receipt_ids=["bad receipt"]
                ),
                "work_receipt_ids",
            ),
            (
                lambda record: record["lineage"].update(prior_capability_id="Bad"),
                "prior_capability_id",
            ),
            (
                lambda record: record["lineage"].update(
                    local_build_artifact_ref="https://bad"
                ),
                "safe local",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_unsupported_schema_fields(self) -> None:
        cases = (
            (lambda record: record.update(network_trusted=True), "capability record"),
            (lambda record: record["metadata"].update(peer_count=3), "metadata"),
            (
                lambda record: record["validation"].update(network_verified=True),
                "validation",
            ),
            (
                lambda record: record["validation"]["receipt_evidence"][0].update(
                    network_verified=True
                ),
                "documented receipt fields",
            ),
            (lambda record: record["lineage"].update(remote_parent="peer"), "lineage"),
            (
                lambda record: record["contribution_attribution"].update(credits=10),
                "contribution_attribution",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_invalid_document_shapes_and_metadata(self) -> None:
        with self.assertRaisesRegex(CapabilityRecordError, "must be an object"):
            self.validate([])
        cases = (
            (lambda record: record.update(metadata=[]), "metadata must be an object"),
            (lambda record: record["metadata"].update(name=""), "name"),
            (lambda record: record["metadata"].pop("name"), "name"),
            (lambda record: record["metadata"].pop("type"), "type"),
            (
                lambda record: record["metadata"].update(supported_input_formats=[]),
                "supported_input_formats",
            ),
            (
                lambda record: record["metadata"].update(
                    supported_output_formats=[None]
                ),
                "supported_output_formats",
            ),
            (lambda record: record["metadata"].update(constraints=[]), "constraints"),
            (
                lambda record: record["metadata"].update(
                    local_execution_requirements=[]
                ),
                "local_execution_requirements",
            ),
            (
                lambda record: record["lineage"].update(
                    source_manifest_ref="/absolute"
                ),
                "safe local",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_missing_unknown_or_drifting_input_schemas(self) -> None:
        cases = (
            (
                lambda record: record["metadata"].pop("supported_input_schemas"),
                "supported_input_schemas",
            ),
            (
                lambda record: record["metadata"]["supported_input_schemas"][0].update(
                    schema_ref="examples/schemas/unknown.schema.json"
                ),
                "readable local schema",
            ),
            (
                lambda record: record["metadata"]["supported_input_schemas"][0].update(
                    schema_digest="sha256:" + "0" * 64
                ),
                "does not match local schema",
            ),
            (
                lambda record: record["metadata"]["supported_input_schemas"][0].update(
                    schema_version="1.0"
                ),
                "semantic version",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_receipt_with_different_input_schema_reference(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"]["receipt_evidence"][0]["input_schema"] = {
            "schema_ref": "examples/schemas/other.schema.json",
            "schema_version": "1.0.0",
            "schema_digest": "sha256:" + "0" * 64,
        }

        with self.assertRaisesRegex(CapabilityRecordError, "supported input schema"):
            self.validate(record)

    def test_rejects_missing_unknown_or_drifting_output_schemas(self) -> None:
        cases = (
            (
                lambda record: record["metadata"].pop("supported_output_schemas"),
                "supported_output_schemas",
            ),
            (
                lambda record: record["metadata"]["supported_output_schemas"][0].update(
                    schema_ref="examples/schemas/unknown.schema.json"
                ),
                "readable local schema",
            ),
            (
                lambda record: record["metadata"]["supported_output_schemas"][0].update(
                    schema_id="other-output"
                ),
                "schema ID",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.record)
                mutate(record)
                with self.assertRaisesRegex(CapabilityRecordError, expected):
                    self.validate(record)

    def test_rejects_receipt_with_different_output_schema_reference(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"]["receipt_evidence"][0]["output_schema"] = {
            "schema_ref": "examples/schemas/other.schema.json",
            "schema_id": "other-output",
            "schema_version": "1.0.0",
            "schema_digest": "sha256:" + "0" * 64,
        }

        with self.assertRaisesRegex(CapabilityRecordError, "supported output schema"):
            self.validate(record)


if __name__ == "__main__":
    unittest.main()
