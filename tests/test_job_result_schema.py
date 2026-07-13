import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.job_result_schema import (
    JobResultSchemaError,
    validate_job_result_document,
)


class JobResultSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.success = json.loads(
            (root / "examples/job-results/local-echo-success.json").read_text("utf-8")
        )
        self.failed = json.loads(
            (root / "examples/job-results/local-echo-failed.json").read_text("utf-8")
        )

    def test_success_and_failed_examples_validate(self) -> None:
        self.assertIs(validate_job_result_document(self.success), self.success)
        self.assertIs(validate_job_result_document(self.failed), self.failed)

    def test_required_attribution_lineage_manifest_and_validation_fields_reject_omission(
        self,
    ) -> None:
        for field in (
            "creator_node_id",
            "executor_node_id",
            "manifest_id",
            "references",
            "error_summary",
            "validation_status",
            "validation_receipt_id",
            "validator_node_id",
            "lineage",
            "contribution",
        ):
            with self.subTest(field=field):
                document = copy.deepcopy(self.success)
                document.pop(field)
                with self.assertRaisesRegex(JobResultSchemaError, f"missing: {field}"):
                    validate_job_result_document(document)

    def test_invalid_status_and_missing_identifiers_are_rejected(self) -> None:
        invalid_status = copy.deepcopy(self.success)
        invalid_status["status"] = "complete"
        with self.assertRaisesRegex(JobResultSchemaError, "status is unsupported"):
            validate_job_result_document(invalid_status)

        for field in ("result_id", "job_id", "task_id"):
            with self.subTest(field=field):
                document = copy.deepcopy(self.success)
                document[field] = ""
                with self.assertRaisesRegex(
                    JobResultSchemaError, "non-empty identifier"
                ):
                    validate_job_result_document(document)

    def test_rejects_inconsistent_runtime_and_attribution_values(self) -> None:
        cases = (
            ("duration_ms", 124, "must match"),
            ("summary", "x" * 513, "up to 512"),
            ("validation_status", "pending", "is unsupported"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                document = copy.deepcopy(self.success)
                document[field] = value
                with self.assertRaisesRegex(JobResultSchemaError, message):
                    validate_job_result_document(document)

        document = copy.deepcopy(self.success)
        document["contribution"]["executor_node_id"] = "node.other"
        with self.assertRaisesRegex(
            JobResultSchemaError, "must match the top-level record"
        ):
            validate_job_result_document(document)

        document = copy.deepcopy(self.success)
        document["failure_reasons"].pop("missing_artifact")
        with self.assertRaisesRegex(JobResultSchemaError, "missing: missing_artifact"):
            validate_job_result_document(document)

        document = copy.deepcopy(self.success)
        document["future"] = True
        with self.assertRaisesRegex(JobResultSchemaError, "unsupported: future"):
            validate_job_result_document(document)

    def test_outcome_statuses_and_local_artifact_reference_rules(self) -> None:
        for status in (
            "succeeded",
            "failed",
            "timed_out",
            "cancelled",
            "validation_failed",
            "partially_completed",
        ):
            with self.subTest(status=status):
                document = copy.deepcopy(self.success)
                document["status"] = status
                document["error_summary"] = (
                    None if status == "succeeded" else "local outcome"
                )
                self.assertIs(validate_job_result_document(document), document)

        for reference in (
            "https://dashboard.example/result",
            "https:dashboard.example/result",
            "file:/Users/example/private.log",
            "C:/Users/example/private.log",
        ):
            with self.subTest(reference=reference):
                document = copy.deepcopy(self.success)
                document["references"]["artifact_refs"] = [reference]
                with self.assertRaisesRegex(
                    JobResultSchemaError, "relative local paths"
                ):
                    validate_job_result_document(document)

        document = copy.deepcopy(self.failed)
        document["error_summary"] = None
        with self.assertRaisesRegex(
            JobResultSchemaError, "required when the job did not succeed"
        ):
            validate_job_result_document(document)

        document = copy.deepcopy(self.success)
        document["error_summary"] = "contradictory failure detail"
        with self.assertRaisesRegex(
            JobResultSchemaError, "must be null when the job succeeded"
        ):
            validate_job_result_document(document)


if __name__ == "__main__":
    unittest.main()
