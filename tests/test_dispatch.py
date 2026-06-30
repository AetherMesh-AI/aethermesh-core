import unittest

from aethermesh_core.dispatch import dispatch_local_batch
from aethermesh_core.models import Job
from aethermesh_core.scheduler import NodeStatus, ScheduledNode


class DispatchTests(unittest.TestCase):
    def test_dispatch_emits_heartbeats_and_assignments_without_execution_messages(
        self,
    ) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(
                job_id="stats-1", job_type="text_stats", payload={"text": "hello mesh"}
            ),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
        ]

        result = dispatch_local_batch(
            manifest_path="examples/local-batch.json",
            message_log_path="./local-dispatch.json",
            nodes=[
                ScheduledNode("node-a", capabilities=("echo", "text_stats")),
                ScheduledNode(
                    "node-b", status=NodeStatus.OFFLINE, capabilities=("echo",)
                ),
                ScheduledNode("node-c", capabilities=("echo",)),
            ],
            jobs=jobs,
        )

        self.assertEqual(
            [message.message_type for message in result.messages],
            [
                "node_heartbeat",
                "node_heartbeat",
                "job_assigned",
                "job_assigned",
                "job_assigned",
            ],
        )
        self.assertEqual(
            [message.message_id for message in result.messages],
            ["msg-0001", "msg-0002", "msg-0003", "msg-0004", "msg-0005"],
        )
        self.assertEqual(
            [assignment.to_dict() for assignment in result.assignments],
            [
                {"job_id": "echo-1", "node_id": "node-a"},
                {"job_id": "stats-1", "node_id": "node-a"},
                {"job_id": "echo-2", "node_id": "node-c"},
            ],
        )
        self.assertEqual(
            [
                message.payload
                for message in result.messages
                if message.message_type == "job_assigned"
            ],
            [
                {
                    "job_id": "echo-1",
                    "job_type": "echo",
                    "payload": {"message": "one"},
                    "node_id": "node-a",
                },
                {
                    "job_id": "stats-1",
                    "job_type": "text_stats",
                    "payload": {"text": "hello mesh"},
                    "node_id": "node-a",
                },
                {
                    "job_id": "echo-2",
                    "job_type": "echo",
                    "payload": {"message": "two"},
                    "node_id": "node-c",
                },
            ],
        )
        self.assertEqual(
            [
                message.payload
                for message in result.messages
                if message.message_type == "node_heartbeat"
            ],
            [
                {
                    "node_id": "node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "capabilities": ["echo", "text_stats"],
                },
                {
                    "node_id": "node-c",
                    "status": "available",
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                    "capabilities": ["echo"],
                },
            ],
        )
        self.assertNotIn(
            "job_result_reported", [message.message_type for message in result.messages]
        )
        self.assertNotIn(
            "contribution_recorded",
            [message.message_type for message in result.messages],
        )
        self.assertEqual(
            result.to_dict(),
            {
                "command": "dispatch-local-batch",
                "manifest_path": "examples/local-batch.json",
                "message_log_path": "./local-dispatch.json",
                "job_count": 3,
                "assignment_count": 3,
                "message_count": 5,
                "nodes": [
                    {
                        "node_id": "node-a",
                        "status": "available",
                        "capabilities": ["echo", "text_stats"],
                    },
                    {
                        "node_id": "node-b",
                        "status": "offline",
                        "capabilities": ["echo"],
                    },
                    {
                        "node_id": "node-c",
                        "status": "available",
                        "capabilities": ["echo"],
                    },
                ],
                "assignments": [
                    {"job_id": "echo-1", "node_id": "node-a"},
                    {"job_id": "stats-1", "node_id": "node-a"},
                    {"job_id": "echo-2", "node_id": "node-c"},
                ],
                "assigned_node_ids": ["node-a", "node-c"],
            },
        )

    def test_dispatch_empty_nodes_error_message_is_stable(self) -> None:
        with self.assertRaises(ValueError) as cm:
            dispatch_local_batch(
                manifest_path="manifest.json",
                message_log_path="messages.json",
                nodes=[],
                jobs=[Job(job_id="echo-1", job_type="echo", payload={})],
            )
        self.assertEqual(str(cm.exception), "nodes must contain at least one node")

    def test_dispatch_uses_scheduler_capability_failure(self) -> None:
        with self.assertRaises(ValueError) as cm:
            dispatch_local_batch(
                manifest_path="manifest.json",
                message_log_path="messages.json",
                nodes=[ScheduledNode("node-a", capabilities=("echo",))],
                jobs=[Job(job_id="stats-1", job_type="text_stats", payload={})],
            )

        self.assertIn("job_id=stats-1 job_type=text_stats", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
