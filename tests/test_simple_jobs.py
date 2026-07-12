import unittest

from aethermesh_core.simple_jobs import (
    SIMPLE_JOB_TYPES,
    SimpleJobError,
    execute_simple_job,
    parse_simple_job_manifest,
)


class SimpleJobExecutionTests(unittest.TestCase):
    def test_allowed_types_are_the_small_phase_one_set(self) -> None:
        self.assertEqual(
            SIMPLE_JOB_TYPES, ("echo", "hash", "compute", "schema_transform")
        )

    def test_echo_preserves_payload_and_full_success_lineage(self) -> None:
        manifest = self._manifest("echo", {"payload": "hello mesh"}, {"type": "string"})

        execution = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )

        self.assertEqual(execution.output, "hello mesh")
        self._assert_success(execution, manifest)

    def test_hash_receipt_hashes_are_stable(self) -> None:
        manifest = self._manifest(
            "hash",
            {"value": {"message": "hello mesh"}},
            {"type": "object", "fields": {"sha256": "string"}},
        )

        first = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )
        second = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )

        self.assertEqual(first.output, second.output)
        self.assertEqual(
            first.validation_receipt["input_hash"],
            second.validation_receipt["input_hash"],
        )
        self.assertEqual(
            first.validation_receipt["output_hash"],
            second.validation_receipt["output_hash"],
        )
        self.assertEqual(len(first.validation_receipt["input_hash"]), 64)
        self.assertEqual(len(first.validation_receipt["output_hash"]), 64)
        self._assert_success(first, manifest)

    def test_compute_is_deterministic_across_runs(self) -> None:
        manifest = self._manifest(
            "compute",
            {"operation": "multiply", "operands": [2, 3, 5]},
            {"type": "object", "fields": {"result": "number"}},
        )

        first = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )
        second = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:01:00+00:00",
        )

        self.assertEqual(first.output, {"result": 30})
        self.assertEqual(first.output, second.output)
        self._assert_success(first, manifest)

    def test_schema_transform_matches_declared_schema(self) -> None:
        schema = {"active": "boolean", "age": "integer", "name": "string"}
        manifest = self._manifest(
            "schema_transform",
            {
                "value": {"name": "Miyu", "age": 7, "active": True, "ignored": "value"},
                "schema": schema,
            },
            {"type": "object", "fields": schema},
        )

        execution = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )

        self.assertEqual(execution.output, {"active": True, "age": 7, "name": "Miyu"})
        self._assert_success(execution, manifest)

    def test_declared_shape_failure_has_receipt_but_no_contribution_credit(
        self,
    ) -> None:
        manifest = self._manifest("echo", {"payload": "hello mesh"}, {"type": "number"})

        execution = execute_simple_job(
            manifest,
            executor_node_id="node-executor",
            timestamp="2026-07-12T12:00:00+00:00",
        )

        self.assertFalse(execution.validation_receipt["valid"])
        self.assertEqual(execution.validation_receipt["status"], "failed")
        self.assertIsNone(execution.contribution_attribution)
        self.assertIn("manifest_ref", execution.lineage)
        default_timestamp_execution = execute_simple_job(
            manifest, executor_node_id="node-executor"
        )
        self.assertFalse(default_timestamp_execution.validation_receipt["valid"])

    def test_invalid_object_and_unknown_declared_shapes_do_not_receive_credit(
        self,
    ) -> None:
        for shape in ({"type": "object"}, {"type": "array"}):
            with self.subTest(shape=shape):
                manifest = self._manifest("echo", {"payload": "hello mesh"}, shape)
                execution = execute_simple_job(
                    manifest,
                    executor_node_id="node-executor",
                    timestamp="2026-07-12T12:00:00+00:00",
                )
                self.assertFalse(execution.validation_receipt["valid"])
                self.assertIsNone(execution.contribution_attribution)

    def test_unsupported_type_is_rejected_before_execution_or_credit(self) -> None:
        document = self._document("complex_ai", {}, {"type": "object", "fields": {}})

        with self.assertRaisesRegex(
            SimpleJobError, "unsupported simple job type: complex_ai"
        ):
            parse_simple_job_manifest(document)

    def test_required_manifest_fields_and_json_compatibility_are_enforced(self) -> None:
        valid = self._document("echo", {"payload": "hi"}, {"type": "string"})
        cases = [
            ([], "manifest must be an object"),
            (
                {key: value for key, value in valid.items() if key != "job_id"},
                "job_id must be a non-empty string",
            ),
            ({**valid, "inputs": []}, "inputs must be an object"),
            (
                {**valid, "expected_output_shape": []},
                "expected_output_shape must be an object",
            ),
            (
                {**valid, "attribution_metadata": {}},
                "attribution_metadata must not be empty",
            ),
            (
                {**valid, "inputs": {"payload": float("nan")}},
                "inputs must be JSON-compatible",
            ),
        ]
        for document, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(SimpleJobError, message):
                    parse_simple_job_manifest(document)

    def test_execution_input_errors_and_timestamp_are_rejected(self) -> None:
        cases = [
            ("echo", {}, {"type": "string"}, "echo inputs.payload must be a string"),
            (
                "hash",
                {},
                {"type": "object", "fields": {"sha256": "string"}},
                "hash inputs.value is required",
            ),
            (
                "compute",
                {"operation": "divide", "operands": [1]},
                {"type": "object", "fields": {"result": "number"}},
                "compute inputs.operation must be add or multiply",
            ),
            (
                "compute",
                {"operation": "add", "operands": [True]},
                {"type": "object", "fields": {"result": "number"}},
                "compute inputs.operands must contain only numbers",
            ),
            (
                "schema_transform",
                {"value": {}, "schema": {}},
                {"type": "object", "fields": {}},
                "schema_transform inputs.value and inputs.schema must be non-empty objects",
            ),
            (
                "schema_transform",
                {"value": {"name": 7}, "schema": {"name": "string"}},
                {"type": "object", "fields": {"name": "string"}},
                "schema_transform input does not match declared schema",
            ),
        ]
        for job_type, inputs, shape, message in cases:
            with self.subTest(message=message):
                manifest = self._manifest(job_type, inputs, shape)
                with self.assertRaisesRegex(SimpleJobError, message):
                    execute_simple_job(manifest, executor_node_id="node-executor")
        manifest = self._manifest("echo", {"payload": "hi"}, {"type": "string"})
        with self.assertRaisesRegex(
            SimpleJobError, "executor_node_id must be a non-empty string"
        ):
            execute_simple_job(manifest, executor_node_id=" ")
        with self.assertRaisesRegex(SimpleJobError, "timestamp must be ISO 8601"):
            execute_simple_job(
                manifest, executor_node_id="node-executor", timestamp="nope"
            )

    def _document(self, job_type, inputs, expected_output_shape):
        return {
            "job_id": "simple-job-1",
            "job_type": job_type,
            "inputs": inputs,
            "creator_node_id": "node-creator",
            "expected_output_shape": expected_output_shape,
            "attribution_metadata": {"source": "phase-1-test"},
        }

    def _manifest(self, job_type, inputs, expected_output_shape):
        return parse_simple_job_manifest(
            self._document(job_type, inputs, expected_output_shape)
        )

    def _assert_success(self, execution, manifest) -> None:
        self.assertTrue(execution.validation_receipt["valid"])
        self.assertEqual(execution.validation_receipt["status"], "passed")
        self.assertEqual(
            execution.validation_receipt["executor_node_id"], "node-executor"
        )
        self.assertEqual(execution.lineage["manifest_ref"], manifest.reference)
        self.assertEqual(
            set(execution.lineage),
            {"manifest_ref", "execution_attempt_id", "validation_receipt_ref"},
        )
        self.assertEqual(
            execution.contribution_attribution["creator_node_id"], "node-creator"
        )
        self.assertEqual(
            execution.contribution_attribution["executor_node_id"], "node-executor"
        )
        self.assertEqual(
            execution.contribution_attribution["attribution_metadata"],
            {"source": "phase-1-test"},
        )


if __name__ == "__main__":
    unittest.main()
