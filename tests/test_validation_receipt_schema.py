import copy
import json
import os
import unittest
from importlib import metadata
from pathlib import Path
from unittest.mock import patch

from aethermesh_core.result_hash import (
    canonical_result_document_hash,
    validate_validation_receipt_result_hash,
)
from aethermesh_core.validation_receipt_schema import (
    ValidationReceiptSchemaError,
    canonical_validation_receipt_hash,
    capture_validator_software_metadata,
    validation_receipt_id,
    validate_validation_receipt_document,
)


class ValidationReceiptSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        examples = root / "examples" / "validation-receipts"
        self.passing = json.loads(
            (examples / "local-echo-pass.json").read_text("utf-8")
        )
        self.failing = json.loads(
            (examples / "local-echo-fail.json").read_text("utf-8")
        )
        results = root / "examples" / "job-results"
        self.success_result = json.loads(
            (results / "local-echo-success.json").read_text("utf-8")
        )
        self.failed_result = json.loads(
            (results / "local-echo-failed.json").read_text("utf-8")
        )

    def test_passing_and_failing_examples_validate(self) -> None:
        self.assertIs(validate_validation_receipt_document(self.passing), self.passing)
        self.assertIs(validate_validation_receipt_document(self.failing), self.failing)
        self.assertEqual(self.passing["validation_status"], "pass")
        self.assertEqual(self.failing["validation_status"], "fail")
        self.assertEqual(self.passing["status"], "accepted")
        self.assertEqual(self.failing["status"], "rejected")
        self.assertEqual(
            self.failing["rejection_reason"],
            "output did not match deterministic echo expectation",
        )
        self.assertEqual(
            self.failing["lineage"]["prior_receipt_ids"],
            [self.passing["receipt_id"]],
        )
        validate_validation_receipt_result_hash(
            self.passing, canonical_result_document_hash(self.success_result)
        )
        validate_validation_receipt_result_hash(
            self.failing, canonical_result_document_hash(self.failed_result)
        )

    def test_capture_validator_software_uses_explicit_unknown_for_unsafe_builds(
        self,
    ) -> None:
        with (
            patch(
                "aethermesh_core.validation_receipt_schema.metadata.version",
                side_effect=metadata.PackageNotFoundError,
            ),
            patch.dict(os.environ, {"AETHERMESH_BUILD_ID": "/private/build"}),
        ):
            captured = capture_validator_software_metadata(
                validator_name="deterministic_fixture_replay", receipt_schema_version=6
            )

        self.assertEqual(captured["validator_build_identifier"], "unknown")
        self.assertEqual(captured["receipt_schema_version"], 6)

    def test_required_fields_and_unknown_fields_are_rejected(self) -> None:
        missing = copy.deepcopy(self.passing)
        missing.pop("job_id")
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "missing: job_id"):
            validate_validation_receipt_document(missing)

        missing_method = copy.deepcopy(self.passing)
        missing_method.pop("validation_method")
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "missing: validation_method"
        ):
            validate_validation_receipt_document(missing_method)

        missing_validator_software = copy.deepcopy(self.passing)
        missing_validator_software.pop("validator_software")
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "missing: validator_software"
        ):
            validate_validation_receipt_document(missing_validator_software)

        missing_timestamp = copy.deepcopy(self.passing)
        missing_timestamp.pop("validated_at")
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "missing: validated_at"
        ):
            validate_validation_receipt_document(missing_timestamp)

        malformed_timestamp = copy.deepcopy(self.passing)
        malformed_timestamp["validated_at"] = "2026-07-13T12:00:00+00:00"
        malformed_timestamp["receipt_hash"] = canonical_validation_receipt_hash(
            malformed_timestamp
        )
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "validated_at must be a UTC timestamp"
        ):
            validate_validation_receipt_document(malformed_timestamp)

        blank = copy.deepcopy(self.passing)
        blank["job_id"] = ""
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "job_id must be a non-empty identifier"
        ):
            validate_validation_receipt_document(blank)

        unknown = copy.deepcopy(self.passing)
        unknown["unreviewed_critical_field"] = "not silently accepted"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "unsupported fields"):
            validate_validation_receipt_document(unknown)

    def test_validation_statuses_map_to_explicit_receipt_statuses(self) -> None:
        for state, status in (
            ("pass", "accepted"),
            ("fail", "rejected"),
            ("error", "rejected"),
            ("skipped", "rejected"),
        ):
            with self.subTest(state=state):
                receipt = copy.deepcopy(self.passing)
                receipt["validation_status"] = state
                receipt["status"] = status
                receipt["rejection_reason"] = (
                    None if status == "accepted" else "required validation did not pass"
                )
                receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
                self.assertIs(validate_validation_receipt_document(receipt), receipt)

    def test_invalid_or_mismatched_receipt_status_is_rejected(self) -> None:
        cases = (
            ("pending", None, "must be accepted or rejected"),
            ("accepted", "unexpected", "must be null"),
            ("rejected", "required validation failed", "does not match"),
        )
        for status, rejection_reason, error in cases:
            with self.subTest(status=status):
                receipt = copy.deepcopy(self.passing)
                receipt["status"] = status
                receipt["rejection_reason"] = rejection_reason
                receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
                with self.assertRaisesRegex(ValidationReceiptSchemaError, error):
                    validate_validation_receipt_document(receipt)

        receipt = copy.deepcopy(self.failing)
        receipt["rejection_reason"] = None
        receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "rejection_reason"):
            validate_validation_receipt_document(receipt)

    def test_identical_local_evidence_has_stable_id_and_hash(self) -> None:
        first = copy.deepcopy(self.passing)
        second = copy.deepcopy(self.passing)
        second["created_at"] = "2026-07-13T12:01:00.000000Z"
        second["validated_at"] = "2026-07-13T12:02:00.000000Z"
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(first["receipt_id"], validation_receipt_id(first["work_id"]))
        self.assertEqual(
            canonical_validation_receipt_hash(first),
            canonical_validation_receipt_hash(second),
        )
        self.assertEqual(
            first["receipt_hash"], canonical_validation_receipt_hash(first)
        )

    def test_receipt_id_must_be_derived_from_work_id(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["receipt_id"] = "local-validation-receipt-unrelated-work"
        receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "match its work_id"):
            validate_validation_receipt_document(receipt)

    def test_job_id_must_match_work_id(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["job_id"] = "unrelated-job"
        receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "match its work_id"):
            validate_validation_receipt_document(receipt)

    def test_hash_mismatch_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["evidence"]["reason"] = "changed after hashing"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "does not match"):
            validate_validation_receipt_document(receipt)

    def test_validator_software_metadata_is_hash_bound_to_work_lineage(self) -> None:
        receipt = copy.deepcopy(self.failing)
        receipt["validator_software"]["validator_version"] = "changed-after-validation"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "receipt_hash"):
            validate_validation_receipt_document(receipt)

    def test_types_hashes_and_json_compatibility_are_strict(self) -> None:
        for field, value in (("schema_version", 5.0), ("validation_status", [])):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[field] = value
                with self.assertRaises(ValidationReceiptSchemaError):
                    validate_validation_receipt_document(receipt)

        old_version = copy.deepcopy(self.passing)
        old_version["schema_version"] = 5
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "must be integer 6"):
            validate_validation_receipt_document(old_version)

        receipt = copy.deepcopy(self.passing)
        receipt["lineage"]["input_hashes"] = ["sha256:not-a-digest"]
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "content-addressed"):
            validate_validation_receipt_document(receipt)

        for result_hash in (None, "c" * 64, "sha256:not-a-digest"):
            with self.subTest(result_hash=result_hash):
                receipt = copy.deepcopy(self.passing)
                receipt["result_hash"] = result_hash
                with self.assertRaisesRegex(
                    ValidationReceiptSchemaError, "SHA-256 digest"
                ):
                    validate_validation_receipt_document(receipt)

        receipt = copy.deepcopy(self.passing)
        receipt["not_json"] = {float("nan")}
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "JSON-compatible"):
            canonical_validation_receipt_hash(receipt)

    def test_local_references_cannot_leak_machine_paths(self) -> None:
        cases = (
            ("lineage", "source_manifest_refs", "/Users/example/private.json"),
            ("contribution", "contribution_manifest_ref", "../private.json"),
            ("evidence", "log_path", "C:\\Users\\example\\private.log"),
            ("evidence", "artifact_path", "https://example.test/result.json"),
        )
        for block, field, value in cases:
            with self.subTest(block=block, field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[block][field] = [value] if block == "lineage" else value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "relative"):
                    validate_validation_receipt_document(receipt)

    def test_reason_is_required_validation_evidence(self) -> None:
        for value in (None, ""):
            with self.subTest(value=value):
                receipt = copy.deepcopy(self.passing)
                receipt["evidence"]["reason"] = value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "non-empty"):
                    validate_validation_receipt_document(receipt)

    def test_next_local_action_is_required_validation_evidence(self) -> None:
        for value in (None, ""):
            with self.subTest(value=value):
                receipt = copy.deepcopy(self.failing)
                receipt["evidence"]["next_local_action"] = value
                receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
                with self.assertRaisesRegex(
                    ValidationReceiptSchemaError, "next_local_action"
                ):
                    validate_validation_receipt_document(receipt)

    def test_lineage_and_attribution_ids_reject_whitespace(self) -> None:
        nullable = copy.deepcopy(self.passing)
        nullable["contribution"]["submitter_id"] = None
        nullable["receipt_hash"] = canonical_validation_receipt_hash(nullable)
        self.assertIs(validate_validation_receipt_document(nullable), nullable)

        cases = (
            ("lineage", "parent_work_ids", ["not an id"]),
            ("lineage", "prior_receipt_ids", ["receipt\nleak"]),
            ("contribution", "submitter_id", "/Users/example/private id"),
            ("contribution", "claimed_role", "validator\nsecret"),
        )
        for block, field, value in cases:
            with self.subTest(block=block, field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[block][field] = value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "identifier"):
                    validate_validation_receipt_document(receipt)
