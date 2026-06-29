import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_message_log_document,
    write_message_log,
)
from aethermesh_core.models import Job
from aethermesh_core.simulation import run_local_simulation


class MessageLogTests(unittest.TestCase):
    def test_build_message_log_document_is_deterministic_and_ordered(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello mesh"}),
            Job(
                job_id="text-stats-1",
                job_type="text_stats",
                payload={"text": "hello mesh\nhello node"},
            ),
        ]
        first_simulation = run_local_simulation(
            node_ids=["local-node-a", "local-node-b"], jobs=jobs
        )
        second_simulation = run_local_simulation(
            node_ids=["local-node-a", "local-node-b"], jobs=jobs
        )

        first_document = build_message_log_document(
            simulation=first_simulation,
            jobs=jobs,
            manifest_path="examples/local-batch.json",
        )
        second_document = build_message_log_document(
            simulation=second_simulation,
            jobs=jobs,
            manifest_path="examples/local-batch.json",
        )

        self.assertEqual(first_document, second_document)
        self.assertEqual(first_document["version"], 1)
        self.assertEqual(first_document["metadata"]["source"], "run-local-batch")
        self.assertEqual(first_document["metadata"]["message_count"], 8)
        self.assertEqual(first_document["metadata"]["node_count"], 2)
        self.assertEqual(first_document["metadata"]["job_count"], 2)
        self.assertEqual(first_document["metadata"]["completed_count"], 2)
        self.assertEqual(first_document["metadata"]["failed_count"], 0)
        self.assertEqual(first_document["metadata"]["total_contribution_units"], 2)
        self.assertEqual(first_document["metadata"]["job_ids"], ["echo-1", "text-stats-1"])
        self.assertEqual(
            [message["message_id"] for message in first_document["messages"]],
            [f"msg-{index:04d}" for index in range(1, 9)],
        )
        self.assertEqual(first_document["messages"][0]["message_type"], "node_heartbeat")
        self.assertEqual(first_document["messages"][2]["message_type"], "job_assigned")
        self.assertEqual(first_document["messages"][3]["message_type"], "job_result_reported")
        self.assertEqual(first_document["messages"][4]["message_type"], "contribution_recorded")
        self.assertEqual(first_document["messages"][2]["correlation_id"], "echo-1")

        first_json = json.dumps(first_document, indent=2, sort_keys=True) + "\n"
        second_json = json.dumps(second_document, indent=2, sort_keys=True) + "\n"
        self.assertEqual(first_json, second_json)

    def test_write_message_log_uses_stable_json_and_creates_parents(self) -> None:
        document = {
            "version": 1,
            "metadata": {"message_count": 0},
            "messages": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "nested" / "messages.json"

            write_message_log(log_path, document)

            persisted = log_path.read_text(encoding="utf-8")

        self.assertEqual(persisted, json.dumps(document, indent=2, sort_keys=True) + "\n")

    def test_write_message_log_failure_preserves_existing_path(self) -> None:
        document = {
            "version": 1,
            "metadata": {"message_count": 0},
            "messages": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.mkdir()

            with self.assertRaises(MessageLogPersistenceError) as cm:
                write_message_log(log_path, document)

            self.assertTrue(log_path.is_dir())
            self.assertEqual(list(Path(temp_dir).glob(".messages.json.*.tmp")), [])

        self.assertIn("could not write message log file", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
