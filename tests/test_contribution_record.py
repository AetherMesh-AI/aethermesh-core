import copy
import json
import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from aethermesh_core.contribution_record import (
    ContributionRecordError,
    validate_local_contribution_record,
    validate_contribution_record,
)


class ContributionRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.minimal = self._load("minimal-local-echo.json")
        self.failed = self._load("failed-local-echo.json")

    def test_minimal_local_record_validates_against_the_versioned_contract(
        self,
    ) -> None:
        self.assertIs(validate_contribution_record(self.minimal), self.minimal)
        self.assertEqual(self.minimal["job_id"], "local-job-echo-001")
        self.assertEqual(
            self.minimal["validation_receipt_id"],
            "local-validation-receipt-local-job-echo-001",
        )
        self.assertEqual(self.minimal["validation"]["status"], "passed")
        self.assertEqual(self.minimal["lineage"]["parent_contribution_ids"], [])
        self.assertIs(
            validate_local_contribution_record(self.minimal, self.root), self.minimal
        )

    def test_linked_failed_record_retains_manifest_lineage_and_attribution(
        self,
    ) -> None:
        receipt = json.loads(
            (self.root / self.failed["validation"]["validation_receipt_ref"]).read_text(
                encoding="utf-8"
            )
        )
        self.assertIs(validate_contribution_record(self.failed), self.failed)
        self.assertEqual(self.failed["validation"]["status"], "failed")
        work_manifest = self._load_job_envelope("complete-local-echo.json")
        self.assertEqual(self.failed["job_id"], work_manifest["job_id"])
        self.assertEqual(self.failed["job_id"], receipt["job_id"])
        self.assertEqual(self.failed["validation_receipt_id"], receipt["receipt_id"])
        self.assertEqual(receipt["work_id"], receipt["job_id"])

        self.assertEqual(
            self.failed["validation"]["validation_receipt_ref"],
            "examples/validation-receipts/local-echo-fail.json",
        )
        self.assertEqual(
            self.failed["lineage"]["parent_contribution_ids"],
            ["contribution.echo-0001"],
        )
        self.assertEqual(
            self.failed["validation"]["validator_node_id"], receipt["validator_id"]
        )
        self.assertEqual(
            self.failed["validation"]["failure_reason"], receipt["rejection_reason"]
        )
        self.assertIn(receipt["result_hash"], self.failed["lineage"]["output_hashes"])
        self.assertEqual(
            self.failed["lineage"]["contributor_node_id"],
            self.failed["contributor_node_id"],
        )
        self.assertNotEqual(
            self.failed["creator_node_id"], self.failed["contributor_node_id"]
        )
        self.assertEqual(self.failed["attribution"]["author_id"], "node.local-worker")
        self.assertIs(
            validate_local_contribution_record(self.failed, self.root), self.failed
        )

    def test_local_receipt_reference_rejects_missing_or_synthetic_receipts(
        self,
    ) -> None:
        record = copy.deepcopy(self.failed)
        record["validation"]["validation_receipt_ref"] = (
            "examples/validation-receipts/missing.json"
        )
        record["manifest_links"]["validation_manifest_ref"] = (
            "examples/validation-receipts/missing.json"
        )
        with self.assertRaisesRegex(ContributionRecordError, "does not exist"):
            validate_local_contribution_record(record, self.root)

        record = copy.deepcopy(self.failed)
        record["validation_receipt_id"] = "local-validation-receipt-local-job-fake"
        with self.assertRaisesRegex(ContributionRecordError, "must match"):
            validate_contribution_record(record)

        with TemporaryDirectory() as directory:
            local_root = Path(directory)
            (local_root / "receipt.json").symlink_to(
                self.root / "examples/validation-receipts/local-echo-fail.json"
            )
            record = copy.deepcopy(self.failed)
            record["validation"]["validation_receipt_ref"] = "receipt.json"
            record["manifest_links"]["validation_manifest_ref"] = "receipt.json"
            with self.assertRaisesRegex(ContributionRecordError, "escapes local root"):
                validate_local_contribution_record(record, local_root)

    def test_local_receipt_evidence_must_match_validation_and_manifest(self) -> None:
        cases = (
            (
                lambda record: record["manifest_links"].update(
                    validation_manifest_ref="examples/validation-receipts/local-echo-fail.json"
                ),
                "validation manifest reference",
            ),
            (
                lambda record: record["validation"].update(
                    status="failed", failure_reason="synthetic failure"
                ),
                "status does not match",
            ),
            (
                lambda record: record["validation"].update(
                    validated_at="2026-07-13T12:00:02Z"
                ),
                "validated_at does not match",
            ),
            (
                lambda record: record["validation"].update(validated_at=None),
                "validated_at is required",
            ),
            (
                lambda record: record["manifest_links"].update(work_manifest_ref=None),
                "work_manifest_ref is required",
            ),
            (
                lambda record: record["manifest_links"].update(
                    work_manifest_ref="examples/job-envelopes/complete-local-echo.json"
                ),
                "work manifest job_id does not match",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.minimal)
                mutate(record)
                with self.assertRaisesRegex(ContributionRecordError, expected):
                    validate_local_contribution_record(record, self.root)

        with TemporaryDirectory() as directory:
            local_root = Path(directory)
            receipt_ref = self.minimal["validation"]["validation_receipt_ref"]
            manifest_ref = self.minimal["manifest_links"]["work_manifest_ref"]
            for reference in (receipt_ref, manifest_ref):
                assert isinstance(reference, str)
                target = local_root / reference
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((self.root / reference).read_bytes())
            assert isinstance(manifest_ref, str)
            manifest_path = local_root / manifest_ref
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["creator_node_id"] = "node.other-creator"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ContributionRecordError, "creator_node_id"):
                validate_local_contribution_record(self.minimal, local_root)

        record = copy.deepcopy(self.failed)
        record["validation"]["failure_reason"] = "synthetic failure"
        with self.assertRaisesRegex(ContributionRecordError, "rejection_reason"):
            validate_local_contribution_record(record, self.root)

    def test_unvalidated_shape_keeps_optional_validation_fields_nullable(self) -> None:
        record = copy.deepcopy(self.minimal)
        record["validation"] = {
            "status": "unvalidated",
            "validator_node_id": None,
            "validation_receipt_ref": None,
            "validated_at": None,
            "failure_reason": None,
        }
        self.assertIs(validate_contribution_record(record), record)
        with self.assertRaisesRegex(
            ContributionRecordError, "required for local evidence"
        ):
            validate_local_contribution_record(record, self.root)

    def test_plain_schema_declares_the_same_required_shape(self) -> None:
        schema = json.loads(
            (self.root / "examples/schemas/contribution-record.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(set(schema["required"]), set(self.minimal))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema_version"], {"const": 2})
        self.assertIn("failure_reason", schema["properties"]["validation"]["required"])
        self.assertIn(
            "parent_contribution_ids", schema["properties"]["lineage"]["required"]
        )
        self.assertIn(
            "contributor_node_id", schema["properties"]["lineage"]["required"]
        )
        self.assertIn("creation_mode", schema["properties"]["attribution"]["required"])
        receipt_id_schema = schema["properties"]["validation_receipt_id"]
        self.assertTrue(
            any(
                re.fullmatch(option["pattern"], self.minimal["validation_receipt_id"])
                for option in receipt_id_schema["anyOf"]
            )
        )
        sha_receipt_id = "local-validation-receipt-sha256:" + "a" * 64
        self.assertTrue(
            any(
                re.fullmatch(option["pattern"], sha_receipt_id)
                for option in receipt_id_schema["anyOf"]
            )
        )
        schema_text = json.dumps(schema).lower()
        self.assertNotIn("reward_amount", schema_text)
        self.assertNotIn("consensus_status", schema_text)

    def test_missing_required_record_identity_and_timestamp_fields_fail(self) -> None:
        for field in (
            "record_id",
            "job_id",
            "validation_receipt_id",
            "creator_node_id",
            "contributor_node_id",
            "created_at",
        ):
            with self.subTest(field=field):
                record = copy.deepcopy(self.minimal)
                record.pop(field)
                with self.assertRaisesRegex(
                    ContributionRecordError, f"missing: {field}"
                ):
                    validate_contribution_record(record)

    def test_version_one_record_is_not_silently_reinterpreted(self) -> None:
        record = copy.deepcopy(self.minimal)
        record["schema_version"] = 1
        with self.assertRaisesRegex(ContributionRecordError, "must be integer 2"):
            validate_contribution_record(record)

    def test_failed_validation_requires_reason_without_losing_other_evidence(
        self,
    ) -> None:
        record = copy.deepcopy(self.failed)
        record["validation"]["failure_reason"] = None
        with self.assertRaisesRegex(ContributionRecordError, "requires failure_reason"):
            validate_contribution_record(record)

        record = copy.deepcopy(self.minimal)
        record["validation"]["failure_reason"] = "not applicable"
        with self.assertRaisesRegex(ContributionRecordError, "only failed"):
            validate_contribution_record(record)

    def test_rejects_unknown_or_malformed_core_values(self) -> None:
        cases = (
            (lambda record: record.update(schema_version=True), "schema_version"),
            (lambda record: record.update(record_id="bad id"), "record_id"),
            (lambda record: record.update(job_id=""), "job_id"),
            (lambda record: record.update(job_id="not a local id"), "job_id"),
            (
                lambda record: record.update(created_at="2026-99-13T12:00:00Z"),
                "created_at",
            ),
            (lambda record: record.update(work_type=""), "work_type"),
            (
                lambda record: record.update(unreviewed_network_claim=True),
                "unsupported fields",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.minimal)
                mutate(record)
                with self.assertRaisesRegex(ContributionRecordError, expected):
                    validate_contribution_record(record)

    def test_rejects_missing_or_unsafe_source_and_manifest_references(self) -> None:
        record = copy.deepcopy(self.minimal)
        record["source"] = {"local_source_path": None, "artifact_ref": None}
        with self.assertRaisesRegex(ContributionRecordError, "requires"):
            validate_contribution_record(record)

        for section, field in (
            ("source", "local_source_path"),
            ("manifest_links", "work_manifest_ref"),
            ("validation", "validation_receipt_ref"),
        ):
            with self.subTest(section=section, field=field):
                record = copy.deepcopy(self.failed)
                record[section][field] = "/private/record.json"
                with self.assertRaisesRegex(ContributionRecordError, "safe local"):
                    validate_contribution_record(record)

    def test_rejects_invalid_validation_lineage_and_attribution_values(self) -> None:
        cases = (
            (
                lambda record: record["validation"].update(status="trusted"),
                "validation.status",
            ),
            (
                lambda record: record["validation"].update(validated_at="not-a-time"),
                "validated_at",
            ),
            (
                lambda record: record["lineage"].update(
                    parent_contribution_ids="parent"
                ),
                "parent_contribution_ids",
            ),
            (
                lambda record: record["lineage"].update(input_hashes=["sha256:bad"]),
                "input_hashes",
            ),
            (
                lambda record: record["lineage"].update(
                    contributor_node_id="node.other"
                ),
                "must match contributor_node_id",
            ),
            (
                lambda record: record["attribution"].update(author_kind="account"),
                "author_kind",
            ),
            (
                lambda record: record["attribution"].update(creation_mode="imported"),
                "creation_mode",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                record = copy.deepcopy(self.failed)
                mutate(record)
                with self.assertRaisesRegex(ContributionRecordError, expected):
                    validate_contribution_record(record)

    def test_rejects_non_object_sections_and_unknown_nested_fields(self) -> None:
        record = copy.deepcopy(self.minimal)
        record["source"] = []
        with self.assertRaisesRegex(
            ContributionRecordError, "source must be an object"
        ):
            validate_contribution_record(record)

        record = copy.deepcopy(self.minimal)
        record["attribution"]["reward_amount"] = 1
        with self.assertRaisesRegex(
            ContributionRecordError, "attribution contains unsupported"
        ):
            validate_contribution_record(record)

    def _load(self, name: str) -> dict[str, Any]:
        return json.loads(
            (self.root / "examples/contributions" / name).read_text(encoding="utf-8")
        )

    def _load_job_envelope(self, name: str) -> dict[str, Any]:
        return json.loads(
            (self.root / "examples/job-envelopes" / name).read_text(encoding="utf-8")
        )


if __name__ == "__main__":
    unittest.main()
