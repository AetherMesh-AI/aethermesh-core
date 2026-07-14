import copy
import json
import unittest
from pathlib import Path
from typing import Any

from aethermesh_core.contribution_record import (
    ContributionRecordError,
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
        self.assertEqual(self.minimal["job_id"], "local-echo-minimal-001")
        self.assertEqual(self.minimal["validation"]["status"], "unvalidated")
        self.assertEqual(self.minimal["lineage"]["parent_contribution_ids"], [])

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
        schema_text = json.dumps(schema).lower()
        self.assertNotIn("reward_amount", schema_text)
        self.assertNotIn("consensus_status", schema_text)

    def test_missing_required_record_identity_and_timestamp_fields_fail(self) -> None:
        for field in (
            "record_id",
            "job_id",
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
