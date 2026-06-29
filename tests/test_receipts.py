import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aethermesh_core.ledger import ContributionLedger
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, JobResult
from aethermesh_core.node_service import ProcessedAssignment
from aethermesh_core.receipts import (
    build_receipt_document,
    load_receipt_document_if_exists,
    write_receipt_document,
)
from aethermesh_core.validation import validate_job_result


class ReceiptTests(unittest.TestCase):
    def test_build_receipt_document_uses_processed_assignment_audit_fields(self) -> None:
        assignment = _processed_assignment(
            message_id="msg-0003",
            correlation_id="echo-1",
            job=Job("echo-1", "echo", {"message": "hello mesh"}),
            result=JobResult("echo-1", "local-node-a", "completed", "hello mesh", None, 1),
            result_message_id="msg-0004",
            contribution_message_id="msg-0005",
        )

        document = build_receipt_document([assignment])

        self.assertEqual(document["version"], 1)
        self.assertEqual(document["run_source"], "run-local-flow")
        self.assertEqual(
            document["receipts"],
            [
                {
                    "job_id": "echo-1",
                    "job_type": "echo",
                    "node_id": "local-node-a",
                    "assignment_message_id": "msg-0003",
                    "correlation_id": "echo-1",
                    "result_message_id": "msg-0004",
                    "contribution_message_id": "msg-0005",
                    "result_status": "completed",
                    "validation": {"valid": True, "reason": "ok"},
                    "credited_units": 1,
                    "output_summary": {"value": "hello mesh"},
                }
            ],
        )

    def test_invalid_validation_receipt_keeps_zero_credit(self) -> None:
        job = Job("bad-1", "echo", {"message": "expected"})
        invalid_result = JobResult(
            "bad-1", "local-node-a", "completed", "actual", None, 1
        )
        assignment = _processed_assignment(
            message_id="msg-0003",
            correlation_id="bad-1",
            job=job,
            result=invalid_result,
            result_message_id="msg-0004",
            contribution_message_id="msg-0005",
        )

        receipt = build_receipt_document([assignment])["receipts"][0]

        self.assertEqual(receipt["validation"], {"valid": False, "reason": "output_mismatch"})
        self.assertEqual(receipt["credited_units"], 0)
        self.assertEqual(receipt["contribution_message_id"], "msg-0005")

    def test_receipts_sort_deterministically_and_keep_compact_dict_summary(self) -> None:
        first = _processed_assignment(
            message_id="msg-0007",
            correlation_id="text-stats-1",
            job=Job("text-stats-1", "text_stats", {"text": "hello mesh\nhello node"}),
            result=JobResult(
                "text-stats-1",
                "local-node-b",
                "completed",
                {"word_count": 4, "line_count": 2, "normalized_preview": "hello mesh hello node"},
                None,
                1,
            ),
            result_message_id="msg-0008",
            contribution_message_id="msg-0009",
        )
        second = _processed_assignment(
            message_id="msg-0003",
            correlation_id="echo-1",
            job=Job("echo-1", "echo", {"message": "hello mesh"}),
            result=JobResult("echo-1", "local-node-a", "completed", "hello mesh", None, 1),
            result_message_id="msg-0004",
            contribution_message_id="msg-0005",
        )

        document = build_receipt_document([first, second])

        self.assertEqual(
            [receipt["job_id"] for receipt in document["receipts"]],
            ["echo-1", "text-stats-1"],
        )
        self.assertEqual(
            document["receipts"][1]["output_summary"],
            {"line_count": 2, "normalized_preview": "hello mesh hello node", "word_count": 4},
        )

    def test_existing_receipts_are_merged_by_assignment_id_for_reruns(self) -> None:
        original = _processed_assignment(
            message_id="msg-0003",
            correlation_id="echo-1",
            job=Job("echo-1", "echo", {"message": "hello mesh"}),
            result=JobResult("echo-1", "local-node-a", "completed", "hello mesh", None, 1),
            result_message_id="msg-0004",
            contribution_message_id="msg-0005",
        )
        existing = build_receipt_document([original])

        merged = build_receipt_document([], existing_document=existing)

        self.assertEqual(merged, existing)

    def test_receipt_document_write_and_load_round_trip(self) -> None:
        document = build_receipt_document([])
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "receipts.json"

            write_receipt_document(path, document)
            loaded = load_receipt_document_if_exists(path)
            missing = load_receipt_document_if_exists(Path(temp_dir) / "missing.json")
            raw = path.read_text(encoding="utf-8")

        self.assertEqual(loaded, document)
        self.assertIsNone(missing)
        self.assertTrue(raw.endswith("\n"))
        self.assertEqual(json.loads(raw), document)


def _processed_assignment(
    *,
    message_id: str,
    correlation_id: str,
    job: Job,
    result: JobResult,
    result_message_id: str,
    contribution_message_id: str,
) -> ProcessedAssignment:
    validation = validate_job_result(job, result)
    accounted_result = result if validation.valid else replace(result, contribution_units=0)
    record = ContributionLedger().record(
        accounted_result,
        validation_valid=validation.valid,
        validation_reason=validation.reason,
        job_type=job.job_type,
    )
    return ProcessedAssignment(
        message_id=message_id,
        correlation_id=correlation_id,
        job=job,
        result=result,
        validation=validation,
        contribution_record=record,
        emitted_messages=[
            MeshMessage(
                message_id=result_message_id,
                message_type="job_result_reported",
                sender_node_id=result.node_id,
                recipient_node_id="local-ledger",
                payload={"job_id": result.job_id, "status": result.status},
                correlation_id=correlation_id,
            ),
            MeshMessage(
                message_id=contribution_message_id,
                message_type="contribution_recorded",
                sender_node_id="local-ledger",
                recipient_node_id=result.node_id,
                payload={"job_id": result.job_id, "contribution_units": record.contribution_units},
                correlation_id=correlation_id,
            ),
        ],
    )


if __name__ == "__main__":
    unittest.main()
