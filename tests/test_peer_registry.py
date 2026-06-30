import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.peer_registry import (
    PeerRegistryError,
    discover_local_peers_document,
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

    def test_discover_local_peers_aggregates_sorted_roster_from_multiple_logs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "node-b.json"
            second_log = Path(temp_dir) / "node-a.json"
            _write_message_log(
                first_log, [_heartbeat("msg-0001", "node-b", 1, ["echo"])]
            )
            _write_message_log(
                second_log,
                [
                    {
                        "message_id": "msg-0002",
                        "message_type": "job_assigned",
                        "sender_node_id": "local-scheduler",
                        "recipient_node_id": "node-a",
                        "payload": {
                            "job_id": "echo-1",
                            "job_type": "echo",
                            "payload": {},
                        },
                        "correlation_id": "echo-1",
                    },
                    _heartbeat("msg-0003", "node-a", 1, ["text_stats"]),
                ],
            )

            payload = discover_local_peers_document([first_log, second_log])

        self.assertEqual(
            payload,
            {
                "peers": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "heartbeat_count": 1,
                        "last_heartbeat_sequence": 1,
                        "capabilities": ["text_stats"],
                    },
                    {
                        "node_id": "node-b",
                        "status": "available",
                        "heartbeat_count": 1,
                        "last_heartbeat_sequence": 1,
                        "capabilities": ["echo"],
                    },
                ]
            },
        )

    def test_discover_local_peers_merges_duplicate_nodes_by_highest_sequence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "node-a-old.json"
            second_log = Path(temp_dir) / "node-a-new.json"
            _write_message_log(
                first_log, [_heartbeat("msg-0001", "node-a", 1, ["echo"])]
            )
            _write_message_log(
                second_log,
                [_heartbeat("msg-0002", "node-a", 3, ["text_stats"], status="offline")],
            )

            payload = discover_local_peers_document([first_log, second_log])

        self.assertEqual(
            payload,
            {
                "peers": [
                    {
                        "node_id": "node-a",
                        "status": "offline",
                        "heartbeat_count": 2,
                        "last_heartbeat_sequence": 3,
                        "capabilities": ["text_stats"],
                    }
                ]
            },
        )

    def test_discover_local_peers_equal_sequence_keeps_first_visible_state(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "node-a-first.json"
            second_log = Path(temp_dir) / "node-a-second.json"
            _write_message_log(
                first_log, [_heartbeat("msg-0001", "node-a", 2, ["echo"])]
            )
            _write_message_log(
                second_log,
                [_heartbeat("msg-0002", "node-a", 2, ["text_stats"], status="offline")],
            )

            payload = discover_local_peers_document([first_log, second_log])

        self.assertEqual(
            payload,
            {
                "peers": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "heartbeat_count": 2,
                        "last_heartbeat_sequence": 2,
                        "capabilities": ["echo"],
                    }
                ]
            },
        )

    def test_discover_local_peers_malformed_later_log_leaves_earlier_log_unchanged(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_log = Path(temp_dir) / "valid.json"
            second_log = Path(temp_dir) / "malformed.json"
            _write_message_log(
                first_log, [_heartbeat("msg-0001", "node-a", 1, ["echo"])]
            )
            original_first = first_log.read_text(encoding="utf-8")
            second_log.write_text("not-json", encoding="utf-8")

            with self.assertRaises(PeerRegistryError) as cm:
                discover_local_peers_document([first_log, second_log])
            after_first = first_log.read_text(encoding="utf-8")

        self.assertIn("message log JSON is malformed", str(cm.exception))
        self.assertEqual(after_first, original_first)


def _heartbeat(
    message_id: str,
    node_id: str,
    sequence: int,
    capabilities: list[str],
    *,
    status: str = "available",
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
            "heartbeat_count": 1,
            "capabilities": capabilities,
        },
        "correlation_id": None,
    }


def _write_message_log(path: Path, messages: list[dict[str, object]]) -> None:
    path.write_text(
        json.dumps({"version": 1, "messages": messages}, sort_keys=True),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
