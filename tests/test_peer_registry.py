import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.peer_registry import (
    PeerRegistryError,
    peer_roster_document,
    peer_summary_document,
)


class PeerRegistryTests(unittest.TestCase):
    def test_summarizes_merges_and_sorts_heartbeat_peers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "node-b",
                                "recipient_node_id": None,
                                "payload": {
                                    "node_id": "node-b",
                                    "status": "available",
                                    "heartbeat_sequence": 2,
                                    "heartbeat_count": 1,
                                    "capabilities": ["echo"],
                                },
                                "correlation_id": None,
                            },
                            {
                                "message_id": "msg-0002",
                                "message_type": "job_assigned",
                                "sender_node_id": "local-scheduler",
                                "recipient_node_id": "node-b",
                                "payload": {
                                    "job_id": "echo-1",
                                    "job_type": "echo",
                                    "payload": {},
                                },
                                "correlation_id": "echo-1",
                            },
                            {
                                "message_id": "msg-0003",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "node-a",
                                "recipient_node_id": None,
                                "payload": {
                                    "node_id": "node-a",
                                    "status": "available",
                                    "heartbeat_sequence": 1,
                                    "heartbeat_count": 1,
                                    "capabilities": ["echo", "text_stats"],
                                },
                                "correlation_id": None,
                            },
                            {
                                "message_id": "msg-0004",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "node-b",
                                "recipient_node_id": None,
                                "payload": {
                                    "node_id": "node-b",
                                    "status": "offline",
                                    "heartbeat_sequence": 4,
                                    "heartbeat_count": 2,
                                    "capabilities": ["keyword_extract"],
                                },
                                "correlation_id": None,
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = peer_summary_document(log_path)

        self.assertEqual(
            payload,
            {
                "peers": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "heartbeat_count": 1,
                        "last_heartbeat_sequence": 1,
                        "capabilities": ["echo", "text_stats"],
                    },
                    {
                        "node_id": "node-b",
                        "status": "offline",
                        "heartbeat_count": 2,
                        "last_heartbeat_sequence": 4,
                        "capabilities": ["keyword_extract"],
                    },
                ]
            },
        )

    def test_missing_capabilities_are_backward_compatible_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "node-a",
                                "recipient_node_id": None,
                                "payload": {
                                    "node_id": "node-a",
                                    "status": "available",
                                    "heartbeat_sequence": 1,
                                    "heartbeat_count": 1,
                                },
                                "correlation_id": None,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            payload = peer_summary_document(log_path)

        self.assertEqual(
            payload,
            {
                "peers": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "heartbeat_count": 1,
                        "last_heartbeat_sequence": 1,
                        "capabilities": [],
                    }
                ]
            },
        )

    def test_malformed_heartbeat_payload_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            original = json.dumps(
                {
                    "version": 1,
                    "messages": [
                        {
                            "message_id": "msg-0001",
                            "message_type": "node_heartbeat",
                            "sender_node_id": "node-a",
                            "recipient_node_id": None,
                            "payload": {
                                "node_id": "node-a",
                                "status": "available",
                                "heartbeat_sequence": 1,
                                "capabilities": "echo",
                            },
                            "correlation_id": None,
                        }
                    ],
                },
                sort_keys=True,
            )
            log_path.write_text(original, encoding="utf-8")

            with self.assertRaises(PeerRegistryError) as cm:
                peer_summary_document(log_path)
            contents = log_path.read_text(encoding="utf-8")

        self.assertIn("capabilities", str(cm.exception))
        self.assertEqual(contents, original)

    def test_malformed_heartbeat_error_messages_are_stable(self) -> None:
        base = {
            "version": 1,
            "messages": [
                {
                    "message_id": "msg-0001",
                    "message_type": "node_heartbeat",
                    "sender_node_id": "node-a",
                    "recipient_node_id": None,
                    "payload": {
                        "node_id": "node-a",
                        "status": "available",
                        "heartbeat_sequence": 1,
                        "heartbeat_count": 1,
                        "capabilities": ["echo"],
                    },
                    "correlation_id": None,
                }
            ],
        }
        cases = [
            (
                ("node_id", ""),
                "heartbeat message msg-0001 payload field 'node_id' must be a non-empty string",
            ),
            (
                ("status", ""),
                "heartbeat message msg-0001 payload field 'status' must be a non-empty string",
            ),
            (
                ("heartbeat_sequence", True),
                "heartbeat message msg-0001 payload field 'heartbeat_sequence' must be a non-negative integer",
            ),
            (
                ("heartbeat_sequence", -1),
                "heartbeat message msg-0001 payload field 'heartbeat_sequence' must be a non-negative integer",
            ),
            (
                ("heartbeat_count", False),
                "heartbeat message msg-0001 payload field 'heartbeat_count' must be a non-negative integer",
            ),
            (
                ("heartbeat_count", -1),
                "heartbeat message msg-0001 payload field 'heartbeat_count' must be a non-negative integer",
            ),
            (
                ("capabilities", "echo"),
                "heartbeat message msg-0001 payload field 'capabilities' must be a list of strings",
            ),
            (
                ("capabilities", [""]),
                "heartbeat message msg-0001 payload field 'capabilities[0]' must be a non-empty string",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            for (field_name, value), expected_message in cases:
                with self.subTest(expected_message=expected_message):
                    document = json.loads(json.dumps(base))
                    document["messages"][0]["payload"][field_name] = value
                    log_path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(PeerRegistryError) as cm:
                        peer_summary_document(log_path)
                    self.assertEqual(str(cm.exception), expected_message)

    def test_peer_roster_builds_manifest_nodes_from_multiple_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "announce-a.json"
            second_log = Path(temp_dir) / "flow-message-log.json"
            _write_message_log(
                first_log,
                [
                    _heartbeat(
                        "msg-0001",
                        "node-b",
                        "available",
                        1,
                        ["echo"],
                    ),
                    {
                        "message_id": "msg-0002",
                        "message_type": "job_assigned",
                        "sender_node_id": "local-scheduler",
                        "recipient_node_id": "node-b",
                        "payload": {"job_id": "echo-1"},
                        "correlation_id": "echo-1",
                    },
                    _heartbeat(
                        "msg-0003",
                        "node-a",
                        "available",
                        5,
                        ["text_stats", "echo"],
                    ),
                ],
            )
            _write_message_log(
                second_log,
                [
                    _heartbeat(
                        "msg-0004",
                        "node-b",
                        "offline",
                        3,
                        ["keyword_extract"],
                    ),
                    _heartbeat(
                        "msg-0005",
                        "node-a",
                        "available",
                        4,
                        ["echo"],
                    ),
                ],
            )

            payload = peer_roster_document([first_log, second_log])

        self.assertEqual(
            payload,
            {
                "version": 1,
                "nodes": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "capabilities": ["text_stats", "echo"],
                    },
                    {
                        "node_id": "node-b",
                        "status": "offline",
                        "capabilities": ["keyword_extract"],
                    },
                ],
                "metadata": {
                    "source_message_log_paths": [str(first_log), str(second_log)],
                    "peer_count": 2,
                    "heartbeat_count": 4,
                    "heartbeat_counts_by_node": {"node-a": 2, "node-b": 2},
                },
            },
        )

    def test_peer_roster_sequence_tie_uses_later_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "first.json"
            second_log = Path(temp_dir) / "second.json"
            _write_message_log(
                first_log,
                [
                    _heartbeat("msg-0001", "node-a", "available", 7, ["echo"]),
                    _heartbeat(
                        "msg-0002",
                        "node-a",
                        "available",
                        7,
                        ["text_stats"],
                    ),
                ],
            )
            _write_message_log(
                second_log,
                [
                    _heartbeat(
                        "msg-0003",
                        "node-a",
                        "offline",
                        7,
                        ["keyword_extract"],
                    )
                ],
            )

            payload = peer_roster_document([first_log, second_log])

        self.assertEqual(
            payload["nodes"],
            [
                {
                    "node_id": "node-a",
                    "status": "offline",
                    "capabilities": ["keyword_extract"],
                }
            ],
        )
        metadata = payload["metadata"]
        if not isinstance(metadata, dict):
            self.fail("metadata must be a dictionary")
        self.assertEqual(metadata.get("heartbeat_counts_by_node"), {"node-a": 3})

    def test_peer_roster_invalid_heartbeat_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            _write_message_log(
                log_path,
                [_heartbeat("msg-0001", "node-a", "available", 1, "echo")],
            )

            with self.assertRaises(PeerRegistryError) as cm:
                peer_roster_document([log_path])

        self.assertIn("capabilities", str(cm.exception))


def _write_message_log(path: Path, messages: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps({"version": 1, "messages": messages}, sort_keys=True),
        encoding="utf-8",
    )


def _heartbeat(
    message_id: str,
    node_id: str,
    status: str,
    sequence: int,
    capabilities: object,
) -> dict[str, object]:
    return {
        "message_id": message_id,
        "message_type": "node_heartbeat",
        "sender_node_id": node_id,
        "recipient_node_id": None,
        "payload": {
            "node_id": node_id,
            "status": status,
            "heartbeat_sequence": sequence,
            "capabilities": capabilities,
        },
        "correlation_id": None,
    }


if __name__ == "__main__":
    unittest.main()
