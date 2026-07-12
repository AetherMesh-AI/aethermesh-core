# Local capability record schema

`capability-record.json` is a strict, versioned schema for a capability that one local AetherMesh prototype node can honestly describe. It is a local artifact contract, not a peer advertisement, registry entry, consensus claim, or proof that a capability is trusted.

Validate a loaded JSON object with `aethermesh_core.capability_record.validate_capability_record`. Version 1 rejects unknown fields so later routing does not accidentally treat display-only metadata as provenance.

## Required top-level fields

Every version-1 record has exactly these fields:

| Field | Meaning |
| --- | --- |
| `schema_version` | Integer `1`. |
| `capability_id` | Stable `local-capability-...` identifier. |
| `creator_node_id` | Non-empty stable local creator node ID. |
| `created_at`, `updated_at` | UTC ISO 8601 timestamps. |
| `metadata` | Capability description and local execution boundary. |
| `manifest_references` | Required local node/runtime/backing manifest references. |
| `validation` | Required validation state and evidence. |
| `lineage` | Required source-manifest and optional predecessor/build links. |
| `contribution_attribution` | Required creator, maintainer, and local work-receipt links. |

All manifest, lineage, and build references are safe relative local references: they cannot be absolute paths, parent traversal, or URLs. They may use a `#fragment` to address an item inside a local document. Receipt IDs must match `local-validation-receipt-...`.

## Metadata and manifest fields

`metadata` has exactly `name`, `description`, `capability_type`, `supported_input_formats`, `supported_output_formats`, `constraints`, and `local_execution_requirements`.

- `capability_type` is one of `model`, `tool`, `validator`, `worker`, or `work`.
- Input/output formats are non-empty string lists (for example, `application/json`).
- `constraints` is an object, including `{}` when no extra constraint is known.
- `local_execution_requirements` is `{ "execution_scope": "local-only", "requirements": [ ... ] }`; the requirements list is non-empty. No other execution scope is valid in this prototype.

`manifest_references` has exactly `node_manifest_ref`, `runtime_manifest_ref`, and non-empty `backing_manifest_refs`. The backing list holds the local model, tool, worker, or other implementation manifests supporting this capability.

## Validation, lineage, and attribution

`validation` has exactly `status`, `receipt_ids`, `last_validated_at`, `check_name`, and `failure_reason`.

- Allowed statuses: `unvalidated`, `passed`, `failed`, `stale`.
- `unvalidated` must use an empty `receipt_ids` list and `null` for the timestamp, check name, and failure reason. It is intentionally not trusted.
- `passed`, `failed`, and `stale` require at least one receipt ID, a UTC `last_validated_at`, and a non-empty check name.
- Only `failed` may contain a non-null failure reason, and it must be non-empty. `passed` and `stale` use `null`.

`lineage` has exactly `source_manifest_ref`, `prior_capability_id`, and `local_build_artifact_ref`. The source reference is required; the predecessor capability ID and build artifact reference are nullable when there is no predecessor or retained build artifact.

`contribution_attribution` has exactly `creator_node_id`, `maintainer_node_id`, and `local_work_receipt_ids`. Its creator must equal the top-level creator ID; maintainer is required; work receipts are a list and may be empty before the capability produces local work.

## Valid example

See [`examples/capability-record.json`](../examples/capability-record.json). It is validated by `tests/test_capability_record.py`.

## Unvalidated example

To represent a capability that has not been checked, retain every required provenance field and use:

```json
{
  "validation": {
    "status": "unvalidated",
    "receipt_ids": [],
    "last_validated_at": null,
    "check_name": null,
    "failure_reason": null
  }
}
```

This state cannot carry receipts or a successful-looking check name, so callers must not present it as trusted.
