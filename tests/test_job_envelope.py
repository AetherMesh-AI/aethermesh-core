import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any

from aethermesh_core.job_envelope import (
    JobEnvelopeError,
    canonical_job_envelope_json,
    validate_job_envelope,
)


class JobEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.example_path = self.root / "examples/job-envelopes/local-echo.json"
        self.envelope = json.loads(self.example_path.read_text(encoding="utf-8"))

    def test_example_validates_against_the_phase_1_contract(self) -> None:
        self.assertIs(validate_job_envelope(self.envelope), self.envelope)
        input_file = self.root / self.envelope["input_manifest"]["files"][0]["path"]
        self.assertEqual(
            self.envelope["input_manifest"]["files"][0]["size_bytes"],
            input_file.stat().st_size,
        )
        self.assertEqual(
            self.envelope["input_manifest"]["files"][0]["sha256"],
            f"sha256:{hashlib.sha256(input_file.read_bytes()).hexdigest()}",
        )

    def test_schema_declares_the_same_required_fields_as_the_validator(self) -> None:
        schema = json.loads(
            (self.root / "examples/schemas/phase-1-job-envelope.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(set(schema["required"]), set(self.envelope))
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("created_at", schema["required"])
        created_at_schema = schema["properties"]["created_at"]
        self.assertEqual(created_at_schema["format"], "date-time")
        self.assertIsNotNone(
            re.fullmatch(created_at_schema["pattern"], self.envelope["created_at"])
        )
        self.assertIsNone(
            re.fullmatch(created_at_schema["pattern"], "2026-07-12T12:00:00+00:00")
        )
        self.assertEqual(
            schema["properties"]["job_type"]["enum"],
            [
                "echo",
                "keyword_extract",
                "text_chunk",
                "text_embed",
                "text_retrieve",
                "text_stats",
            ],
        )
        self.assertIn(
            "sha256",
            schema["properties"]["input_manifest"]["properties"]["files"]["items"][
                "required"
            ],
        )
        self.assertIn(
            "receipt_path",
            schema["properties"]["validation_requirements"]["properties"]["checks"][
                "items"
            ]["required"],
        )
        path_pattern = schema["properties"]["input_manifest"]["properties"]["files"][
            "items"
        ]["properties"]["path"]["pattern"]
        self.assertIsNotNone(re.fullmatch(path_pattern, "inputs/local.json"))
        for unsafe_path in ("/private/input.json", "../input.json", "C:\\input.json"):
            self.assertIsNone(re.fullmatch(path_pattern, unsafe_path))
        schema_text = json.dumps(schema).lower()
        for excluded_term in ("token", "dashboard", "frontier", "mixture-of-experts"):
            with self.subTest(excluded_term=excluded_term):
                self.assertNotIn(excluded_term, schema_text)

    def test_each_required_field_is_rejected_when_missing(self) -> None:
        for field in self.envelope:
            with self.subTest(field=field):
                document = copy.deepcopy(self.envelope)
                document.pop(field)
                with self.assertRaisesRegex(JobEnvelopeError, f"missing: {field}"):
                    validate_job_envelope(document)

    def test_canonical_serialization_is_deterministic(self) -> None:
        canonical = canonical_job_envelope_json(self.envelope)

        self.assertEqual(canonical, canonical_job_envelope_json(json.loads(canonical)))
        self.assertTrue(canonical.endswith("\n"))
        self.assertLess(
            canonical.index('"contribution"'), canonical.index('"created_at"')
        )

    def test_job_id_rejects_malformed_values_and_accepts_content_id(self) -> None:
        for job_id in ("has spaces", "../job", "UPPERCASE", "sha256:bad"):
            with self.subTest(job_id=job_id):
                document = copy.deepcopy(self.envelope)
                document["job_id"] = job_id
                with self.assertRaisesRegex(
                    JobEnvelopeError, "job_id must be a local ID"
                ):
                    validate_job_envelope(document)
        document = copy.deepcopy(self.envelope)
        document["job_id"] = "sha256:" + "a" * 64
        self.assertIs(validate_job_envelope(document), document)

    def test_job_type_requires_a_supported_local_capability(self) -> None:
        for job_type, message in (
            ("", "non-empty string"),
            ("future_job", "must be one of"),
        ):
            with self.subTest(job_type=job_type):
                document = copy.deepcopy(self.envelope)
                document["job_type"] = job_type
                with self.assertRaisesRegex(JobEnvelopeError, message):
                    validate_job_envelope(document)

    def test_explicit_lineage_receipts_and_contribution_artifacts_are_accepted(
        self,
    ) -> None:
        document = copy.deepcopy(self.envelope)
        document["lineage"] = {
            "parent_job_ids": ["local-parent-001"],
            "source_manifests": ["examples/manifests/parent.json"],
            "prior_validation_receipts": ["examples/receipts/parent.json"],
        }
        document["contribution"]["executor_node_id"] = "node.local-02"

        self.assertIs(validate_job_envelope(document), document)

    def test_rejects_invalid_local_references_and_attribution(self) -> None:
        cases = [
            (
                "input_manifest.files[0].path",
                "/private/input.json",
                "safe relative paths",
            ),
            ("input_manifest.files[0].sha256", "sha256:bad", "sha256 digest"),
            (
                "validation_requirements.checks[0].receipt_path",
                "https://example.test/receipt",
                "safe relative paths",
            ),
            ("lineage.source_manifests", ["../parent.json"], "safe relative paths"),
            ("lineage.source_manifests", ["C:\\parent.json"], "safe relative paths"),
            ("contribution.creator_node_id", "node.other-01", "must match"),
            (
                "contribution.produced_artifacts",
                ["other/result.json"],
                "declared in expected_outputs",
            ),
        ]
        for path, value, message in cases:
            with self.subTest(path=path):
                document = copy.deepcopy(self.envelope)
                self._set(document, path, value)
                with self.assertRaisesRegex(JobEnvelopeError, message):
                    validate_job_envelope(document)

    def test_rejects_wrong_types_and_unknown_fields(self) -> None:
        cases = [
            ("schema_version", True, "integer 1"),
            ("created_at", "2026-07-12", "UTC timestamp"),
            ("input_manifest.files", [], "non-empty list"),
            ("input_manifest.files[0].size_bytes", -1, "non-negative integer"),
            ("expected_outputs.artifacts", [], "non-empty list"),
            ("validation_requirements.checks[0].pass_criteria", {}, "non-empty object"),
            ("lineage.parent_job_ids", "local-parent-001", "must be a list"),
            ("contribution.executor_node_id", "", "non-empty string or null"),
            ("contribution.produced_artifacts", "result.json", "must be a list"),
        ]
        for path, value, message in cases:
            with self.subTest(path=path):
                document = copy.deepcopy(self.envelope)
                self._set(document, path, value)
                with self.assertRaisesRegex(JobEnvelopeError, message):
                    validate_job_envelope(document)

        document = copy.deepcopy(self.envelope)
        document["future"] = True
        with self.assertRaisesRegex(JobEnvelopeError, "unsupported: future"):
            validate_job_envelope(document)

    @staticmethod
    def _set(document: dict[str, Any], path: str, value: object) -> None:
        current: Any = document
        for part in path.split(".")[:-1]:
            name, separator, index = part.partition("[")
            if name:
                current = current[name]
            if separator:
                current = current[int(index[:-1])]
        name, separator, index = path.split(".")[-1].partition("[")
        if separator:
            current[name][int(index[:-1])] = value
        else:
            current[name] = value


if __name__ == "__main__":
    unittest.main()
