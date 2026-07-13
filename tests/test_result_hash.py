import json
import math
import unittest
from copy import deepcopy
from pathlib import Path

from aethermesh_core.models import JobResult
from aethermesh_core.result_hash import (
    RESULT_HASH_ALGORITHM,
    canonical_result_document_hash,
    result_hash,
    result_hash_from_fields,
    result_hash_manifest,
    validate_validation_receipt_result_hash,
)


class ResultHashTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.document = json.loads(
            (root / "examples/job-results/local-echo-success.json").read_text("utf-8")
        )

    def test_durable_result_hash_is_stable_and_ignores_runtime_formatting(self) -> None:
        first = canonical_result_document_hash(self.document)
        reformatted = json.loads(json.dumps(self.document, indent=4, sort_keys=False))
        reformatted["created_at"] = "2030-01-01T00:00:00.000Z"
        reformatted["started_at"] = "2030-01-01T00:00:01.000Z"
        reformatted["finished_at"] = "2030-01-01T00:00:01.125Z"

        self.assertEqual(first, canonical_result_document_hash(reformatted))
        self.assertEqual(
            result_hash_manifest(self.document),
            {"algorithm": RESULT_HASH_ALGORITHM, "result_hash": first},
        )

    def test_durable_result_hash_covers_result_provenance_and_attribution(self) -> None:
        original = canonical_result_document_hash(self.document)
        changes = (
            ("summary", "different result content"),
            ("capability", "work.text_stats"),
            ("manifest_id", "sha256:" + "d" * 64),
            ("creator_node_id", "node.another-creator"),
            ("lineage.parent_task_ids", ["local-parent-task"]),
            ("contribution.local_operator_id", "operator.another"),
        )
        for field, value in changes:
            with self.subTest(field=field):
                changed = deepcopy(self.document)
                target = changed
                *parents, leaf = field.split(".")
                for parent in parents:
                    target = target[parent]
                target[leaf] = value
                if field == "manifest_id":
                    changed["references"]["manifest_hash"] = value
                if field == "creator_node_id":
                    changed["contribution"]["creator_node_id"] = value
                self.assertNotEqual(original, canonical_result_document_hash(changed))

    def test_durable_result_hash_excludes_machine_local_reference_paths(self) -> None:
        original = canonical_result_document_hash(self.document)
        relocated = deepcopy(self.document)
        relocated["references"]["artifact_refs"][0] = "other/artifact.json"
        relocated["references"]["log_refs"][0] = "other/result.log"
        self.assertEqual(original, canonical_result_document_hash(relocated))

        changed_content = deepcopy(self.document)
        changed_content["references"]["artifact_refs"][1] = "sha256:" + "d" * 64
        self.assertNotEqual(original, canonical_result_document_hash(changed_content))

    def test_durable_failed_and_error_results_are_hashable_after_validation(
        self,
    ) -> None:
        failed = deepcopy(self.document)
        failed["status"] = "failed"
        failed["exit_code"] = 1
        failed["error_summary"] = "local failure"
        failed["validation_status"] = "error"
        self.assertRegex(canonical_result_document_hash(failed), r"^[0-9a-f]{64}$")

        pending = deepcopy(self.document)
        pending["validation_status"] = "not_run"
        with self.assertRaisesRegex(ValueError, "requires a passed, failed, or error"):
            canonical_result_document_hash(pending)

    def test_validation_receipt_references_expected_durable_result_hash(self) -> None:
        digest = canonical_result_document_hash(self.document)
        validate_validation_receipt_result_hash({"result_hash": digest}, digest)
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_validation_receipt_result_hash({"result_hash": "f" * 64}, digest)

    def test_hash_is_stable_for_semantically_identical_dict_output(self) -> None:
        first = JobResult(
            job_id="job-1",
            node_id="node-a",
            status="completed",
            output={"b": [2, 1], "a": {"z": True, "x": None}},
            error=None,
            contribution_units=1,
        )
        second = JobResult(
            job_id="job-1",
            node_id="node-a",
            status="completed",
            output={"a": {"x": None, "z": True}, "b": [2, 1]},
            error=None,
            contribution_units=99,
        )

        digest = result_hash(first)

        self.assertEqual(digest, result_hash(second))
        self.assertEqual(
            digest,
            "449f669df0a283b995de4745d1b003af2df20f346b2b557adc70841e7fa54b45",
        )
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_hash_matches_canonical_failed_result_digest(self) -> None:
        self.assertEqual(
            result_hash_from_fields(
                job_id="job-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="boom",
            ),
            "6a8fb8fbe70509b2be2968e60d3426560070a92b35110d2ace184b58367c1380",
        )

    def test_hash_uses_only_result_identity_and_content_fields(self) -> None:
        completed = JobResult("job-1", "node-a", "completed", "hello", None, 1)
        failed = JobResult("job-1", "node-a", "failed", "hello", "boom", 1)

        self.assertEqual(
            result_hash(completed),
            result_hash_from_fields(
                job_id="job-1",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
            ),
        )
        self.assertEqual(
            result_hash(failed),
            result_hash_from_fields(
                job_id="job-1",
                node_id="node-a",
                status="failed",
                output="hello",
                error="boom",
            ),
        )
        self.assertNotEqual(result_hash(completed), result_hash(failed))

    def test_non_json_compatible_values_raise_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "JSON-compatible"):
            result_hash(
                JobResult(
                    "job-1",
                    "node-a",
                    "completed",
                    {"bad": {"not", "json"}},
                    None,
                    1,
                )
            )

        with self.assertRaises(ValueError) as cm:
            result_hash(JobResult("job-1", "node-a", "completed", math.nan, None, 1))
        self.assertEqual(
            str(cm.exception), "result hash fields must be JSON-compatible"
        )


if __name__ == "__main__":
    unittest.main()
