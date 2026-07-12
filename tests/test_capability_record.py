import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.capability_record import (
    CapabilityRecordError,
    validate_capability_record,
)


EXAMPLE_PATH = Path(__file__).parents[1] / "examples" / "capability-record.json"


class CapabilityRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_complete_example_is_valid(self) -> None:
        validated = validate_capability_record(self.record)

        self.assertEqual(validated, self.record)
        self.assertIsNot(validated, self.record)

        derived_record = copy.deepcopy(self.record)
        derived_record["lineage"]["prior_capability_id"] = (
            "local-capability-text-embed-v0"
        )
        self.assertEqual(
            validate_capability_record(derived_record)["lineage"][
                "prior_capability_id"
            ],
            "local-capability-text-embed-v0",
        )

        root_record = copy.deepcopy(self.record)
        root_record["lineage"]["local_build_artifact_ref"] = None
        self.assertIsNone(
            validate_capability_record(root_record)["lineage"][
                "local_build_artifact_ref"
            ]
        )

    def test_missing_required_provenance_fields_fail(self) -> None:
        for field, message in (
            ("creator_node_id", "documented fields"),
            ("manifest_references", "documented fields"),
            ("validation", "documented fields"),
        ):
            record = copy.deepcopy(self.record)
            record.pop(field)
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(CapabilityRecordError, message),
            ):
                validate_capability_record(record)

    def test_unknown_capability_type_and_malformed_receipts_fail(self) -> None:
        record = copy.deepcopy(self.record)
        record["metadata"]["capability_type"] = "remote-expert"
        with self.assertRaisesRegex(CapabilityRecordError, "unknown value"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["validation"]["receipt_ids"] = ["receipt-123"]
        with self.assertRaisesRegex(CapabilityRecordError, "receipt ID"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["contribution_attribution"]["local_work_receipt_ids"] = [
            "local-validation-receipt-text-embed-v1"
        ]
        with self.assertRaisesRegex(CapabilityRecordError, "work receipt ID"):
            validate_capability_record(record)

    def test_unvalidated_state_cannot_present_as_trusted(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"] = {
            "status": "unvalidated",
            "receipt_ids": [],
            "last_validated_at": None,
            "check_name": None,
            "failure_reason": None,
        }
        self.assertEqual(
            validate_capability_record(record)["validation"]["status"], "unvalidated"
        )

        record["validation"]["check_name"] = "pretend-check"
        with self.assertRaisesRegex(CapabilityRecordError, "must not present"):
            validate_capability_record(record)

    def test_failed_status_requires_reason_and_passed_rejects_one(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"]["status"] = "failed"
        record["validation"]["failure_reason"] = None
        with self.assertRaisesRegex(CapabilityRecordError, "failure_reason"):
            validate_capability_record(record)

        record["validation"]["status"] = "passed"
        record["validation"]["failure_reason"] = "unexpected"
        with self.assertRaisesRegex(CapabilityRecordError, "only failed"):
            validate_capability_record(record)

    def test_stale_status_is_valid_with_historical_evidence(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"]["status"] = "stale"
        self.assertEqual(
            validate_capability_record(record)["validation"]["status"], "stale"
        )

    def test_rejects_bad_schema_identifiers_references_and_timestamps(self) -> None:
        cases = (
            ("schema_version", True, "integer 1"),
            ("capability_id", "capability-1", "invalid format"),
            ("creator_node_id", "", "non-empty"),
            ("created_at", "2026-07-11T00:00:00", "UTC timestamp"),
        )
        for field, value, message in cases:
            record = copy.deepcopy(self.record)
            record[field] = value
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(CapabilityRecordError, message),
            ):
                validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["manifest_references"]["node_manifest_ref"] = "../node.json"
        with self.assertRaisesRegex(CapabilityRecordError, "invalid format"):
            validate_capability_record(record)

    def test_rejects_nonlocal_execution_and_lost_attribution(self) -> None:
        record = copy.deepcopy(self.record)
        record["metadata"]["local_execution_requirements"]["execution_scope"] = (
            "peer-to-peer"
        )
        with self.assertRaisesRegex(CapabilityRecordError, "local-only"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["contribution_attribution"]["creator_node_id"] = "node-other"
        with self.assertRaisesRegex(CapabilityRecordError, "must match"):
            validate_capability_record(record)


if __name__ == "__main__":
    unittest.main()
