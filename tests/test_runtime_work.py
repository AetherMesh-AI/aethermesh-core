import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from aethermesh_core.cli import main
from aethermesh_core.runtime_work import run_local_batch


class RuntimeWorkTests(unittest.TestCase):
    def test_run_local_batch_runtime_returns_structured_result_and_artifacts(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "local-batch.json"
            ledger_path = root / "ledger.json"
            message_log_path = root / "messages.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["runtime-node-a"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello runtime"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                payload = run_local_batch(
                    str(manifest_path), str(ledger_path), str(message_log_path)
                )

            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(payload["nodes"], ["runtime-node-a"])
            self.assertEqual(payload["results"][0]["output"], "hello runtime")
            self.assertEqual(
                payload["validation_summary"],
                {"valid": 1, "invalid": 0, "unsupported": 0},
            )
            self.assertEqual(payload["ledger_path"], str(ledger_path))
            self.assertEqual(payload["message_log_path"], str(message_log_path))
            persisted_summaries = cast(
                list[dict[str, Any]], payload["persisted_ledger_summaries"]
            )
            self.assertEqual(
                persisted_summaries[0]["node_id"],
                "runtime-node-a",
            )
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            self.assertEqual(ledger["records"][0]["node_id"], "runtime-node-a")
            self.assertEqual(ledger["records"][0]["job_type"], "echo")
            self.assertTrue(ledger["records"][0]["validation_valid"])
            message_log = json.loads(message_log_path.read_text(encoding="utf-8"))
            self.assertEqual(
                message_log["metadata"]["manifest_path"], str(manifest_path)
            )
            messages = cast(list[dict[str, Any]], message_log["messages"])
            job_messages = [
                message
                for message in messages
                if message["message_type"] == "job_result_reported"
            ]
            self.assertEqual(job_messages[0]["payload"]["job_id"], "echo-1")

    def test_run_local_batch_cli_delegates_to_runtime_result(self) -> None:
        runtime_payload = {
            "nodes": ["runtime-node-a"],
            "results": [],
            "validation_summary": {"valid": 0, "invalid": 0, "unsupported": 0},
        }
        stdout = io.StringIO()

        with (
            patch(
                "aethermesh_core.cli.run_local_batch", return_value=runtime_payload
            ) as runtime,
            contextlib.redirect_stdout(stdout),
        ):
            exit_code = main(["run-local-batch", "--manifest", "manifest.json"])

        self.assertEqual(exit_code, 0)
        runtime.assert_called_once_with("manifest.json", None, None)
        self.assertEqual(json.loads(stdout.getvalue()), runtime_payload)


if __name__ == "__main__":
    unittest.main()
