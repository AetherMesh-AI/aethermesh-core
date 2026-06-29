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
                    "dispatch_message_log": str(output_dir / "dispatch-message-log.json"),
                    "flow_message_log": str(output_dir / "flow-message-log.json"),
                    "ledger": str(output_dir / "ledger.json"),
                    "receipts": str(output_dir / "receipts.json"),
                    "worker_message_logs": [
                        str(output_dir / "worker-message-logs" / "local-node-a.json"),
                        str(output_dir / "worker-message-logs" / "local-node-b.json"),
                    ],
                    "node_state_files": [
                        str(output_dir / "node-state" / "local-node-a.json"),
                        str(output_dir / "node-state" / "local-node-b.json"),
                    ],
                },
                "dispatch_message_count": 4,
                "flow_message_count": 8,
                "emitted_worker_message_count": 4,
                "receipt_count": 2,
                "ledger_record_count": 2,
                "processed_assignment_count": 2,
                "skipped_processed_assignment_count": 0,
                "total_contribution_units": 2,
                "credited_receipt_units": 2,
                "audited_node_ids": ["local-node-a", "local-node-b"],
                "processed_node_ids": ["local-node-a", "local-node-b"],
            },
        )

    def test_missing_receipts_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            receipts_path = output_dir / "receipts.json"
            receipts_path.unlink()
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "receipt file does not exist"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_missing_worker_message_log_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            worker_log_path = output_dir / "worker-message-logs" / "local-node-a.json"
            worker_log_path.unlink()
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "worker message log for node local-node-a does not exist"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_missing_node_state_file_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            state_path = output_dir / "node-state" / "local-node-a.json"
            state_path.unlink()
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "node-state file for node local-node-a does not exist"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_mismatched_flow_metadata_count_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            flow_log_path = output_dir / "flow-message-log.json"
            flow_log = json.loads(flow_log_path.read_text(encoding="utf-8"))
            flow_log["metadata"]["message_count"] = 999
            _write_json(flow_log_path, flow_log)
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "message_count.*mismatch"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_node_state_processed_ids_missing_receipt_assignment_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            state_path = output_dir / "node-state" / "local-node-a.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["processed_message_ids"].remove("msg-0003")
            state["processed_assignment_count"] = len(state["processed_message_ids"])
            _write_json(state_path, state)
            flow_log_path = output_dir / "flow-message-log.json"
            flow_log = json.loads(flow_log_path.read_text(encoding="utf-8"))
            flow_log["metadata"]["processed_assignment_count"] = 1
            _write_json(flow_log_path, flow_log)
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "does not include receipt assignment_message_id"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)

    def test_mismatched_receipt_units_returns_audit_error_without_mutating_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = _run_flow(Path(temp_dir))
            receipts_path = output_dir / "receipts.json"
            receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
            receipts["receipts"][0]["credited_units"] = 99
            _write_json(receipts_path, receipts)
            before = _artifact_contents(output_dir)

            with self.assertRaisesRegex(FlowAuditError, "credited units do not match"):
                audit_local_flow(output_dir)

            after = _artifact_contents(output_dir)

        self.assertEqual(after, before)


def _run_flow(directory: Path) -> Path:
    manifest_path = _write_manifest(directory)
    output_dir = directory / "flow"
    run_local_flow(str(manifest_path), str(output_dir))
    return output_dir


def _write_manifest(directory: Path) -> Path:
    manifest_path = directory / "local-batch.json"
    manifest_path.write_text(
        json.dumps(
            {
                "version": 1,
                "nodes": ["local-node-a", "local-node-b"],
                "jobs": [
                    {"job_id": "echo-1", "job_type": "echo", "payload": {"message": "hello mesh"}},
                    {"job_id": "text-stats-1", "job_type": "text_stats", "payload": {"text": "hello mesh\nhello node"}},
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


def _write_json(path: Path, document: dict[str, object]) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
