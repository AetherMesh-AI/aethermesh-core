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
    def test_assigns_jobs_fairly_across_available_nodes(self) -> None:
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

    def test_routes_assignments_by_job_type_capability(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", capabilities=("echo",)),
                ScheduledNode("node-b", capabilities=("text_stats",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [
                Job(job_id="stats-1", job_type="text_stats"),
                Job(job_id="echo-1", job_type="echo"),
            ]
        )

        self.assertEqual(
            [assignment.to_dict() for assignment in assignments],
            [
                {"job_id": "stats-1", "node_id": "node-b"},
                {"job_id": "echo-1", "node_id": "node-a"},
            ],
        )

    def test_default_capabilities_support_current_local_job_types(self) -> None:
        node = ScheduledNode("node-a")

        self.assertEqual(node.capabilities, DEFAULT_LOCAL_CAPABILITIES)
        assignments = LocalScheduler([node]).assign_jobs(
            [
                Job(job_id="echo-1", job_type="echo"),
                Job(job_id="keyword-1", job_type="keyword_extract"),
                Job(job_id="chunk-1", job_type="text_chunk"),
                Job(job_id="embed-1", job_type="text_embed"),
                Job(job_id="stats-1", job_type="text_stats"),
            ]
        )
        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["node-a", "node-a", "node-a", "node-a", "node-a"],
        )

    def test_skips_offline_nodes_even_when_capable(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode(
                    "node-a", status=NodeStatus.OFFLINE, capabilities=("echo",)
                ),
                ScheduledNode(
                    "node-b", status=NodeStatus.AVAILABLE, capabilities=("echo",)
                ),
            ]
        )

        assignments = scheduler.assign_jobs(
            [
                Job(job_id="job-1", job_type="echo"),
                Job(job_id="job-2", job_type="echo"),
                Job(job_id="job-3", job_type="echo"),
            ]
        )

        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["node-b", "node-b", "node-b"],
        )

    def test_prefers_fewest_batch_assignments_then_manifest_order(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", capabilities=("echo",)),
                ScheduledNode("node-b", capabilities=("echo", "text_stats")),
                ScheduledNode("node-c", capabilities=("text_stats",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [
                Job(job_id="echo-1", job_type="echo"),
                Job(job_id="stats-1", job_type="text_stats"),
                Job(job_id="echo-2", job_type="echo"),
                Job(job_id="stats-2", job_type="text_stats"),
            ]
        )

        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["node-a", "node-b", "node-a", "node-c"],
        )

    def test_mixed_job_types_share_work_across_equally_capable_nodes(self) -> None:
        scheduler = LocalScheduler(["node-a", "node-b"])

        assignments = scheduler.assign_jobs(
            [
                Job(job_id="echo-1", job_type="echo"),
                Job(job_id="stats-1", job_type="text_stats"),
                Job(job_id="keyword-1", job_type="keyword_extract"),
                Job(job_id="chunk-1", job_type="text_chunk"),
                Job(job_id="embed-1", job_type="text_embed"),
            ]
        )

        self.assertEqual(
            [assignment.node_id for assignment in assignments],
            ["node-a", "node-b", "node-a", "node-b", "node-a"],
        )

    def test_routes_keyword_extract_by_declared_capability(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", capabilities=("echo", "text_stats")),
                ScheduledNode("node-b", capabilities=("keyword_extract",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [Job(job_id="keyword-1", job_type="keyword_extract")]
        )

        self.assertEqual(
            assignments[0].to_dict(), {"job_id": "keyword-1", "node_id": "node-b"}
        )

    def test_routes_text_chunk_by_declared_capability(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", capabilities=("echo", "text_stats")),
                ScheduledNode("node-b", capabilities=("text_chunk",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [Job(job_id="chunk-1", job_type="text_chunk")]
        )

        self.assertEqual(
            assignments[0].to_dict(), {"job_id": "chunk-1", "node_id": "node-b"}
        )

    def test_routes_text_embed_by_declared_capability(self) -> None:
        scheduler = LocalScheduler(
            [
                ScheduledNode("node-a", capabilities=("echo", "text_stats")),
                ScheduledNode("node-b", capabilities=("text_embed",)),
            ]
        )

        assignments = scheduler.assign_jobs(
            [Job(job_id="embed-1", job_type="text_embed")]
        )

        self.assertEqual(
            assignments[0].to_dict(), {"job_id": "embed-1", "node_id": "node-b"}
        )

    def test_returns_empty_assignments_when_no_jobs(self) -> None:
        scheduler = LocalScheduler([])

        self.assertEqual(scheduler.assign_jobs([]), [])

    def test_raises_when_jobs_exist_but_no_nodes_are_available(self) -> None:
        scheduler = LocalScheduler([ScheduledNode("node-a", status=NodeStatus.OFFLINE)])

        with self.assertRaisesRegex(NoAvailableNodesError, "no available nodes"):
            scheduler.assign_jobs([Job(job_id="job-1", job_type="echo")])

    def test_raises_when_no_available_node_is_capable(self) -> None:
        scheduler = LocalScheduler([ScheduledNode("node-a", capabilities=("echo",))])

        with self.assertRaisesRegex(
            NoAvailableNodesError, "job_id=embed-1 job_type=text_embed"
        ):
            scheduler.assign_jobs([Job(job_id="embed-1", job_type="text_embed")])

    def test_plain_job_like_object_requires_string_id_and_type(self) -> None:
        class HalfJob:
            job_id = "job-half"
            job_type = None

            def __str__(self) -> str:
                return "fallback-half-job"

        scheduler = LocalScheduler(["node-a"])

        assignment = scheduler.assign_jobs([HalfJob()])[0]

        self.assertEqual(
            assignment.to_dict(), {"job_id": "fallback-half-job", "node_id": "node-a"}
        )

    def test_accepts_plain_node_ids_as_available_nodes(self) -> None:
        scheduler = LocalScheduler(["node-a"])

        assignments = scheduler.assign_jobs(["job-1"])

        self.assertEqual(assignments[0].node_id, "node-a")


if __name__ == "__main__":
    unittest.main()
