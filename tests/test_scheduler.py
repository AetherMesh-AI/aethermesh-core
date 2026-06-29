import unittest

from aethermesh_core.models import Job
from aethermesh_core.scheduler import (
    DEFAULT_LOCAL_CAPABILITIES,
    LocalScheduler,
    NoAvailableNodesError,
    NodeStatus,
    ScheduledNode,
)


class LocalSchedulerTests(unittest.TestCase):
    def test_assigns_jobs_round_robin_across_available_nodes(self) -> None:
        scheduler = LocalScheduler(["node-a", "node-b"])

        assignments = scheduler.assign_jobs(["job-1", "job-2", "job-3"])

        self.assertEqual(
            [assignment.to_dict() for assignment in assignments],
            [
                {"job_id": "job-1", "node_id": "node-a"},
                {"job_id": "job-2", "node_id": "node-b"},
                {"job_id": "job-3", "node_id": "node-a"},
            ],
        )

    def test_skips_offline_nodes(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", status=NodeStatus.OFFLINE),
                ScheduledNode("node-b", status=NodeStatus.AVAILABLE),
            ]
        )

        assignments = scheduler.assign_jobs(["job-1", "job-2", "job-3"])

        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["node-b", "node-b", "node-b"],
        )

    def test_returns_empty_assignments_when_no_jobs(self) -> None:
        scheduler = LocalScheduler([])

        self.assertEqual(scheduler.assign_jobs([]), [])

    def test_raises_when_jobs_exist_but_no_nodes_are_available(self) -> None:
        scheduler = LocalScheduler(
            [ScheduledNode("node-a", status=NodeStatus.OFFLINE)]
        )

        with self.assertRaisesRegex(
            NoAvailableNodesError, "no available nodes for job 'job-1' of type 'echo'"
        ):
            scheduler.assign_jobs([Job("job-1", "echo")])

    def test_accepts_plain_node_ids_as_available_nodes_with_default_capabilities(self) -> None:
        scheduler = LocalScheduler(["node-a"])

        assignments = scheduler.assign_jobs([Job("job-1", "text_stats")])

        self.assertEqual(assignments[0].node_id, "node-a")
        self.assertEqual(scheduler.nodes[0].capabilities, DEFAULT_LOCAL_CAPABILITIES)

    def test_assigns_to_available_capable_node(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("echo-node", capabilities=("echo",)),
                ScheduledNode("stats-node", capabilities=("text_stats",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [
                Job("echo-1", "echo"),
                Job("stats-1", "text_stats"),
            ]
        )

        self.assertEqual(
            [assignment.to_dict() for assignment in assignments],
            [
                {"job_id": "echo-1", "node_id": "echo-node"},
                {"job_id": "stats-1", "node_id": "stats-node"},
            ],
        )

    def test_round_robin_is_deterministic_per_eligible_job_type(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("echo-a", capabilities=("echo",)),
                ScheduledNode("both", capabilities=("echo", "text_stats")),
                ScheduledNode("stats-a", capabilities=("text_stats",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [
                Job("echo-1", "echo"),
                Job("stats-1", "text_stats"),
                Job("echo-2", "echo"),
                Job("stats-2", "text_stats"),
                Job("echo-3", "echo"),
            ]
        )

        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["echo-a", "both", "both", "stats-a", "echo-a"],
        )

    def test_raises_when_no_available_node_supports_job_type(self) -> None:
        scheduler = LocalScheduler([ScheduledNode("echo-node", capabilities=("echo",))])

        with self.assertRaisesRegex(
            NoAvailableNodesError, "no available node supports job 'stats-1' of type 'text_stats'"
        ):
            scheduler.assign_jobs([Job("stats-1", "text_stats")])

    def test_offline_capable_node_is_not_assigned(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("stats-offline", NodeStatus.OFFLINE, ("text_stats",)),
                ScheduledNode("echo-node", NodeStatus.AVAILABLE, ("echo",)),
            ]
        )

        with self.assertRaisesRegex(
            NoAvailableNodesError, "no available node supports job 'stats-1' of type 'text_stats'"
        ):
            scheduler.assign_jobs([Job("stats-1", "text_stats")])


if __name__ == "__main__":
    unittest.main()
