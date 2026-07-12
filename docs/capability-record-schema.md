# Local Capability Record Schema

This is the version 1 schema for a local AetherMesh capability claim. `aethermesh_core.capability_record.bind_capability_record_to_local_node` copies a draft record and stamps it with the canonical `NodeIdentity.node_id`; `validate_capability_record` requires that same local node ID for comparison. Neither function writes artifacts, advertises to peers, discovers nodes, establishes consensus, or awards contribution credit.

A capability is trusted only when `validation.status` is `passed` and the record contains local receipt IDs. `unvalidated` is valid only as explicitly untrusted metadata and cannot carry receipt IDs.

Fields not defined by version 1 are rejected at the top level and inside its structured sections. New trust, networking, or reward claims therefore require an explicit schema revision rather than being silently accepted.

## Required fields

| Field | Type and rule |
| --- | --- |
| `schema_version` | Integer `1`. |
| `capability_id`, `node_id`, `creator_node_id` | Stable local identifiers: lowercase letter followed by 2–127 lowercase letters, digits, `.`, `_`, or `-`. `node_id` is required and must equal the active local `NodeIdentity.node_id` during validation. |
| `created_at`, `updated_at` | UTC timestamps in `YYYY-MM-DDTHH:MM:SSZ` form. |
| `metadata.name`, `metadata.description` | Non-empty strings. |
| `metadata.capability_type` | One of `model`, `tool`, `worker`, `runtime`. |
| `metadata.supported_input_formats`, `metadata.supported_output_formats` | Non-empty lists of non-empty strings. |
| `metadata.constraints` | Object describing local limits or assumptions. |
| `metadata.local_execution_requirements` | Non-empty list of non-empty strings. |
| `manifest_refs` | Non-empty list of safe local relative references backing the claim. |
| `validation.status` | One of `unvalidated`, `passed`, `failed`. |
| `validation.receipt_ids` | List of stable local receipt IDs. |
| `lineage.source_manifest_ref` | Safe local relative reference for the source manifest. |
| `contribution_attribution.creator_node_id` | Required and exactly equal to top-level `creator_node_id`. |
| `contribution_attribution.maintainer_node_id` | Stable local identifier. |
| `contribution_attribution.work_receipt_ids` | List of stable local work receipt IDs. |

A safe local reference is non-empty, relative, and cannot begin with `/` or `~`, contain `..`, or contain a URI scheme. This keeps records portable without treating a filesystem reference as a network location.

## Conditional validation fields

- `passed` requires one or more `receipt_ids`, `last_validated_at`, and `check_name`.
- `failed` requires `last_validated_at`, `check_name`, and a non-empty `failure_reason`. Receipt IDs remain optional because a failed local check may not produce a receipt.
- `unvalidated` requires an empty `receipt_ids` list. It must not be presented as trusted.

## Optional lineage fields

`lineage.prior_capability_id` links a replacement to an earlier capability record. `lineage.local_build_artifact_ref` links it to a local build artifact. Either may be omitted or `null` when not applicable. `source_manifest_ref` remains required in every record.

## Valid passed record

```json
{
  "schema_version": 1,
  "capability_id": "capability.echo-v1",
  "node_id": "node.local-01",
  "creator_node_id": "node.local-01",
  "created_at": "2026-07-11T12:00:00Z",
  "updated_at": "2026-07-11T12:05:00Z",
  "metadata": {
    "name": "Local echo worker",
    "description": "Returns an input message without remote execution.",
    "capability_type": "worker",
    "supported_input_formats": ["application/json"],
    "supported_output_formats": ["application/json"],
    "constraints": {"network_mode": "local-only-no-p2p"},
    "local_execution_requirements": ["python>=3.11"]
  },
  "manifest_refs": ["manifests/local-echo-worker.json"],
  "validation": {
    "status": "passed",
    "receipt_ids": ["receipt.echo-smoke-01"],
    "last_validated_at": "2026-07-11T12:05:00Z",
    "check_name": "echo-smoke-test"
  },
  "lineage": {
    "source_manifest_ref": "manifests/local-echo-worker.json",
    "prior_capability_id": null,
    "local_build_artifact_ref": "artifacts/echo-worker-v1.whl"
  },
  "contribution_attribution": {
    "creator_node_id": "node.local-01",
    "maintainer_node_id": "node.local-01",
    "work_receipt_ids": ["work.echo-0001"]
  }
}
```

## Valid unvalidated record

Set `validation.status` to `unvalidated` and `validation.receipt_ids` to `[]`; omit `last_validated_at`, `check_name`, and `failure_reason`. This remains a local claim, not a trusted or network-advertised capability.
