import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.job_result_schema import (
    JobResultSchemaError,
    validate_job_result_document,
)
from aethermesh_core.result_hash import canonical_result_document_hash


class JobResultSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.success = json.loads(
            (root / "examples/job-results/local-echo-success.json").read_text("utf-8")
        )
        self.failed = json.loads(
            (root / "examples/job-results/local-echo-failed.json").read_text("utf-8")
        )
        self.pending = json.loads(
            (
                root / "examples/job-results/local-echo-pending-validation.json"
            ).read_text("utf-8")
        )

    def test_success_and_failed_examples_validate(self) -> None:
        self.assertIs(validate_job_result_document(self.success), self.success)
        self.assertIs(validate_job_result_document(self.failed), self.failed)
        self.assertEqual(self.failed["validation_status"], "failed")

    def test_pending_validation_is_explicit_and_retains_provenance(self) -> None:
        self.assertIs(validate_job_result_document(self.pending), self.pending)
        self.assertEqual(self.pending["validation_status"], "pending")
        self.assertEqual(
            self.pending["validation_receipt_id"],
            "local-validation-receipt-echo-pending-001",
        )
        self.assertIn(
            self.pending["validation_receipt_id"],
            self.pending["references"]["validation_receipt_ids"],
        )
        self.assertIsNone(self.pending["result_hash"])
        self.assertEqual(self.pending["creator_node_id"], "node.local-creator")
        self.assertEqual(
            self.pending["manifest_id"], self.pending["references"]["manifest_hash"]
        )
        self.assertEqual(self.pending["lineage"]["parent_job_ids"], [])
        self.assertEqual(
            self.pending["contribution"]["creator_node_id"],
            self.pending["creator_node_id"],
        )

    def test_required_attribution_lineage_manifest_and_validation_fields_reject_omission(
        self,
    ) -> None:
        for field in (
            "creator_node_id",
            "capability",
            "executor_node_id",
            "manifest_id",
            "references",
            "error_summary",
            "validation_status",
            "validation_receipt_id",
            "validator_node_id",
            "lineage",
            "contribution",
            "result_hash",
            "reported_at",
        ):
            with self.subTest(field=field):
                document = copy.deepcopy(self.success)
                document.pop(field)
                with self.assertRaisesRegex(JobResultSchemaError, f"missing: {field}"):
                    validate_job_result_document(document)

    def test_missing_or_stale_result_hash_is_rejected(self) -> None:
        missing = copy.deepcopy(self.success)
        missing.pop("result_hash")
        with self.assertRaisesRegex(JobResultSchemaError, "missing: result_hash"):
            validate_job_result_document(missing)

        stale = copy.deepcopy(self.success)
        stale["summary"] = "mutated after hashing"
        with self.assertRaisesRegex(JobResultSchemaError, "does not match"):
            validate_job_result_document(stale)

    def test_invalid_status_and_missing_identifiers_are_rejected(self) -> None:
        old_version = copy.deepcopy(self.success)
        old_version["schema_version"] = 1
        with self.assertRaisesRegex(JobResultSchemaError, "must be integer 6"):
            validate_job_result_document(old_version)

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

    def test_output_payload_requires_one_safe_delivery_mode_for_success(self) -> None:
        missing = copy.deepcopy(self.success)
        missing.pop("output_payload")
        with self.assertRaisesRegex(JobResultSchemaError, "missing: output_payload"):
            validate_job_result_document(missing)

        absent = copy.deepcopy(self.success)
        absent["output_payload"] = {
            "inline_payload": None,
            "payload_ref": None,
            "payload_digest": None,
        }
        with self.assertRaisesRegex(
            JobResultSchemaError, "must include an output payload"
        ):
            validate_job_result_document(absent)

        referenced = copy.deepcopy(self.success)
        referenced["output_payload"] = {
            "inline_payload": None,
            "payload_ref": "data/job-output-payloads/local-echo-001.json",
            "payload_digest": "sha256:" + "e" * 64,
        }
        referenced["result_hash"] = canonical_result_document_hash(referenced)
        self.assertIs(validate_job_result_document(referenced), referenced)

        unsafe_reference = copy.deepcopy(referenced)
        unsafe_reference["output_payload"]["payload_ref"] = (
            "https://example.test/output"
        )
        with self.assertRaisesRegex(JobResultSchemaError, "relative local paths"):
            validate_job_result_document(unsafe_reference)

    def test_rejects_inconsistent_runtime_and_attribution_values(self) -> None:
        cases = (
            ("duration_ms", 124, "must match"),
            ("summary", "x" * 513, "up to 512"),
            ("validation_status", "unknown", "is unsupported"),
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
                document["result_hash"] = canonical_result_document_hash(document)
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

    def test_unvalidated_results_cannot_claim_a_durable_result_hash(self) -> None:
        document = copy.deepcopy(self.pending)
        document["result_hash"] = self.success["result_hash"]
        with self.assertRaisesRegex(JobResultSchemaError, "must be null"):
            validate_job_result_document(document)

        document = copy.deepcopy(self.success)
        document["result_hash"] = None
        with self.assertRaisesRegex(
            JobResultSchemaError, "required after final validation"
        ):
            validate_job_result_document(document)


if __name__ == "__main__":
    unittest.main()
