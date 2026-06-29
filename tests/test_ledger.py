import unittest

from aethermesh_core.ledger import ContributionLedger
from aethermesh_core.models import JobResult


class ContributionLedgerTests(unittest.TestCase):
    def test_completed_result_adds_positive_contribution_units(self) -> None:
        ledger = ContributionLedger()
        result = JobResult(
            job_id="job-1",
            node_id="node-a",
            status="completed",
            output="hello mesh",
            error=None,
            contribution_units=3,
        )

        record = ledger.record(result)
        summary = ledger.summary_for_node("node-a")

        self.assertEqual(record.node_id, "node-a")
        self.assertEqual(record.job_id, "job-1")
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.contribution_units, 3)
        self.assertEqual(record.message, "hello mesh")
        self.assertEqual(summary.node_id, "node-a")
        self.assertEqual(summary.completed_job_count, 1)
        self.assertEqual(summary.failed_job_count, 0)
        self.assertEqual(summary.total_result_count, 1)
        self.assertEqual(summary.total_contribution_units, 3)

    def test_failed_result_is_recorded_without_contribution_units(self) -> None:
        ledger = ContributionLedger()
        result = JobResult(
            job_id="job-2",
            node_id="node-a",
            status="failed",
            output=None,
            error="Unsupported job type: nope",
            contribution_units=5,
        )

        record = ledger.record(result)
        summary = ledger.summary_for_node("node-a")

        self.assertEqual(record.status, "failed")
        self.assertEqual(record.contribution_units, 0)
        self.assertEqual(record.message, "Unsupported job type: nope")
        self.assertEqual(summary.completed_job_count, 0)
        self.assertEqual(summary.failed_job_count, 1)
        self.assertEqual(summary.total_result_count, 1)
        self.assertEqual(summary.total_contribution_units, 0)

    def test_multiple_results_for_one_node_aggregate_deterministically(self) -> None:
        ledger = ContributionLedger()
        ledger.record(
            JobResult(
                job_id="job-1",
                node_id="node-a",
                status="completed",
                output="one",
                error=None,
                contribution_units=1,
            )
        )
        ledger.record(
            JobResult(
                job_id="job-2",
                node_id="node-a",
                status="completed",
                output="two",
                error=None,
                contribution_units=2,
            )
        )
        ledger.record(
            JobResult(
                job_id="job-3",
                node_id="node-a",
                status="failed",
                output=None,
                error="boom",
                contribution_units=7,
            )
        )
        ledger.record(
            JobResult(
                job_id="job-other",
                node_id="node-b",
                status="completed",
                output="other",
                error=None,
                contribution_units=100,
            )
        )

        summary = ledger.summary_for_node("node-a")

        self.assertEqual(summary.completed_job_count, 2)
        self.assertEqual(summary.failed_job_count, 1)
        self.assertEqual(summary.total_result_count, 3)
        self.assertEqual(summary.total_contribution_units, 3)

    def test_negative_completed_units_are_clamped_to_zero(self) -> None:
        ledger = ContributionLedger()
        result = JobResult(
            job_id="job-negative",
            node_id="node-a",
            status="completed",
            output="invalid units",
            error=None,
            contribution_units=-2,
        )

        record = ledger.record(result)
        summary = ledger.summary_for_node("node-a")

        self.assertEqual(record.contribution_units, 0)
        self.assertEqual(summary.completed_job_count, 1)
        self.assertEqual(summary.total_result_count, 1)
        self.assertEqual(summary.total_contribution_units, 0)

    def test_non_integer_completed_units_raise_value_error(self) -> None:
        ledger = ContributionLedger()
        result = JobResult(
            job_id="job-invalid",
            node_id="node-a",
            status="completed",
            output="invalid units",
            error=None,
            contribution_units="1",  # type: ignore[arg-type]
        )

        with self.assertRaisesRegex(ValueError, "contribution_units must be an integer"):
            ledger.record(result)


if __name__ == "__main__":
    unittest.main()
