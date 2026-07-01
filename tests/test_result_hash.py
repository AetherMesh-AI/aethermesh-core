import math
import unittest

from aethermesh_core.models import JobResult
from aethermesh_core.result_hash import result_hash, result_hash_from_fields


class ResultHashTests(unittest.TestCase):
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
