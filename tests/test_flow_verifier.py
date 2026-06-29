import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from aethermesh_core.cli import run_local_flow
from aethermesh_core.local_flow_verifier import verify_local_flow


class LocalFlowVerifierTests(unittest.TestCase):
    def test_verify_local_flow_accepts_run_local_flow_artifacts(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        manifest_path = repo_root / "examples" / "local-batch.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))

            payload = verify_local_flow(output_dir)

        self.assertEqual(payload["command"], "verify-local-flow")
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["output_dir"], str(output_dir))
        self.assertEqual(payload["dispatch_message_count"], 5)
        self.assertEqual(payload["emitted_worker_message_count"], 6)
        self.assertEqual(payload["flow_message_count"], 11)
        self.assertEqual(payload["receipt_count"], 3)
        self.assertEqual(payload["processed_assignment_count"], 3)
        self.assertEqual(payload["skipped_processed_assignment_count"], 0)
        self.assertEqual(payload["total_contribution_units"], 3)
        self.assertEqual(payload["verified_node_ids"], ["local-node-a", "local-node-c"])
        self.assertEqual(
            payload["worker_message_log_paths"],
            [
                str(output_dir / "worker-message-logs" / "local-node-a.json"),
                str(output_dir / "worker-message-logs" / "local-node-c.json"),
            ],
        )
        self.assertEqual(payload["errors"], [])

    def test_verify_local_flow_reports_missing_required_artifact(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        manifest_path = repo_root / "examples" / "local-batch.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            (output_dir / "receipts.json").unlink()

            payload = verify_local_flow(output_dir)

        errors = cast(list[str], payload["errors"])
        self.assertIsInstance(errors, list)
        self.assertFalse(payload["valid"])
        self.assertIn("missing required artifact: receipts.json", errors)

    def test_verify_local_flow_reports_ledger_total_mismatch(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        manifest_path = repo_root / "examples" / "local-batch.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            ledger_path = output_dir / "ledger.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            ledger["records"][0]["contribution_units"] = 99
            ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            payload = verify_local_flow(output_dir)

        errors = cast(list[str], payload["errors"])
        self.assertFalse(payload["valid"])
        self.assertIn(
            "ledger total contribution units 101 does not match credited receipt total 3",
            errors,
        )
        self.assertIn(
            "ledger total contribution units 101 does not match flow metadata total 3",
            errors,
        )

    def test_verify_local_flow_reports_flow_metadata_total_mismatch(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        manifest_path = repo_root / "examples" / "local-batch.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            flow_path = output_dir / "flow-message-log.json"
            flow_log = json.loads(flow_path.read_text(encoding="utf-8"))
            flow_log["metadata"]["message_count"] = 999
            flow_path.write_text(json.dumps(flow_log, indent=2, sort_keys=True) + "\n", encoding="utf-8")

            payload = verify_local_flow(output_dir)

        errors = cast(list[str], payload["errors"])
        self.assertFalse(payload["valid"])
        self.assertIn(
            "flow-message-log.json: metadata field 'message_count' is 999, expected 11",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
