# Local Capability Record Schema

Schema version `1` defines a persisted capability claim for the local AetherMesh prototype. It is a validation boundary for record shape, not proof of network discovery, consensus, routing eligibility, or trust. A record with `validation.status: "unvalidated"` must not claim evidence.

Use `validate_capability_record()` from `aethermesh_core.capability_record` before persisting or consuming a record. The validator rejects unknown fields so a version-1 consumer cannot silently reinterpret an unsupported claim.

## Required top-level fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | Exactly `1`. |
| `capability_id`, `creator_node_id` | string | Stable safe local identifiers: lowercase letter followed by lowercase letters, digits, or `-`. |
| `created_at`, `updated_at` | string | UTC timestamp in `YYYY-MM-DDTHH:MM:SSZ` form. |
| `metadata` | object | Required fields below. |
| `manifest_references` | object | At least one manifest backing the claim. |
| `validation` | object | Required explicit validation state below. |
| `lineage` | object | Required fields may be `null` when no predecessor exists. |
| `contribution_attribution` | object | Preserves creator, maintainer, and local work receipts. |

All references are relative local references. They cannot be absolute, URI-shaped, or traverse a parent directory.

## Metadata and manifests

`metadata` requires non-empty `name` and `description`, `capability_type`, non-empty `supported_input_formats` and `supported_output_formats`, plus `constraints` and `local_execution_requirements` string lists (either may be empty). Allowed `capability_type` values are `model`, `tool`, `worker`, and `runtime`.

`manifest_references` is a non-empty map whose keys are `node`, `runtime`, `model`, `tool`, or `worker`; each value is a safe relative local reference. Include every node, runtime, model, tool, or worker manifest that materially backs the capability.

## Validation, lineage, and attribution

`validation` requires `status`, `receipt_ids`, `last_validated_at`, `check_name`, and `failure_reason`. Allowed statuses are `unvalidated`, `pending`, `passed`, and `failed`. Receipt IDs must use the local form `local-validation-receipt-<safe-id>`.

- `unvalidated` requires an empty receipt list and `null` timestamp, check name, and failure reason. It is explicitly not trusted.
- `passed` requires at least one receipt plus non-null timestamp and check name.
- `failed` requires a non-null timestamp, check name, and failure reason; receipts may be empty when the failed check produced no receipt.
- `pending` may preserve prior local evidence while a new check is in progress.

`lineage` requires `source_manifest_ref`, `prior_capability_record_id`, and `local_build_artifact_ref`; each may be `null` when irrelevant. Non-null manifest/build values are safe local references, and a predecessor is a safe capability ID.

`contribution_attribution` requires `creator_node_id` (which must exactly equal the top-level creator), nullable `maintainer_node_id`, and `local_work_receipt_ids`. Receipt IDs use the same strict local form and are attribution evidence, not display-only labels.

## Valid example

[`examples/local-capability-record.json`](../examples/local-capability-record.json) is a complete passed local record. It has a local validation receipt but does not imply consensus or remote advertisement.

An unvalidated record changes only the `validation` object to:

```json
{
  "status": "unvalidated",
  "receipt_ids": [],
  "last_validated_at": null,
  "check_name": null,
  "failure_reason": null
}
```
