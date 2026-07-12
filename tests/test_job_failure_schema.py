import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.job_failure_schema import (
    JobFailureSchemaError,
    validate_job_failure_document,
)


class JobFailureSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.examples = {
            path.stem: json.loads(path.read_text("utf-8"))
            for path in (root / "examples/job-failures").glob("*.json")
        }
        self.crash = self.examples["task-crash"]

    def test_required_failure_examples_validate(self) -> None:
        self.assertEqual(
            set(self.examples),
            {
                "task-crash",
                "validation-failure",
                "timeout",
                "manifest-mismatch",
                "rejected-contribution",
            },
        )
        for name, example in self.examples.items():
            with self.subTest(name=name):
                self.assertIs(validate_job_failure_document(example), example)

    def test_required_identity_classification_timestamp_and_evidence_reject_omission(
        self,
    ) -> None:
        for field in (
            "job_id",
            "creator_node_id",
            "failure_type",
            "observed_at",
            "evidence",
        ):
            with self.subTest(field=field):
                document = copy.deepcopy(self.crash)
                document.pop(field)
                with self.assertRaisesRegex(JobFailureSchemaError, f"missing: {field}"):
                    validate_job_failure_document(document)

        document = copy.deepcopy(self.crash)
        document["evidence"]["log_refs"] = []
        with self.assertRaisesRegex(JobFailureSchemaError, "evidence reference"):
            validate_job_failure_document(document)

    def test_manifest_receipt_lineage_and_attribution_links_are_preserved(self) -> None:
        example = self.examples["validation-failure"]
        validated = validate_job_failure_document(example)
        self.assertTrue(validated["links"]["job_manifest_hash"].startswith("sha256:"))
        self.assertTrue(validated["links"]["input_manifest_hash"].startswith("sha256:"))
        self.assertEqual(
            validated["links"]["validation_receipt_ids"], ["receipt-validation-001"]
        )
        self.assertIn("lineage_parent_ids", validated["links"])
        self.assertEqual(
            validated["links"]["attribution_record_ids"], ["attribution-attempt-002"]
        )
        self.assertEqual(validated["attribution"]["accepted_work_amount"], 0)

    def test_rejects_vague_or_unsafe_structures_and_unattributed_rejection(
        self,
    ) -> None:
        cases = []
        no_details = copy.deepcopy(self.crash)
        no_details["details"] = dict.fromkeys(no_details["details"])
        cases.append((no_details, "machine-readable evidence"))

        absolute_log = copy.deepcopy(self.crash)
        absolute_log["evidence"]["log_refs"][0]["path"] = "/private/job.log"
        cases.append((absolute_log, "safe relative"))

        raw_log = copy.deepcopy(self.crash)
        raw_log["evidence"]["raw_log"] = "credential=secret"
        cases.append((raw_log, "unsupported: raw_log"))

        no_reason = copy.deepcopy(self.crash)
        no_reason["attribution"]["rejection_reason"] = None
        cases.append((no_reason, "required when no work is accepted"))

        for document, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(document)

    def test_rejects_invalid_scalar_values(self) -> None:
        cases = (
            ("schema_version", True, "must be integer 1"),
            ("failure_type", "unknown", "must be one of"),
            ("retryable", 1, "must be a boolean"),
            ("human_summary", "x" * 513, "up to 512"),
            ("observed_at", "2026-07-12", "UTC timestamp"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                document = copy.deepcopy(self.crash)
                document[field] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(document)


if __name__ == "__main__":
    unittest.main()
