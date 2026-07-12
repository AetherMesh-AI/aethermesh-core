import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.capability_record import (
    CapabilityRecordError,
    validate_capability_record,
)


EXAMPLE_PATH = Path(__file__).parents[1] / "examples" / "local-capability-record.json"


class CapabilityRecordTests(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    def test_complete_example_is_valid_and_copied(self) -> None:
        validated = validate_capability_record(self.record)
        self.assertEqual(validated, self.record)
        self.assertIsNot(validated, self.record)

    def test_missing_required_claim_fields_fail(self) -> None:
        for field in ("creator_node_id", "manifest_references", "validation"):
            record = copy.deepcopy(self.record)
            del record[field]
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(CapabilityRecordError, "missing or unknown"),
            ):
                validate_capability_record(record)

    def test_schema_version_and_timestamps_are_real_json_values(self) -> None:
        record = copy.deepcopy(self.record)
        record["schema_version"] = True
        with self.assertRaisesRegex(CapabilityRecordError, "must be integer 1"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["created_at"] = "2026-99-11T22:20:09Z"
        with self.assertRaisesRegex(CapabilityRecordError, "UTC timestamp"):
            validate_capability_record(record)

    def test_unknown_type_and_malformed_receipt_references_fail(self) -> None:
        record = copy.deepcopy(self.record)
        record["metadata"]["capability_type"] = "remote-gateway"
        with self.assertRaisesRegex(
            CapabilityRecordError, "capability_type is unknown"
        ):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["metadata"]["capability_type"] = []
        with self.assertRaisesRegex(
            CapabilityRecordError, "capability_type is unknown"
        ):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["validation"]["receipt_ids"] = ["https://not-local.example/receipt"]
        with self.assertRaisesRegex(CapabilityRecordError, "malformed receipt ID"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["contribution_attribution"]["local_work_receipt_ids"] = ["../bad"]
        with self.assertRaisesRegex(CapabilityRecordError, "malformed receipt ID"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["contribution_attribution"]["local_work_receipt_ids"] = [
            "work-receipt-local-echo-worker-v1"
        ]
        self.assertEqual(
            validate_capability_record(record)["contribution_attribution"][
                "local_work_receipt_ids"
            ],
            ["work-receipt-local-echo-worker-v1"],
        )

    def test_unvalidated_record_is_explicitly_not_trusted(self) -> None:
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

        record["validation"]["check_name"] = "unsupported-claim"
        with self.assertRaisesRegex(
            CapabilityRecordError, "must not claim validation evidence"
        ):
            validate_capability_record(record)

    def test_validation_status_evidence_rules_fail_dishonest_claims(self) -> None:
        record = copy.deepcopy(self.record)
        record["validation"]["receipt_ids"] = []
        with self.assertRaisesRegex(
            CapabilityRecordError, "passed validation requires"
        ):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["validation"]["status"] = "failed"
        record["validation"]["failure_reason"] = None
        with self.assertRaisesRegex(
            CapabilityRecordError, "failed validation requires"
        ):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["validation"]["status"] = "unknown"
        with self.assertRaisesRegex(
            CapabilityRecordError, "validation.status is unknown"
        ):
            validate_capability_record(record)

        record["validation"]["status"] = []
        with self.assertRaisesRegex(
            CapabilityRecordError, "validation.status is unknown"
        ):
            validate_capability_record(record)

    def test_lineage_and_attribution_allow_optional_values(self) -> None:
        record = copy.deepcopy(self.record)
        record["lineage"]["source_manifest_ref"] = None
        record["lineage"]["prior_capability_record_id"] = "previous-local-echo-worker"
        record["contribution_attribution"]["maintainer_node_id"] = None
        self.assertEqual(
            validate_capability_record(record)["lineage"]["prior_capability_record_id"],
            "previous-local-echo-worker",
        )

    def test_reference_lineage_and_attribution_are_strict(self) -> None:
        record = copy.deepcopy(self.record)
        record["manifest_references"]["remote"] = "data/remote.json"
        with self.assertRaisesRegex(CapabilityRecordError, "unknown kind"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["lineage"]["source_manifest_ref"] = "../not-local.json"
        with self.assertRaisesRegex(CapabilityRecordError, "safe relative"):
            validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["lineage"]["source_manifest_ref"] = "..\\not-local.json"
        with self.assertRaisesRegex(CapabilityRecordError, "safe relative"):
            validate_capability_record(record)

        for unsafe_reference in (
            "C:/private/manifest.json",
            "~/private/manifest.json",
            "data/manifest.json#fragment",
            " data/manifest.json",
        ):
            record = copy.deepcopy(self.record)
            record["lineage"]["source_manifest_ref"] = unsafe_reference
            with (
                self.subTest(reference=unsafe_reference),
                self.assertRaisesRegex(CapabilityRecordError, "safe relative"),
            ):
                validate_capability_record(record)

        record = copy.deepcopy(self.record)
        record["contribution_attribution"]["creator_node_id"] = "other-node"
        with self.assertRaisesRegex(CapabilityRecordError, "must match"):
            validate_capability_record(record)
