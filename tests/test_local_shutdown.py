import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from aethermesh_core.cli import main
from aethermesh_core.local_shutdown import LocalShutdownError, shutdown_local_node
from aethermesh_core.local_startup import start_local_node


class LocalShutdownTests(unittest.TestCase):
    def test_shutdown_persists_final_state_preserves_artifacts_and_is_idempotent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start = start_local_node(root).to_dict()
            identity_path = root / str(start["identity_path"])
            manifest_path = root / str(start["manifest_path"])
            identity_before = identity_path.read_text(encoding="utf-8")
            manifest_before = manifest_path.read_text(encoding="utf-8")
            receipt_before = sorted((root / "receipts").glob("*.json"))
            lineage_before = sorted((root / "lineage").glob("*.json"))
            contribution_dir = root / "contributions"
            contribution_dir.mkdir(exist_ok=True)
            (contribution_dir / "contribution-0001.json").write_text(
                json.dumps({"job_id": "job-1", "status": "completed"}),
                encoding="utf-8",
            )
            (root / "node.pid").write_text("12345", encoding="utf-8")
            (root / "runtime.lock").write_text("locked", encoding="utf-8")
            (root / "work" / "inputs").mkdir(parents=True, exist_ok=True)
            (root / "work" / "outputs").mkdir(parents=True, exist_ok=True)
            (root / "work" / "inputs" / "queued.json").write_text(
                "{}", encoding="utf-8"
            )
            (root / "work" / "inputs" / "done.json").write_text("{}", encoding="utf-8")
            (root / "work" / "outputs" / "done.json").write_text("{}", encoding="utf-8")

            first = shutdown_local_node(root).to_dict()
            second = shutdown_local_node(root).to_dict()
            identity_after = identity_path.read_text(encoding="utf-8")
            manifest_after = manifest_path.read_text(encoding="utf-8")
            state = json.loads((root / str(first["state_path"])).read_text())
            stopped_work = json.loads(
                (root / str(first["stopped_work_path"])).read_text()
            )
            log_lines = (root / str(first["log_path"])).read_text().splitlines()
            receipts_after = sorted((root / "receipts").glob("*.json"))
            lineage_after = sorted((root / "lineage").glob("*.json"))

        self.assertEqual(identity_after, identity_before)
        self.assertEqual(manifest_after, manifest_before)
        self.assertEqual(first["final_status"], "stopped")
        self.assertEqual(first["shutdown_outcome"], "clean")
        self.assertFalse(first["accepting_work"])
        self.assertFalse(first["repeated_request"])
        self.assertTrue(second["repeated_request"])
        self.assertEqual(first["validation_receipt_count"], len(receipt_before))
        self.assertEqual(first["lineage_record_count"], len(lineage_before))
        self.assertEqual(first["contribution_record_count"], 1)
        self.assertEqual(first["interrupted_work_count"], 1)
        self.assertEqual(second["validation_receipt_count"], len(receipt_before))
        self.assertEqual(second["lineage_record_count"], len(lineage_before))
        self.assertEqual(
            state["validation_receipt_refs"],
            [p.relative_to(root).as_posix() for p in receipt_before],
        )
        self.assertEqual(
            state["lineage_refs"],
            [p.relative_to(root).as_posix() for p in lineage_before],
        )
        self.assertEqual(
            state["contribution_refs"], ["contributions/contribution-0001.json"]
        )
        self.assertEqual(state["interrupted_work_count"], 1)
        self.assertEqual(stopped_work["status"], "stopped_retryable")
        self.assertEqual(
            stopped_work["work"],
            [{"work_ref": "work/inputs/queued.json", "status": "stopped_retryable"}],
        )
        self.assertFalse((root / "node.pid").exists())
        self.assertFalse((root / "runtime.lock").exists())
        self.assertIn("shutdown_start", log_lines[0])
        self.assertIn("shutdown_persistence_complete", "\n".join(log_lines))
        self.assertIn("shutdown_resources_released", "\n".join(log_lines))
        self.assertIn("shutdown_complete", log_lines[-1])
        self.assertEqual(receipts_after, receipt_before)
        self.assertEqual(lineage_after, lineage_before)

    def test_shutdown_marks_in_progress_work_retryable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start_local_node(root)
            (root / "work" / "in-progress").mkdir(parents=True)
            (root / "work" / "in-progress" / "active.json").write_text(
                "{}", encoding="utf-8"
            )

            result = shutdown_local_node(root).to_dict()
            stopped_work = json.loads(
                (root / str(result["stopped_work_path"])).read_text()
            )

        self.assertEqual(result["interrupted_work_count"], 1)
        self.assertEqual(
            stopped_work["work"],
            [
                {
                    "work_ref": "work/in-progress/active.json",
                    "status": "stopped_retryable",
                }
            ],
        )

    def test_shutdown_cli_exits_successfully_and_reports_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start_local_node(root)
            exit_code = main(["shutdown-local-node", "--runtime-dir", str(root)])
            state_path = root / "state" / "shutdown-state.json"
            state_exists = state_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertTrue(state_exists)

    def test_shutdown_fails_closed_for_missing_or_mismatched_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(LocalShutdownError, "runtime_stop"):
                shutdown_local_node(Path(temp_dir))

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start_local_node(root)
            manifest_path = root / "manifests" / "local-node-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["node"]["node_id"] = "different-node"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(LocalShutdownError, "manifest_flush"):
                shutdown_local_node(root)

    def test_shutdown_reports_worker_termination_failure_without_mutating_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start = start_local_node(root).to_dict()
            identity_path = root / str(start["identity_path"])
            manifest_path = root / str(start["manifest_path"])
            identity_before = identity_path.read_text(encoding="utf-8")
            manifest_before = manifest_path.read_text(encoding="utf-8")
            receipts_before = sorted((root / "receipts").glob("*.json"))
            with self.assertRaises(LocalShutdownError) as raised:
                shutdown_local_node(root, timeout_seconds=-1)
            timeout_report = raised.exception.to_dict()
            self.assertEqual(
                timeout_report["error_code"], "SHUTDOWN_RUNTIME_STOP_FAILED"
            )
            with (
                patch(
                    "aethermesh_core.local_shutdown.Path.unlink",
                    side_effect=OSError("busy"),
                ),
                self.assertRaises(LocalShutdownError) as raised,
            ):
                (root / "node.pid").write_text("123", encoding="utf-8")
                shutdown_local_node(root)
            report = raised.exception.to_dict()
            log = (root / "logs" / "shutdown.log").read_text(encoding="utf-8")
            identity_after = identity_path.read_text(encoding="utf-8")
            manifest_after = manifest_path.read_text(encoding="utf-8")
            receipts_after = sorted((root / "receipts").glob("*.json"))

        self.assertEqual(report["error_code"], "SHUTDOWN_WORKER_TERMINATION_FAILED")
        self.assertEqual(report["failing_component"], "worker_termination")
        self.assertEqual(report["node_id"], start["node_id"])
        self.assertEqual(report["affected_artifact"], "node.pid")
        self.assertEqual(report["shutdown_outcome"], "partial_shutdown")
        self.assertTrue(report["contribution_records_finalized"])
        self.assertIn("busy", log)
        self.assertEqual(identity_after, identity_before)
        self.assertEqual(manifest_after, manifest_before)
        self.assertEqual(receipts_after, receipts_before)

    def test_shutdown_reports_state_write_failure_and_preserves_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            start = start_local_node(root).to_dict()
            identity_path = root / str(start["identity_path"])
            identity_before = identity_path.read_text(encoding="utf-8")
            with (
                patch(
                    "aethermesh_core.local_shutdown.atomic_write_json",
                    side_effect=OSError("disk full"),
                ),
                self.assertRaises(LocalShutdownError) as raised,
            ):
                shutdown_local_node(root)
            report = raised.exception.to_dict()
            log = (root / "logs" / "shutdown.log").read_text(encoding="utf-8")
            identity_after = identity_path.read_text(encoding="utf-8")

        self.assertEqual(report["error_code"], "SHUTDOWN_MANIFEST_FLUSH_FAILED")
        self.assertEqual(report["affected_artifact"], "state/shutdown-state.json")
        self.assertEqual(report["node_id"], start["node_id"])
        self.assertTrue(report["contribution_records_finalized"])
        self.assertIn("disk full", log)
        self.assertEqual(identity_after, identity_before)

    def test_shutdown_cli_reports_errors_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stderr = StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["shutdown-local-node", "--runtime-dir", temp_dir])
            report = json.loads(stderr.getvalue())["error"]

        self.assertEqual(exit_code, 1)
        self.assertEqual(report["error_code"], "SHUTDOWN_RUNTIME_STOP_FAILED")
        self.assertEqual(report["shutdown_outcome"], "unsafe_incomplete")

    def test_shutdown_error_reporting_tolerates_unwritable_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with (
                patch(
                    "aethermesh_core.local_shutdown.append_json_line",
                    side_effect=OSError("log unavailable"),
                ),
                self.assertRaises(LocalShutdownError) as raised,
            ):
                shutdown_local_node(Path(temp_dir))

        self.assertEqual(
            raised.exception.to_dict()["error_code"], "SHUTDOWN_RUNTIME_STOP_FAILED"
        )
