import unittest

from aethermesh_core.scheduler import (
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

        with self.assertRaisesRegex(NoAvailableNodesError, "no available nodes"):
            scheduler.assign_jobs(["job-1"])

    def test_accepts_plain_node_ids_as_available_nodes(self) -> None:
        scheduler = LocalScheduler(["node-a"])

        assignments = scheduler.assign_jobs(["job-1"])

        self.assertEqual(assignments[0].node_id, "node-a")


if __name__ == "__main__":
    unittest.main()
