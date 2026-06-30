import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast

from aethermesh_core.ledger import (
    ContributionLedger,
    ContributionRecord,
    LedgerPersistenceError,
    load_existing_ledger_document,
    load_ledger_document,
    save_ledger_document,
)
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
        self.assertIsNone(record.validation_valid)
        self.assertIsNone(record.validation_reason)
        self.assertIsNone(record.job_type)
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
            contribution_units=cast(Any, "1"),
        )

        with self.assertRaisesRegex(
            ValueError, "contribution_units must be an integer"
        ):
            ledger.record(result)

    def test_contribution_record_round_trips_through_json_dict(self) -> None:
        record = ContributionRecord(
            node_id="node-a",
            job_id="job-1",
            status="completed",
            contribution_units=1,
            message="hello mesh",
            validation_valid=True,
            validation_reason="ok",
            job_type="echo",
        )

        decoded = ContributionRecord.from_dict(json.loads(json.dumps(record.to_dict())))

        self.assertEqual(decoded, record)

    def test_legacy_contribution_record_without_validation_metadata_loads(self) -> None:
        payload = {
            "node_id": "node-a",
            "job_id": "job-legacy",
            "status": "completed",
            "contribution_units": 1,
            "message": "legacy ok",
        }

        record = ContributionRecord.from_dict(payload)

        self.assertEqual(record.node_id, "node-a")
        self.assertEqual(record.job_id, "job-legacy")
        self.assertEqual(record.status, "completed")
        self.assertEqual(record.contribution_units, 1)
        self.assertEqual(record.message, "legacy ok")
        self.assertIsNone(record.validation_valid)
        self.assertIsNone(record.validation_reason)
        self.assertIsNone(record.job_type)

    def test_record_persists_validation_metadata_when_supplied(self) -> None:
        ledger = ContributionLedger()

        ledger.record(
            JobResult(
                job_id="job-invalid",
                node_id="node-a",
                status="completed",
                output="unexpected",
                error=None,
                contribution_units=0,
            ),
            validation_valid=False,
            validation_reason="output_mismatch",
            job_type="echo",
        )

        self.assertEqual(
            ledger.to_document()["records"][0],
            {
                "node_id": "node-a",
                "job_id": "job-invalid",
                "status": "completed",
                "contribution_units": 0,
                "message": "unexpected",
                "validation_valid": False,
                "validation_reason": "output_mismatch",
                "job_type": "echo",
            },
        )

    def test_missing_json_ledger_loads_as_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"

            ledger, extra_fields = load_ledger_document(ledger_path)

        self.assertEqual(extra_fields, {})
        self.assertEqual(ledger.summary_for_node("node-a").total_result_count, 0)

    def test_json_ledger_appends_and_persists_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger = ContributionLedger()
            ledger.record(
                JobResult(
                    job_id="job-1",
                    node_id="node-a",
                    status="completed",
                    output="hello mesh",
                    error=None,
                    contribution_units=1,
                )
            )
            save_ledger_document(ledger_path, ledger, {"future_field": {"kept": True}})

            loaded, extra_fields = load_ledger_document(ledger_path)
            loaded.record(
                JobResult(
                    job_id="job-2",
                    node_id="node-a",
                    status="failed",
                    output=None,
                    error="boom",
                    contribution_units=5,
                )
            )
            save_ledger_document(ledger_path, loaded, extra_fields)
            reloaded, reloaded_extras = load_ledger_document(ledger_path)

        summary = reloaded.summary_for_node("node-a")
        self.assertEqual(reloaded_extras, {"future_field": {"kept": True}})
        self.assertEqual(summary.total_result_count, 2)
        self.assertEqual(summary.failed_job_count, 1)
        self.assertEqual(summary.total_contribution_units, 1)

    def test_malformed_json_ledger_raises_clear_error_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text("{not json", encoding="utf-8")

            with self.assertRaisesRegex(LedgerPersistenceError, "malformed"):
                load_ledger_document(ledger_path)

            self.assertEqual(ledger_path.read_text(encoding="utf-8"), "{not json")

    def test_existing_ledger_loader_rejects_missing_file_without_creating_it(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"

            with self.assertRaisesRegex(LedgerPersistenceError, "does not exist"):
                load_existing_ledger_document(ledger_path)

            self.assertFalse(ledger_path.exists())

    def test_summary_document_sorts_nodes_and_uses_ledger_semantics(self) -> None:
        ledger = ContributionLedger(
            [
                ContributionRecord("node-b", "job-1", "completed", 10, "ok"),
                ContributionRecord("node-a", "job-2", "failed", 0, "boom"),
                ContributionRecord("node-a", "job-3", "completed", 5, "ok"),
            ]
        )

        summary = ledger.summary_document("./local-ledger.json")

        self.assertEqual(
            summary,
            {
                "ledger_path": "./local-ledger.json",
                "record_count": 3,
                "completed_result_count": 2,
                "failed_result_count": 1,
                "total_contribution_units": 15,
                "nodes": [
                    {
                        "node_id": "node-a",
                        "record_count": 2,
                        "completed_result_count": 1,
                        "failed_result_count": 1,
                        "total_contribution_units": 5,
                    },
                    {
                        "node_id": "node-b",
                        "record_count": 1,
                        "completed_result_count": 1,
                        "failed_result_count": 0,
                        "total_contribution_units": 10,
                    },
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
