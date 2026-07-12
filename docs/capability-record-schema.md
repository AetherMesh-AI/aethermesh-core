# Local Capability Record Schema

This is the version 1 schema for a local AetherMesh capability claim. It is a validation-only Python contract exposed by `aethermesh_core.capability_record.validate_capability_record`; it does not write artifacts, advertise to peers, discover nodes, establish consensus, or award contribution credit.

A capability is trusted only when `validation.status` is `passed` and the record contains local receipt IDs. `unvalidated` is valid only as explicitly untrusted metadata and cannot carry receipt IDs.

Fields not defined by version 1 are rejected at the top level and inside its structured sections. New trust, networking, or reward claims therefore require an explicit schema revision rather than being silently accepted.

## Required fields

| Field | Type and rule |
| --- | --- |
| `schema_version` | Integer `1`. |
| `capability_id`, `node_id`, `creator_node_id` | Stable local identifiers: lowercase letter followed by 2–127 lowercase letters, digits, `.`, `_`, or `-`. `node_id` is the persisted local identity's `node_id` and identifies the node advertising this capability. |
| `capability_version` | Required Semantic Versioning 2.0 value for the capability contract, such as `1.0.0`; it is not release status, reputation, or reward value. |
| `created_at`, `updated_at` | UTC timestamps in `YYYY-MM-DDTHH:MM:SSZ` form. |
| `metadata.name`, `metadata.description` | Non-empty strings. `name` is a stable, human-readable description of the local function offered. |
| `metadata.type` | Required machine-checkable type: one of `model`, `tool`, `worker`, `runtime`. |
| `metadata.supported_input_formats`, `metadata.supported_output_formats` | Non-empty lists of non-empty strings. |
| `metadata.supported_input_schemas` | Non-empty list of local schema references. Each entry has `schema_ref`, Semantic Version `schema_version`, and content-addressed `sha256:` `schema_digest`. The referenced JSON Schema must be readable below the local schema root, use draft 2020-12, and declare the same `x-aethermesh-schema-version`. |
| `metadata.constraints` | Object describing local limits or assumptions. |
| `metadata.local_execution_requirements` | Non-empty list of non-empty strings. |
| `manifest_refs` | Non-empty list of safe local relative references backing the claim. |
| `validation.status` | One of `unvalidated`, `passed`, `failed`. |
| `validation.receipt_ids` | List of stable local receipt IDs. |
| `validation.receipt_evidence` | Required list aligned with `receipt_ids`; each receipt records its ID, advertised capability name and version, creator node ID, and source manifest reference. |
| `lineage.source_manifest_ref` | Safe local relative reference for the source manifest. |
| `contribution_attribution.creator_node_id` | Required and exactly equal to top-level `creator_node_id`. |
| `contribution_attribution.maintainer_node_id` | Stable local identifier. |
| `contribution_attribution.work_receipt_ids` | List of stable local work receipt IDs. |

A safe local reference is non-empty, relative, and cannot begin with `/` or `~`, contain `..`, or contain a URI scheme. This keeps records portable without treating a filesystem reference as a network location.

## Capability-version changes

Use Semantic Versioning for the capability interface or behavior only: increment the major version for incompatible contract changes, the minor version for backwards-compatible inputs, outputs, or behavior, and the patch version for compatible corrections. After a contract-affecting change, update the source manifest and rerun local validation so receipt evidence records the new version. Existing records without `capability_version` fail local validation and must be migrated with an explicit version and matching fresh receipt evidence.

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
  "capability_version": "1.0.0",
  "node_id": "node.local-01",
  "creator_node_id": "node.local-01",
  "created_at": "2026-07-11T12:00:00Z",
  "updated_at": "2026-07-11T12:05:00Z",
  "metadata": {
    "name": "Local echo worker",
    "description": "Returns an input message without remote execution.",
    "type": "worker",
    "supported_input_formats": ["application/json"],
    "supported_input_schemas": [{
      "schema_ref": "examples/schemas/local-echo-input.schema.json",
      "schema_version": "1.0.0",
      "schema_digest": "sha256:f25619d3f165bd8802258148a37ab97f62fee632354fd9c29765d253cefb4790"
    }],
    "supported_output_formats": ["application/json"],
    "constraints": {"network_mode": "local-only-no-p2p"},
    "local_execution_requirements": ["python>=3.11"]
  },
  "manifest_refs": ["manifests/local-echo-worker.json"],
  "validation": {
    "status": "passed",
    "receipt_ids": ["receipt.echo-smoke-01"],
    "receipt_evidence": [{
      "receipt_id": "receipt.echo-smoke-01",
      "capability_name": "Local echo worker",
      "capability_version": "1.0.0",
      "creator_node_id": "node.local-01",
      "manifest_ref": "manifests/local-echo-worker.json",
      "input_schema": {
        "schema_ref": "examples/schemas/local-echo-input.schema.json",
        "schema_version": "1.0.0",
        "schema_digest": "sha256:f25619d3f165bd8802258148a37ab97f62fee632354fd9c29765d253cefb4790"
      }
    }],
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

Set `validation.status` to `unvalidated`, `validation.receipt_ids` to `[]`, and `validation.receipt_evidence` to `[]`; omit `last_validated_at`, `check_name`, and `failure_reason`. This remains a local claim, not a trusted or network-advertised capability.

Validation requires the persisted identity's ID as `local_node_id`. The record is rejected unless its required `node_id` exactly matches that source of truth.
