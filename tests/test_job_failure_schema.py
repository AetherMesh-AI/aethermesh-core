import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.job_failure_schema import (
    JobFailureSchemaError,
    validate_job_failure_document,
)


class JobFailureSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.examples = json.loads(
            (root / "examples/job-failures/phase-1-examples.json").read_text("utf-8")
        )

    def setUp(self) -> None:
        self.valid = copy.deepcopy(self.examples[0])

    def test_required_failure_examples_validate_and_preserve_links(self) -> None:
        self.assertEqual(
            [record["failure_type"] for record in self.examples],
            [
                "task_crash",
                "validation_failure",
                "timeout",
                "manifest_mismatch",
                "contribution_rejected",
            ],
        )
        for record in self.examples:
            with self.subTest(failure_type=record["failure_type"]):
                self.assertIs(validate_job_failure_document(record), record)
                self.assertTrue(record["references"]["job_manifest_hash"])
                self.assertTrue(record["references"]["input_manifest_hash"])
                self.assertTrue(record["references"]["attribution_record_ids"])
        self.assertTrue(self.examples[1]["references"]["validation_receipt_ids"])
        self.assertTrue(self.examples[1]["references"]["lineage_parent_ids"])

    def test_rejects_required_field_omissions(self) -> None:
        for field in (
            "job_id",
            "creator_node_id",
            "failure_type",
            "observed_at",
            "evidence",
        ):
            with self.subTest(field=field):
                record = copy.deepcopy(self.valid)
                record.pop(field)
                with self.assertRaisesRegex(JobFailureSchemaError, f"missing: {field}"):
                    validate_job_failure_document(record)

    def test_rejects_invalid_top_level_values_and_unknown_fields(self) -> None:
        cases = (
            ("schema_version", 2, "schema_version"),
            ("schema_version", True, "schema_version"),
            ("task_id", "bad id", "task_id"),
            ("observed_at", 1, "UTC timestamp"),
            ("observed_at", "yesterday", "UTC timestamp"),
            ("failure_type", "unknown", "unsupported"),
            ("failure_stage", "routing", "unsupported"),
            ("severity", "low", "unsupported"),
            ("retryable", 1, "boolean"),
            ("human_summary", "", "non-empty"),
            ("human_summary", "x" * 513, "up to 512"),
        )
        for field, value, message in cases:
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.valid)
                record[field] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(record)
        record = copy.deepcopy(self.valid)
        record["raw_log"] = "secret"
        with self.assertRaisesRegex(JobFailureSchemaError, "unsupported: raw_log"):
            validate_job_failure_document(record)
        with self.assertRaisesRegex(JobFailureSchemaError, "must be an object"):
            validate_job_failure_document([])

    def test_rejects_invalid_details(self) -> None:
        cases = (
            ("signal", "bad signal", "non-empty identifier"),
            ("exit_code", -1, "non-negative integer"),
            ("exit_code", True, "non-negative integer"),
            ("timeout_ms", "slow", "non-negative integer"),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                record = copy.deepcopy(self.valid)
                record["details"][field] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(record)
        record = copy.deepcopy(self.valid)
        record["details"]["stderr"] = "credential"
        with self.assertRaisesRegex(JobFailureSchemaError, "unsupported: stderr"):
            validate_job_failure_document(record)

    def test_rejects_invalid_references_and_attribution(self) -> None:
        mutations = (
            (("references", "job_manifest_hash"), "", "non-empty identifier"),
            (("references", "validation_receipt_ids"), "receipt", "must be a list"),
            (("references", "lineage_parent_ids"), ["bad id"], "non-empty identifier"),
            (
                ("attribution", "attempted_contributor_node_id"),
                "node.other",
                "must match executing_node_id",
            ),
            (("attribution", "claimed_work_unit"), "", "non-empty identifier"),
            (("attribution", "accepted_work_amount"), -1, "non-negative integer"),
            (("attribution", "accepted_work_amount"), True, "non-negative integer"),
            (("attribution", "rejection_reason"), "", "non-empty string"),
        )
        for path, value, message in mutations:
            with self.subTest(path=path):
                record = copy.deepcopy(self.valid)
                record[path[0]][path[1]] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(record)

    def test_evidence_requires_safe_reference_and_observation_time(self) -> None:
        record = copy.deepcopy(self.valid)
        for field in ("local_log_paths", "content_hashes", "validation_command_refs"):
            record["evidence"][field] = []
        with self.assertRaisesRegex(JobFailureSchemaError, "evidence reference"):
            validate_job_failure_document(record)

        cases = (
            ("local_log_paths", "log", "must be a list"),
            ("content_hashes", ["bad hash"], "non-empty identifier"),
            ("observed_timestamps", [], "non-empty list"),
            ("observed_timestamps", [1], "UTC timestamp"),
            (
                "observed_timestamps",
                ["2026-07-12T14:59:00.000Z"],
                "must include observed_at",
            ),
        )
        for field, value, message in cases:
            with self.subTest(field=field):
                record = copy.deepcopy(self.valid)
                record["evidence"][field] = value
                with self.assertRaisesRegex(JobFailureSchemaError, message):
                    validate_job_failure_document(record)


if __name__ == "__main__":
    unittest.main()
