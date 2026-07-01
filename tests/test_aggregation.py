import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aethermesh_core.aggregation import (
    AggregationError,
    _accepted_result,
    _is_accepted,
    _totals_by_field,
    _validate_aggregate_document,
    _validation_totals,
    aggregate_local_flow,
    build_local_flow_aggregate,
    write_aggregate_document,
)
from aethermesh_core.cli import run_local_flow
from aethermesh_core.flow_audit import FlowAuditError


class LocalFlowAggregationTests(unittest.TestCase):
    def test_builds_aggregate_from_generated_local_flow_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))

            summary = aggregate_local_flow(output_dir)
            aggregate_path = output_dir / "aggregate-result.json"
            aggregate = _load_json(aggregate_path)

        self.assertEqual(summary["command"], "aggregate-local-flow")
        self.assertEqual(summary["aggregate_path"], str(aggregate_path))
        self.assertEqual(aggregate["version"], 1)
        self.assertEqual(aggregate["counts"]["receipts"], 2)
        self.assertEqual(aggregate["counts"]["accepted_results"], 2)
        self.assertEqual(aggregate["counts"]["invalid_or_zero_credit_receipts"], 0)
        self.assertEqual(aggregate["counts"]["total_credited_units"], 3)
        self.assertEqual(aggregate["totals_by_job_type"], {"echo": 1, "text_stats": 2})
        self.assertEqual(
            aggregate["totals_by_node_id"], {"local-node-a": 1, "local-node-b": 2}
        )
        self.assertEqual(aggregate["validation_totals"]["valid"], 2)
        self.assertEqual(aggregate["validation_totals"]["invalid"], 0)
        self.assertEqual(
            [entry["job_id"] for entry in aggregate["accepted_results"]],
            ["echo-1", "text-stats-1"],
        )
        self.assertEqual(
            aggregate["accepted_results"],
            [
                {
                    "job_id": "echo-1",
                    "job_type": "echo",
                    "node_id": "local-node-a",
                    "result_status": "completed",
                    "credited_units": 1,
                    "validation_valid": True,
                    "validation_reason": "ok",
                    "output_summary": {"value": "hello mesh"},
                    "assignment_message_id": "msg-0003",
                    "result_message_id": "msg-0005",
                    "contribution_message_id": "msg-0007",
                },
                {
                    "job_id": "text-stats-1",
                    "job_type": "text_stats",
                    "node_id": "local-node-b",
                    "result_status": "completed",
                    "credited_units": 2,
                    "validation_valid": True,
                    "validation_reason": "ok",
                    "output_summary": {
                        "character_count": 21,
                        "line_count": 2,
                        "normalized_preview": "hello mesh hello node",
                        "word_count": 4,
                    },
                    "assignment_message_id": "msg-0004",
                    "result_message_id": "msg-0005",
                    "contribution_message_id": "msg-0007",
                },
            ],
        )
        self.assertEqual(aggregate["audit_summary"]["ok"], True)

    def test_aggregate_output_is_deterministic_and_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            aggregate_path = output_dir / "aggregate-result.json"

            aggregate_local_flow(output_dir)
            first_bytes = aggregate_path.read_bytes()
            aggregate_local_flow(output_dir)
            second_bytes = aggregate_path.read_bytes()

        self.assertEqual(second_bytes, first_bytes)

    def test_audit_failure_happens_before_existing_aggregate_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            aggregate_path = output_dir / "aggregate-result.json"
            aggregate_path.write_text("previous aggregate\n", encoding="utf-8")
            receipts_path = output_dir / "receipts.json"
            receipts = _load_json(receipts_path)
            receipts["receipts"][0]["credited_units"] = 99
            _write_json(receipts_path, receipts)

            with self.assertRaises(FlowAuditError):
                aggregate_local_flow(output_dir)

            preserved = aggregate_path.read_text(encoding="utf-8")

        self.assertEqual(preserved, "previous aggregate\n")

    def test_invalid_and_zero_credit_receipts_are_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir), include_unsupported=True)
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))

            aggregate = build_local_flow_aggregate(output_dir)

        self.assertEqual(aggregate["counts"]["receipts"], 3)
        self.assertEqual(aggregate["counts"]["accepted_results"], 2)
        self.assertEqual(aggregate["counts"]["invalid_or_zero_credit_receipts"], 1)
        self.assertEqual(aggregate["validation_totals"]["invalid"], 1)
        self.assertEqual(aggregate["validation_totals"]["zero_credit"], 1)
        self.assertEqual(aggregate["validation_totals"]["failed_status"], 1)
        self.assertNotIn(
            "invalid-1",
            {entry["job_id"] for entry in aggregate["accepted_results"]},
        )

    def test_aggregate_path_override_writes_requested_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            override_path = Path(temp_dir) / "custom" / "aggregate.json"
            run_local_flow(str(manifest_path), str(output_dir))

            summary = aggregate_local_flow(output_dir, override_path)
            override_exists = override_path.exists()
            default_exists = (output_dir / "aggregate-result.json").exists()

        self.assertEqual(summary["aggregate_path"], str(override_path))
        self.assertTrue(override_exists)
        self.assertFalse(default_exists)

    def test_write_failure_does_not_leave_partial_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = _write_manifest(Path(temp_dir))
            output_dir = Path(temp_dir) / "flow"
            run_local_flow(str(manifest_path), str(output_dir))
            bad_path = Path(temp_dir) / "as-directory"
            bad_path.mkdir()

            with self.assertRaises(AggregationError):
                aggregate_local_flow(output_dir, bad_path)

            self.assertTrue(bad_path.is_dir())

    def test_acceptance_helpers_require_valid_positive_credit(self) -> None:
        accepted = _receipt(
            job_id="accepted-1",
            job_type="echo",
            node_id="local-node-a",
            credited_units=2,
            validation_valid=True,
            validation_reason="ok",
            result_status="completed",
        )
        invalid_positive = _receipt(
            job_id="invalid-positive",
            job_type="echo",
            node_id="local-node-a",
            credited_units=2,
            validation_valid=False,
            validation_reason="unsupported_job_type",
            result_status="failed",
        )
        valid_zero = _receipt(
            job_id="valid-zero",
            job_type="echo",
            node_id="local-node-a",
            credited_units=0,
            validation_valid=True,
            validation_reason="ok",
            result_status="completed",
        )

        self.assertTrue(_is_accepted(accepted))
        self.assertFalse(_is_accepted(invalid_positive))
        self.assertFalse(_is_accepted(valid_zero))
        self.assertEqual(
            _accepted_result(accepted),
            {
                "job_id": "accepted-1",
                "job_type": "echo",
                "node_id": "local-node-a",
                "result_status": "completed",
                "credited_units": 2,
                "validation_valid": True,
                "validation_reason": "ok",
                "output_summary": {"message": "accepted-1"},
                "assignment_message_id": "assign-accepted-1",
                "result_message_id": "result-accepted-1",
                "contribution_message_id": "contribution-accepted-1",
            },
        )

    def test_totals_helpers_count_fields_and_validation_reasons(self) -> None:
        receipts = [
            _receipt(
                job_id="echo-1",
                job_type="echo",
                node_id="local-node-b",
                credited_units=3,
                validation_valid=True,
                validation_reason="ok",
                result_status="completed",
            ),
            _receipt(
                job_id="stats-1",
                job_type="text_stats",
                node_id="local-node-a",
                credited_units=2,
                validation_valid=True,
                validation_reason="ok",
                result_status="completed",
            ),
            _receipt(
                job_id="echo-2",
                job_type="echo",
                node_id="local-node-a",
                credited_units=0,
                validation_valid=False,
                validation_reason="unsupported_job_type",
                result_status="failed",
            ),
        ]
        accepted_results = [
            _accepted_result(receipts[0]),
            _accepted_result(receipts[1]),
        ]

        self.assertEqual(
            _totals_by_field(accepted_results, "job_type"), {"echo": 3, "text_stats": 2}
        )
        self.assertEqual(
            _totals_by_field(accepted_results, "node_id"),
            {"local-node-a": 2, "local-node-b": 3},
        )
        self.assertEqual(
            _validation_totals(receipts),
            {
                "valid": 2,
                "invalid": 1,
                "zero_credit": 1,
                "failed_status": 1,
                "reasons": {"ok": 2, "unsupported_job_type": 1},
            },
        )

    def test_write_aggregate_document_rejects_invalid_document_shape(self) -> None:
        valid_document = {"version": 1, "counts": {}, "accepted_results": []}
        _validate_aggregate_document(valid_document)

        for invalid_document, message in [
            ({"version": True, "counts": {}, "accepted_results": []}, "version 1"),
            ({"version": 2, "counts": {}, "accepted_results": []}, "version 1"),
            ({"version": 1, "counts": {}, "accepted_results": {}}, "accepted_results"),
            ({"version": 1, "counts": [], "accepted_results": []}, "counts"),
        ]:
            with self.subTest(message=message):
                with self.assertRaises(AggregationError) as cm:
                    _validate_aggregate_document(invalid_document)
                self.assertIn(message, str(cm.exception))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "aggregate.json"
            with self.assertRaises(AggregationError):
                write_aggregate_document(output_path, {"version": 1, "counts": []})

            self.assertFalse(output_path.exists())


def _write_manifest(directory: Path, *, include_unsupported: bool = False) -> Path:
    jobs = [
        {
            "job_id": "echo-1",
            "job_type": "echo",
            "payload": {"message": "hello mesh"},
        },
        {
            "job_id": "text-stats-1",
            "job_type": "text_stats",
            "payload": {"text": "hello mesh\nhello node"},
        },
    ]
    if include_unsupported:
        jobs.append(
            {
                "job_id": "invalid-1",
                "job_type": "text_stats",
                "payload": {},
            }
        )
    manifest_path = directory / "local-batch.json"
    _write_json(
        manifest_path,
        {"version": 1, "nodes": ["local-node-a", "local-node-b"], "jobs": jobs},
    )
    return manifest_path


def _receipt(
    *,
    job_id: str,
    job_type: str,
    node_id: str,
    credited_units: int,
    validation_valid: bool,
    validation_reason: str,
    result_status: str,
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "job_type": job_type,
        "node_id": node_id,
        "result_status": result_status,
        "credited_units": credited_units,
        "validation": {"valid": validation_valid, "reason": validation_reason},
        "output_summary": {"message": job_id},
        "assignment_message_id": f"assign-{job_id}",
        "result_message_id": f"result-{job_id}",
        "contribution_message_id": f"contribution-{job_id}",
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, document: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    unittest.main()
