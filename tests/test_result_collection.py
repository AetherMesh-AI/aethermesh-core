import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.result_collection import (
    ResultCollectionError,
    collect_local_results,
)


def _message(
    message_id: str,
    message_type: str,
    *,
    payload: dict[str, object] | None = None,
    correlation_id: str | None = None,
    sender_node_id: str = "local-node-a",
    recipient_node_id: str | None = "local-ledger",
) -> dict[str, object]:
    return {
        "message_id": message_id,
        "message_type": message_type,
        "sender_node_id": sender_node_id,
        "recipient_node_id": recipient_node_id,
        "payload": payload or {},
        "correlation_id": correlation_id,
    }


def _write_log(path: Path, messages: list[dict[str, object]]) -> None:
    path.write_text(json.dumps({"version": 1, "messages": messages}), encoding="utf-8")


class ResultCollectionTests(unittest.TestCase):
    def test_collects_results_and_contribution_totals_in_worker_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_path = Path(temp_dir) / "dispatch.json"
            worker_a_path = Path(temp_dir) / "worker-a.json"
            worker_b_path = Path(temp_dir) / "worker-b.json"
            _write_log(
                dispatch_path,
                [
                    _message(
                        "msg-0001",
                        "job_assigned",
                        payload={"job_id": "echo-1", "job_type": "echo"},
                        correlation_id="echo-1",
                        sender_node_id="local-scheduler",
                        recipient_node_id="local-node-a",
                    ),
                    _message(
                        "msg-0002",
                        "job_assigned",
                        payload={"job_id": "echo-2", "job_type": "echo"},
                        correlation_id="echo-2",
                        sender_node_id="local-scheduler",
                        recipient_node_id="local-node-b",
                    ),
                ],
            )
            _write_log(
                worker_a_path,
                [
                    _message(
                        "msg-0001",
                        "job_assigned",
                        payload={"job_id": "echo-1", "job_type": "echo"},
                        correlation_id="echo-1",
                        sender_node_id="local-scheduler",
                        recipient_node_id="local-node-a",
                    ),
                    _message(
                        "msg-0003",
                        "job_result_reported",
                        payload={"job_id": "echo-1", "status": "completed"},
                        correlation_id="echo-1",
                    ),
                    _message(
                        "msg-0004",
                        "contribution_recorded",
                        payload={
                            "job_id": "echo-1",
                            "node_id": "local-node-a",
                            "contribution_units": 1,
                        },
                        correlation_id="echo-1",
                        sender_node_id="local-ledger",
                        recipient_node_id="local-node-a",
                    ),
                ],
            )
            _write_log(
                worker_b_path,
                [
                    _message(
                        "msg-0005",
                        "job_result_reported",
                        payload={"job_id": "echo-2", "status": "completed"},
                        correlation_id="echo-2",
                        sender_node_id="local-node-b",
                    ),
                    _message(
                        "msg-0006",
                        "contribution_recorded",
                        payload={
                            "job_id": "echo-2",
                            "node_id": "local-node-b",
                            "contribution_units": 2,
                        },
                        correlation_id="echo-2",
                        sender_node_id="local-ledger",
                        recipient_node_id="local-node-b",
                    ),
                ],
            )

            summary = collect_local_results(
                dispatch_message_log_path=dispatch_path,
                worker_message_log_paths=[worker_a_path, worker_b_path],
            )

        self.assertEqual(summary["known_assignment_count"], 2)
        self.assertEqual(summary["reported_result_count"], 2)
        self.assertEqual(summary["contribution_recorded_count"], 2)
        self.assertEqual(summary["missing_assignment_ids"], [])
        self.assertEqual(summary["duplicate_message_ids"], [])
        self.assertEqual(summary["conflicting_message_ids"], [])
        self.assertEqual(
            summary["per_node_contribution_units"],
            {"local-node-a": 1, "local-node-b": 2},
        )
        self.assertEqual(summary["total_contribution_units"], 3)
        self.assertEqual(
            summary["collected_message_ids"],
            ["msg-0003", "msg-0004", "msg-0005", "msg-0006"],
        )

    def test_reports_missing_assignment_results_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_path = Path(temp_dir) / "dispatch.json"
            worker_path = Path(temp_dir) / "worker.json"
            _write_log(
                dispatch_path,
                [
                    _message(
                        "msg-0001",
                        "job_assigned",
                        payload={"job_id": "echo-1"},
                        correlation_id="echo-1",
                    ),
                    _message(
                        "msg-0002",
                        "job_assigned",
                        payload={"job_id": "echo-2"},
                        correlation_id="echo-2",
                    ),
                ],
            )
            _write_log(
                worker_path,
                [
                    _message(
                        "msg-0003",
                        "job_result_reported",
                        payload={"job_id": "echo-1"},
                        correlation_id="echo-1",
                    )
                ],
            )

            summary = collect_local_results(
                dispatch_message_log_path=dispatch_path,
                worker_message_log_paths=[worker_path],
            )

        self.assertEqual(summary["missing_assignment_ids"], ["echo-2"])
        self.assertEqual(summary["reported_result_count"], 1)

    def test_deduplicates_exact_duplicate_messages(self) -> None:
        duplicate = _message(
            "msg-0003",
            "job_result_reported",
            payload={"job_id": "echo-1"},
            correlation_id="echo-1",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_path = Path(temp_dir) / "dispatch.json"
            worker_a_path = Path(temp_dir) / "worker-a.json"
            worker_b_path = Path(temp_dir) / "worker-b.json"
            _write_log(
                dispatch_path,
                [_message("msg-0001", "job_assigned", payload={"job_id": "echo-1"})],
            )
            _write_log(worker_a_path, [duplicate])
            _write_log(worker_b_path, [duplicate])

            summary = collect_local_results(
                dispatch_message_log_path=dispatch_path,
                worker_message_log_paths=[worker_a_path, worker_b_path],
            )

        self.assertEqual(summary["duplicate_message_ids"], ["msg-0003"])
        self.assertEqual(summary["reported_result_count"], 1)
        self.assertEqual(summary["collected_message_ids"], ["msg-0003"])

    def test_conflicting_duplicate_message_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_path = Path(temp_dir) / "dispatch.json"
            worker_a_path = Path(temp_dir) / "worker-a.json"
            worker_b_path = Path(temp_dir) / "worker-b.json"
            _write_log(
                dispatch_path,
                [
                    _message("msg-0001", "job_assigned", payload={"job_id": "echo-1"}),
                    _message("msg-0002", "job_assigned", payload={"job_id": "echo-2"}),
                ],
            )
            _write_log(
                worker_a_path,
                [_message("msg-0003", "job_result_reported", payload={"job_id": "echo-1"})],
            )
            _write_log(
                worker_b_path,
                [_message("msg-0003", "job_result_reported", payload={"job_id": "echo-2"})],
            )

            with self.assertRaises(ResultCollectionError) as cm:
                collect_local_results(
                    dispatch_message_log_path=dispatch_path,
                    worker_message_log_paths=[worker_a_path, worker_b_path],
                )

        self.assertIn("conflicting duplicate message_id", str(cm.exception))

    def test_unknown_assignment_and_correlation_mismatch_fail(self) -> None:
        cases = [
            (
                [_message("msg-0002", "job_result_reported", payload={"job_id": "missing"})],
                "unknown assignment",
            ),
            (
                [
                    _message(
                        "msg-0002",
                        "job_result_reported",
                        payload={"job_id": "echo-1"},
                        correlation_id="different",
                    )
                ],
                "correlation_id and payload.job_id disagree",
            ),
        ]
        for worker_messages, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temp_dir:
                dispatch_path = Path(temp_dir) / "dispatch.json"
                worker_path = Path(temp_dir) / "worker.json"
                _write_log(
                    dispatch_path,
                    [_message("msg-0001", "job_assigned", payload={"job_id": "echo-1"})],
                )
                _write_log(worker_path, worker_messages)

                with self.assertRaises(ResultCollectionError) as cm:
                    collect_local_results(
                        dispatch_message_log_path=dispatch_path,
                        worker_message_log_paths=[worker_path],
                    )

                self.assertIn(expected, str(cm.exception))


if __name__ == "__main__":
    unittest.main()
