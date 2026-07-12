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
        root = Path(__file__).resolve().parents[1] / "examples" / "job-failures"
        self.examples = [
            json.loads(path.read_text("utf-8")) for path in sorted(root.glob("*.json"))
        ]
        self.failure = self.examples[0]

    def test_crash_validation_timeout_manifest_and_rejection_examples_validate(
        self,
    ) -> None:
        self.assertEqual(len(self.examples), 5)
        for failure in self.examples:
            with self.subTest(failure_type=failure["failure_type"]):
                self.assertIs(validate_job_failure_document(failure), failure)
        self.assertEqual(
            {failure["failure_type"] for failure in self.examples},
            {
                "task_crash",
                "validation_failure",
                "timeout",
                "manifest_mismatch",
                "contribution_rejected",
            },
        )

    def test_required_identity_classification_timestamp_and_evidence_are_rejected(
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
                document = copy.deepcopy(self.failure)
                document.pop(field)
                with self.assertRaisesRegex(JobFailureSchemaError, f"missing: {field}"):
                    validate_job_failure_document(document)

        document = copy.deepcopy(self.failure)
        document["evidence"]["local_log_paths"] = []
        document["evidence"]["content_hashes"] = []
        document["evidence"]["validation_command_refs"] = []
        with self.assertRaisesRegex(
            JobFailureSchemaError, "include an evidence reference"
        ):
            validate_job_failure_document(document)

    def test_records_link_manifests_receipts_lineage_and_attribution(self) -> None:
        failure = validate_job_failure_document(self.failure)
        self.assertTrue(failure["links"]["job_manifest_hash"])
        self.assertTrue(failure["links"]["input_manifest_hash"])
        self.assertIn("validation_receipt_ids", failure["links"])
        self.assertTrue(failure["links"]["lineage_parent_ids"])
        self.assertEqual(
            failure["attribution"]["attempted_contributor_node_id"], "node.worker"
        )
        self.assertEqual(failure["attribution"]["accepted_work_amount"], 0)
        self.assertTrue(failure["attribution"]["rejection_reason"])

    def test_rejects_payloads_unsafe_paths_and_unexplained_rejection(self) -> None:
        document = copy.deepcopy(self.failure)
        document["evidence"]["log_contents"] = "credential=secret"
        with self.assertRaisesRegex(JobFailureSchemaError, "unsupported: log_contents"):
            validate_job_failure_document(document)

        document = copy.deepcopy(self.failure)
        document["evidence"]["local_log_paths"] = ["/private/job.log"]
        with self.assertRaisesRegex(JobFailureSchemaError, "repository-relative"):
            validate_job_failure_document(document)

        document = copy.deepcopy(self.failure)
        document["attribution"]["rejection_reason"] = None
        with self.assertRaisesRegex(JobFailureSchemaError, "include rejection_reason"):
            validate_job_failure_document(document)

    def test_rejects_invalid_detail_and_classification_values(self) -> None:
        cases = (
            (("retryable",), "yes", "retryable must be boolean"),
            (("severity",), "urgent", "severity is unsupported"),
            (("details", "timeout_ms"), -1, "non-negative integer"),
        )
        for path, value, message in cases:
            with self.subTest(path=path):
                document = copy.deepcopy(self.failure)
                target = document
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(document)


if __name__ == "__main__":
    unittest.main()
