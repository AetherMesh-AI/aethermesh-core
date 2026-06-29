import unittest

from aethermesh_core.models import Job, JobResult
from aethermesh_core.validation import validate_job_result


class ValidationTests(unittest.TestCase):
    def test_completed_echo_result_with_matching_output_is_valid(self) -> None:
        job = Job(job_id="echo-1", job_type="echo", payload={"message": "hello"})
        result = JobResult(
            job_id="echo-1",
            node_id="node-a",
            status="completed",
            output="hello",
            error=None,
            contribution_units=1,
        )

        validation = validate_job_result(job, result)

        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "ok")
        self.assertEqual(
            validation.to_dict(),
            {
                "job_id": "echo-1",
                "result_job_id": "echo-1",
                "valid": True,
                "reason": "ok",
            },
        )

    def test_mismatched_job_id_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
            JobResult(
                job_id="echo-other",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "job_id_mismatch")

    def test_unsupported_job_type_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="job-1", job_type="unsupported", payload={"message": "hello"}),
            JobResult(
                job_id="job-1",
                node_id="node-a",
                status="completed",
                output="hello",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "unsupported_job_type")

    def test_non_completed_result_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="failed",
                output=None,
                error="boom",
                contribution_units=0,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "result_not_completed")

    def test_missing_payload_message_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output="",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "missing_payload_message")

    def test_non_string_payload_message_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": 123}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output=123,
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "missing_payload_message")

    def test_incorrect_output_is_invalid(self) -> None:
        validation = validate_job_result(
            Job(job_id="echo-1", job_type="echo", payload={"message": "expected"}),
            JobResult(
                job_id="echo-1",
                node_id="node-a",
                status="completed",
                output="actual",
                error=None,
                contribution_units=1,
            ),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "output_mismatch")


if __name__ == "__main__":
    unittest.main()
