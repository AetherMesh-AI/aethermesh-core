import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.cli import main
from aethermesh_core.node_announcement import (
    NodeAnnouncementError,
    build_node_announcement_message_log_document,
    normalize_announcement_capabilities,
)
from aethermesh_core.scheduler import DEFAULT_LOCAL_CAPABILITIES


class NodeAnnouncementTests(unittest.TestCase):
    def test_builds_single_heartbeat_message_log_with_default_capabilities(self) -> None:
        document = build_node_announcement_message_log_document(
            node_id="local-node-a",
        )

        self.assertEqual(document["version"], 1)
        self.assertEqual(
            document["metadata"],
            {
                "source": "announce-local-node",
                "node_id": "local-node-a",
                "status": "available",
                "message_count": 1,
                "capabilities": sorted(DEFAULT_LOCAL_CAPABILITIES),
            },
        )
        self.assertEqual(len(document["messages"]), 1)
        self.assertEqual(
            document["messages"][0],
            {
                "message_id": "msg-0001",
                "message_type": "node_heartbeat",
                "sender_node_id": "local-node-a",
                "recipient_node_id": None,
                "correlation_id": None,
                "payload": {
                    "node_id": "local-node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "capabilities": sorted(DEFAULT_LOCAL_CAPABILITIES),
                },
            },
        )

    def test_normalizes_supplied_capabilities_as_sorted_unique_strings(self) -> None:
        self.assertEqual(
            normalize_announcement_capabilities(
                ["text_embed", "echo", "text_embed", "text_chunk"]
            ),
            ("echo", "text_chunk", "text_embed"),
        )

    def test_rejects_empty_capability_before_writing(self) -> None:
        with self.assertRaises(NodeAnnouncementError) as cm:
            build_node_announcement_message_log_document(
                node_id="local-node-a",
                capabilities=["echo", ""],
            )

        self.assertIn("capability[1] must be a non-empty string", str(cm.exception))

    def test_rejects_invalid_node_id(self) -> None:
        with self.assertRaises(NodeAnnouncementError) as cm:
            build_node_announcement_message_log_document(node_id="   ")

        self.assertIn("node_id must be a non-empty string", str(cm.exception))

    def test_rejects_invalid_status(self) -> None:
        with self.assertRaises(NodeAnnouncementError) as cm:
            build_node_announcement_message_log_document(
                node_id="local-node-a",
                status="busy",
            )

        self.assertIn("status must be one of: available, offline", str(cm.exception))

    def test_cli_writes_announcement_and_peer_summary_reads_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-heartbeats.json"
            announce_stdout = io.StringIO()

            with contextlib.redirect_stdout(announce_stdout):
                announce_exit = main(
                    [
                        "announce-local-node",
                        "--node-id",
                        "local-node-a",
                        "--capability",
                        "text_embed",
                        "--capability",
                        "text_chunk",
                        "--capability",
                        "text_embed",
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            announce_payload = json.loads(announce_stdout.getvalue())
            persisted = json.loads(message_log_path.read_text(encoding="utf-8"))
            summary_stdout = io.StringIO()

            with contextlib.redirect_stdout(summary_stdout):
                summary_exit = main(
                    ["peer-summary", "--message-log-path", str(message_log_path)]
                )
            summary_payload = json.loads(summary_stdout.getvalue())

        self.assertEqual(announce_exit, 0)
        self.assertEqual(announce_payload["command"], "announce-local-node")
        self.assertEqual(announce_payload["node_id"], "local-node-a")
        self.assertEqual(announce_payload["status"], "available")
        self.assertEqual(announce_payload["capabilities"], ["text_chunk", "text_embed"])
        self.assertEqual(announce_payload["message_count"], 1)
        self.assertEqual(announce_payload["message_log_path"], str(message_log_path))
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["metadata"]["source"], "announce-local-node")
        self.assertEqual(persisted["metadata"]["message_count"], 1)
        self.assertEqual(len(persisted["messages"]), 1)
        self.assertEqual(summary_exit, 0)
        self.assertEqual(
            summary_payload,
            {
                "peers": [
                    {
                        "node_id": "local-node-a",
                        "status": "available",
                        "heartbeat_count": 1,
                        "last_heartbeat_sequence": 1,
                        "capabilities": ["text_chunk", "text_embed"],
                    }
                ]
            },
        )

    def test_cli_refuses_to_overwrite_existing_message_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-heartbeats.json"
            original = "keep me"
            message_log_path.write_text(original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "announce-local-node",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            contents = message_log_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("message log file already exists", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(contents, original)

    def test_cli_empty_capability_returns_nonzero_without_creating_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-heartbeats.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "announce-local-node",
                        "--node-id",
                        "local-node-a",
                        "--capability",
                        "",
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("capability[0] must be a non-empty string", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertFalse(message_log_path.exists())

    def test_cli_offline_status_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-heartbeats.json"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "announce-local-node",
                        "--node-id",
                        "local-node-a",
                        "--status",
                        "offline",
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            persisted = json.loads(message_log_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["status"], "offline")
        self.assertEqual(persisted["metadata"]["status"], "offline")
        self.assertEqual(persisted["messages"][0]["payload"]["status"], "offline")


if __name__ == "__main__":
    unittest.main()
