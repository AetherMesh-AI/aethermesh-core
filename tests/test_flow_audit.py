import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.cli import run_local_flow
from aethermesh_core.flow_audit import FlowAuditError, audit_local_flow


class FlowAuditTests(unittest.TestCase):
    def test_audit_local_flow_reports_deterministic_artifact_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))

            report = audit_local_flow(output_dir)

        self.assertEqual(
            report,
            {
                "ok": True,
                "output_dir": str(output_dir),
                "artifacts": {
                    "dispatch_message_log": str(
                        output_dir / "dispatch-message-log.json"
                    ),
                    "flow_message_log": str(output_dir / "flow-message-log.json"),
                    "ledger": str(output_dir / "ledger.json"),
                    "receipts": str(output_dir / "receipts.json"),
                },
                "counts": {
                    "dispatch_messages": 4,
                    "flow_messages": 8,
                    "receipts": 2,
                    "ledger_records": 2,
                    "total_contribution_units": 2,
                    "credited_receipt_units": 2,
                },
            },
        )

    def test_missing_receipts_returns_audit_error_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            receipts_path = output_dir / "receipts.json"
            receipts_path.unlink()
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "receipt file does not exist"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_mismatched_receipt_units_returns_audit_error_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            receipts_path = output_dir / "receipts.json"
            receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
            receipts["receipts"][0]["credited_units"] = 99
            receipts_path.write_text(
                json.dumps(receipts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(
                FlowAuditError, "contribution.contribution_units mismatch"
            ):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_tampered_receipt_validation_reason_returns_audit_error_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            receipts_path = output_dir / "receipts.json"
            receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
            receipts["receipts"][0]["validation"]["reason"] = "tampered reason"
            receipts_path.write_text(
                json.dumps(receipts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(
                FlowAuditError, "contribution.validation mismatch"
            ):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_tampered_receipt_output_summary_returns_audit_error_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            receipts_path = output_dir / "receipts.json"
            receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
            receipts["receipts"][0]["output_summary"] = {"tampered": True}
            receipts_path.write_text(
                json.dumps(receipts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(
                FlowAuditError, "result.output_summary mismatch"
            ):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_tampered_ledger_record_returns_audit_error_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            ledger_path = output_dir / "ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["records"][0]["validation_reason"] = "tampered reason"
            ledger_path.write_text(
                json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(
                FlowAuditError, "contribution claims do not match ledger records"
            ):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)


def _write_manifest(directory: Path) -> Path:
    manifest_path = directory / "local-batch.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": 1,
                "nodes": ["local-node-a", "local-node-b"],
                "jobs": [
                    {
                        "job_id": "echo-1",
                        "job_type": "echo",
                        "payload": {"message": "hello mesh"},
                    },
                    {
                        "job_id": "text-stats-1",
                        "job_type": "text_stats",
                        "payload": {"text": "hello mesh\nhello node"},
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


def _artifact_contents(output_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(output_dir).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(output_dir.rglob("*.json"))
    }


if __name__ == "__main__":
    unittest.main()
