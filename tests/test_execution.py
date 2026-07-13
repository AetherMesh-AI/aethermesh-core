import unittest
from dataclasses import replace
from typing import Any, cast
from unittest.mock import patch

from aethermesh_core.execution import (
    ExecutionAssignmentError,
    LocalExecutor,
    PreparedWorkAssignment,
)
from aethermesh_core.models import Job, JobResult, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.scheduler import LocalScheduler


class RecordingRunner:
    def __init__(self, result: JobResult) -> None:
        self.result = result
        self.calls: list[Job] = []

    def run(self, job: Job) -> JobResult:
        self.calls.append(job)
        return self.result


class ExecutorBoundaryTests(unittest.TestCase):
    def _assignment(self) -> PreparedWorkAssignment:
        return PreparedWorkAssignment(
            assignment_id="assignment-1",
            work_item=Job(
                job_id="echo-1", job_type="echo", payload={"message": "hello"}
            ),
            executor_node_id="node-executor",
            manifest_ref="manifests/batch-1.json",
            creator_node_id="node-creator",
            lineage={"parent_assignment_id": "assignment-0"},
            attribution={"requester_node_id": "node-requester"},
        )

    def test_scheduler_produces_assignment_without_invoking_execution(self) -> None:
        with patch.object(LocalRunner, "run") as run:
            assignments = LocalScheduler(["node-executor"]).assign_jobs(
                [Job(job_id="echo-1", job_type="echo")]
            )

        self.assertEqual(
            assignments[0].to_dict(), {"job_id": "echo-1", "node_id": "node-executor"}
        )
        run.assert_not_called()

    def test_executor_runs_prepared_assignment_and_preserves_receipt_provenance(
        self,
    ) -> None:
        assignment = self._assignment()
        runner = RecordingRunner(
            LocalRunner(NodeIdentity("node-executor")).run(assignment.work_item)
        )

        receipt = LocalExecutor(node_id="node-executor", runner=runner).execute(
            assignment
        )

        self.assertEqual(runner.calls, [assignment.work_item])
        self.assertEqual(receipt.assignment_id, "assignment-1")
        self.assertEqual(receipt.manifest_ref, "manifests/batch-1.json")
        self.assertEqual(receipt.creator_node_id, "node-creator")
        self.assertEqual(receipt.executor_node_id, "node-executor")
        self.assertTrue(receipt.validation.valid)
        self.assertEqual(receipt.validation_status, "valid")
        self.assertEqual(
            dict(receipt.lineage), {"parent_assignment_id": "assignment-0"}
        )
        self.assertEqual(
            dict(receipt.attribution), {"requester_node_id": "node-requester"}
        )
        self.assertEqual(
            receipt.to_dict()["validation"],
            {"status": "valid", "reason": "ok"},
        )

    def test_executor_returns_invalid_receipt_when_validation_fails(self) -> None:
        assignment = self._assignment()
        runner = RecordingRunner(
            JobResult(
                job_id="echo-1",
                node_id="node-executor",
                status="completed",
                output="not the assigned payload",
                error=None,
                contribution_units=1,
            )
        )

        receipt = LocalExecutor(node_id="node-executor", runner=runner).execute(
            assignment
        )

        self.assertFalse(receipt.validation.valid)
        self.assertEqual(receipt.validation_status, "invalid")
        self.assertEqual(receipt.to_dict()["lineage"], dict(assignment.lineage))

    def test_executor_rejects_result_reported_by_a_different_node(self) -> None:
        assignment = self._assignment()
        runner = RecordingRunner(
            JobResult(
                job_id="echo-1",
                node_id="node-other",
                status="completed",
                output="hello",
                error=None,
                contribution_units=1,
            )
        )

        receipt = LocalExecutor(node_id="node-executor", runner=runner).execute(
            assignment
        )

        self.assertFalse(receipt.validation.valid)
        self.assertEqual(receipt.validation.reason, "executor_node_id_mismatch")
        self.assertEqual(receipt.executor_node_id, "node-executor")
        self.assertEqual(receipt.result.node_id, "node-other")

    def test_invalid_assignments_fail_before_execution(self) -> None:
        runner = RecordingRunner(
            JobResult("echo-1", "node-executor", "completed", "hello", None, 1)
        )
        invalid_cases = [
            ({"assignment_id": ""}, "assignment_id must be a non-empty string"),
            ({"executor_node_id": ""}, "executor_node_id must be a non-empty string"),
            ({"manifest_ref": ""}, "manifest_ref must be a non-empty string"),
            ({"creator_node_id": ""}, "creator_node_id must be a non-empty string"),
            ({"work_item": "not-a-job"}, "work_item must be a Job"),
            (
                {"work_item": Job(job_id="", job_type="echo")},
                "work_item.job_id must be a non-empty string",
            ),
            (
                {"work_item": Job(job_id="echo-1", job_type="")},
                "work_item.job_type must be a non-empty string",
            ),
            ({"lineage": []}, "lineage must be a mapping"),
            ({"lineage": {"": "bad"}}, "lineage keys must be non-empty strings"),
            ({"attribution": []}, "attribution must be a mapping"),
            (
                {"attribution": {"": "bad"}},
                "attribution keys must be non-empty strings",
            ),
        ]
        for changes, message in invalid_cases:
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ExecutionAssignmentError, message),
            ):
                replace(self._assignment(), **changes)

        with self.assertRaisesRegex(ExecutionAssignmentError, "does not match"):
            LocalExecutor(node_id="node-other", runner=runner).execute(
                self._assignment()
            )
        self.assertEqual(runner.calls, [])

    def test_metadata_is_snapshotted_at_the_boundary(self) -> None:
        payload = {"message": "hello", "options": {"mode": "before"}}
        lineage = {"parent": {"id": "before"}}
        attribution = {"requester": {"id": "before"}}
        assignment = replace(
            self._assignment(),
            work_item=Job(job_id="echo-1", job_type="echo", payload=payload),
            lineage=lineage,
            attribution=attribution,
            creator_node_id=None,
        )
        payload["options"]["mode"] = "after"
        lineage["parent"]["id"] = "after"
        attribution["requester"]["id"] = "after"

        self.assertEqual(assignment.work_item.payload["options"], {"mode": "before"})
        self.assertEqual(dict(assignment.lineage), {"parent": {"id": "before"}})
        self.assertEqual(dict(assignment.attribution), {"requester": {"id": "before"}})
        self.assertIsNone(assignment.creator_node_id)

        with self.assertRaises(TypeError):
            cast(dict[str, Any], assignment.lineage["parent"])["id"] = "direct mutation"

        receipt = LocalExecutor(
            node_id="node-executor",
            runner=RecordingRunner(
                LocalRunner(NodeIdentity("node-executor")).run(assignment.work_item)
            ),
        ).execute(assignment)
        serialized = receipt.to_dict()
        serialized_lineage = cast(dict[str, Any], serialized["lineage"])
        serialized_lineage["parent"]["id"] = "serialized mutation"
        self.assertEqual(dict(receipt.lineage), {"parent": {"id": "before"}})

    def test_metadata_sequences_and_sets_are_frozen_and_serialized(self) -> None:
        assignment = replace(
            self._assignment(),
            lineage={"sequence": ["first", "second"]},
            attribution={"tags": {"local"}},
        )

        self.assertEqual(assignment.lineage["sequence"], ("first", "second"))
        self.assertEqual(assignment.attribution["tags"], frozenset({"local"}))

        receipt = LocalExecutor(
            node_id="node-executor",
            runner=RecordingRunner(
                LocalRunner(NodeIdentity("node-executor")).run(assignment.work_item)
            ),
        ).execute(assignment)
        self.assertEqual(
            receipt.to_dict()["lineage"], {"sequence": ["first", "second"]}
        )
        self.assertEqual(receipt.to_dict()["attribution"], {"tags": ["local"]})


if __name__ == "__main__":
    unittest.main()
