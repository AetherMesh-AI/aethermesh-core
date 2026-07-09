"""Deterministic local work receipt documents for processed jobs."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from aethermesh_core.messages import MeshMessage
from aethermesh_core.node_service import ProcessedAssignment
from aethermesh_core.version_metadata import (
    capture_version_metadata,
    validate_version_metadata,
    version_metadata_ref,
)

RECEIPT_DOCUMENT_VERSION = 1
RUN_SOURCE = "run-local-flow"


class ReceiptPersistenceError(ValueError):
    """Raised when a local receipt document cannot be safely loaded or saved."""


def build_receipt_document(
    processed_assignments: list[ProcessedAssignment],
    *,
    existing_document: dict[str, Any] | None = None,
    artifact_mode: str | None = None,
    version_metadata: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Build a deterministic version 1 receipt document.

    Receipts are derived from already-produced local execution records. When an
    existing document is supplied, new receipts replace matching assignment ids
    and unrelated existing receipts are preserved so resumable ``run-local-flow``
    reruns do not erase prior audited work.
    """

    receipts_by_assignment_id: dict[str, dict[str, Any]] = {}
    metadata_by_ref: dict[str, dict[str, object]] = {}
    if existing_document is not None:
        _validate_receipt_document(existing_document)
        metadata_by_ref.update(_version_metadata_documents(existing_document))

    if existing_document is not None and not processed_assignments:
        metadata = validate_version_metadata(existing_document["version_metadata"])
    else:
        metadata = validate_version_metadata(
            version_metadata or capture_version_metadata()
        )
    metadata_ref = version_metadata_ref(metadata)
    metadata_by_ref[metadata_ref] = metadata
    if existing_document is not None:
        for receipt in existing_document["receipts"]:
            assignment_message_id = receipt["assignment_message_id"]
            receipts_by_assignment_id[assignment_message_id] = dict(receipt)

    for assignment in processed_assignments:
        receipt = _receipt_from_processed_assignment(assignment, metadata_ref)
        if artifact_mode == "ephemeral_test":
            receipt["artifact_mode"] = "ephemeral_test"
            receipt["ephemeral"] = True
        receipts_by_assignment_id[receipt["assignment_message_id"]] = receipt

    document: dict[str, Any] = {
        "version": RECEIPT_DOCUMENT_VERSION,
        "run_source": RUN_SOURCE,
        "version_metadata": metadata,
        "version_metadata_ref": metadata_ref,
        "version_metadata_by_ref": dict(sorted(metadata_by_ref.items())),
        "receipts": sorted(
            receipts_by_assignment_id.values(),
            key=lambda receipt: (
                str(receipt["job_id"]),
                str(receipt["node_id"]),
                str(receipt["assignment_message_id"]),
            ),
        ),
    }
    if artifact_mode == "ephemeral_test":
        document["artifact_mode"] = "ephemeral_test"
        document["ephemeral"] = True
    return document


def load_receipt_document_if_exists(path: str | Path) -> dict[str, Any] | None:
    """Load an existing receipt document, returning ``None`` for a missing file."""

    receipt_path = Path(path)
    if not receipt_path.exists():
        return None
    try:
        with receipt_path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ReceiptPersistenceError(f"receipt JSON is malformed: {exc.msg}") from exc
    except OSError as exc:
        raise ReceiptPersistenceError(f"could not read receipt file: {exc}") from exc
    if not isinstance(document, dict):
        raise ReceiptPersistenceError("receipt JSON must be an object")
    _validate_receipt_document(document)
    return document


def write_receipt_document(path: str | Path, document: dict[str, Any]) -> None:
    """Write a receipt document via temp-file then atomic replace."""

    _validate_receipt_document(document)
    receipt_path = Path(path)
    parent = receipt_path.parent
    temp_name: str | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{receipt_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, receipt_path)
    except (OSError, TypeError, ValueError) as exc:
        if temp_name is not None:
            _remove_temp_file(temp_name)
        raise ReceiptPersistenceError(f"could not write receipt file: {exc}") from exc


def _receipt_from_processed_assignment(
    assignment: ProcessedAssignment,
    metadata_ref: str,
) -> dict[str, Any]:
    result_message = _single_emitted_message(assignment, "job_result_reported")
    validation_message = _single_emitted_message(assignment, "job_validated")
    contribution_message = _single_emitted_message(assignment, "contribution_recorded")
    credited_units = assignment.contribution_record.contribution_units
    return {
        "job_id": assignment.job.job_id,
        "job_type": assignment.job.job_type,
        "node_id": assignment.result.node_id,
        "assignment_message_id": assignment.message_id,
        "correlation_id": assignment.correlation_id,
        "result_message_id": result_message.message_id,
        "validation_message_id": validation_message.message_id,
        "contribution_message_id": contribution_message.message_id,
        "result_status": assignment.result.status,
        "result_hash": assignment.contribution_record.result_hash,
        "validation": {
            "valid": assignment.validation.valid,
            "reason": assignment.validation.reason,
        },
        "version_metadata_ref": metadata_ref,
        "credited_units": credited_units,
        "output_summary": _output_summary(assignment.result.output),
    }


def _single_emitted_message(
    assignment: ProcessedAssignment, message_type: str
) -> MeshMessage:
    matches = [
        message
        for message in assignment.emitted_messages
        if message.message_type == message_type
    ]
    if len(matches) != 1:
        raise ValueError(
            f"processed assignment {assignment.message_id} must emit one {message_type} message"
        )
    return matches[0]


def _output_summary(output: Any) -> dict[str, Any]:
    if output is None:
        return {}
    if isinstance(output, dict):
        return _json_compatible_dict(output)
    if isinstance(output, str | int | float | bool):
        return {"value": output}
    if isinstance(output, list):
        return {"items": _json_compatible_list(output)}
    return {"value": str(output)}


def _json_compatible_dict(value: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in sorted(key for key in value if isinstance(key, str)):
        summary[key] = _json_compatible_value(value[key])
    return summary


def _json_compatible_list(value: list[Any]) -> list[Any]:
    return [_json_compatible_value(item) for item in value]


def _json_compatible_value(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return _json_compatible_dict(value)
    if isinstance(value, list):
        return _json_compatible_list(value)
    return str(value)


def _validate_receipt_document(document: dict[str, Any]) -> None:
    version = document.get("version")
    if version != RECEIPT_DOCUMENT_VERSION or isinstance(version, bool):
        raise ReceiptPersistenceError("receipt JSON must contain version 1")
    if document.get("run_source") != RUN_SOURCE:
        raise ReceiptPersistenceError(
            "receipt JSON field 'run_source' must be run-local-flow"
        )
    metadata_by_ref = _version_metadata_documents(document)
    expected_metadata_ref = version_metadata_ref(
        validate_version_metadata(document.get("version_metadata"))
    )
    document_metadata_ref = document.get("version_metadata_ref")
    if document_metadata_ref != expected_metadata_ref:
        raise ReceiptPersistenceError(
            "receipt JSON field 'version_metadata_ref' must match version_metadata"
        )
    _require_optional_artifact_mode(document, "receipt JSON")
    receipts = document.get("receipts")
    if not isinstance(receipts, list):
        raise ReceiptPersistenceError("receipt JSON field 'receipts' must be a list")
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            raise ReceiptPersistenceError(f"receipt entry {index} must be an object")
        for field_name in (
            "job_id",
            "job_type",
            "node_id",
            "assignment_message_id",
            "result_message_id",
            "validation_message_id",
            "result_status",
            "result_hash",
            "version_metadata_ref",
        ):
            if (
                not isinstance(receipt.get(field_name), str)
                or receipt[field_name] == ""
            ):
                raise ReceiptPersistenceError(
                    f"receipt entry {index} field '{field_name}' must be a non-empty string"
                )
        _require_result_hash(index, receipt["result_hash"])
        if receipt["version_metadata_ref"] not in metadata_by_ref:
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'version_metadata_ref' must reference version_metadata_by_ref"
            )
        correlation_id = receipt.get("correlation_id")
        if correlation_id is not None and not isinstance(correlation_id, str):
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'correlation_id' must be a string or null"
            )
        contribution_message_id = receipt.get("contribution_message_id")
        if contribution_message_id is not None and not isinstance(
            contribution_message_id, str
        ):
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'contribution_message_id' must be a string or null"
            )
        credited_units = receipt.get("credited_units")
        if not isinstance(credited_units, int) or isinstance(credited_units, bool):
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'credited_units' must be an integer"
            )
        validation = receipt.get("validation")
        if not isinstance(validation, dict):
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'validation' must be an object"
            )
        if not isinstance(validation.get("valid"), bool):
            raise ReceiptPersistenceError(
                f"receipt entry {index} validation field 'valid' must be a boolean"
            )
        if not isinstance(validation.get("reason"), str):
            raise ReceiptPersistenceError(
                f"receipt entry {index} validation field 'reason' must be a string"
            )
        if not isinstance(receipt.get("output_summary"), dict):
            raise ReceiptPersistenceError(
                f"receipt entry {index} field 'output_summary' must be an object"
            )
        _require_optional_artifact_mode(receipt, f"receipt entry {index}")


def _version_metadata_documents(
    document: dict[str, Any],
) -> dict[str, dict[str, object]]:
    """Return validated metadata documents keyed by their stable reference."""

    try:
        metadata = validate_version_metadata(document.get("version_metadata"))
    except ValueError as exc:
        raise ReceiptPersistenceError(f"receipt JSON {exc}") from exc
    metadata_ref = version_metadata_ref(metadata)
    raw_metadata_by_ref = document.get(
        "version_metadata_by_ref", {metadata_ref: metadata}
    )
    if not isinstance(raw_metadata_by_ref, dict):
        raise ReceiptPersistenceError(
            "receipt JSON field 'version_metadata_by_ref' must be an object when present"
        )
    metadata_by_ref: dict[str, dict[str, object]] = {}
    for raw_ref, raw_metadata in raw_metadata_by_ref.items():
        if not isinstance(raw_ref, str) or raw_ref == "":
            raise ReceiptPersistenceError(
                "receipt JSON field 'version_metadata_by_ref' keys must be non-empty strings"
            )
        try:
            validated_metadata = validate_version_metadata(raw_metadata)
        except ValueError as exc:
            raise ReceiptPersistenceError(f"receipt JSON {exc}") from exc
        expected_ref = version_metadata_ref(validated_metadata)
        if raw_ref != expected_ref:
            raise ReceiptPersistenceError(
                "receipt JSON field 'version_metadata_by_ref' keys must match their version metadata"
            )
        metadata_by_ref[raw_ref] = validated_metadata
    if metadata_ref not in metadata_by_ref:
        raise ReceiptPersistenceError(
            "receipt JSON field 'version_metadata_by_ref' must include version_metadata_ref"
        )
    return metadata_by_ref


def _require_optional_artifact_mode(document: dict[str, Any], context: str) -> None:
    artifact_mode = document.get("artifact_mode")
    if artifact_mode is None:
        return
    if artifact_mode != "ephemeral_test":
        raise ReceiptPersistenceError(
            f"{context} field 'artifact_mode' must be ephemeral_test when present"
        )
    if document.get("ephemeral") is not True:
        raise ReceiptPersistenceError(
            f"{context} field 'ephemeral' must be true for ephemeral_test artifacts"
        )


def _remove_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        return


def _require_result_hash(index: int, value: object) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ReceiptPersistenceError(
            f"receipt entry {index} field 'result_hash' must be a lowercase SHA-256 hex digest"
        )
    if value.lower() != value or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ReceiptPersistenceError(
            f"receipt entry {index} field 'result_hash' must be a lowercase SHA-256 hex digest"
        )
