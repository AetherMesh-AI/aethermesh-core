# Local Audit Event Schema

`aethermesh_core.local_audit_event` defines the small, stable v1 event format for a local JSONL audit log. It makes prototype actions traceable on one machine. It is not a production security log, peer protocol, blockchain, consensus record, reward ledger, or claim of decentralized finality.

## Storage and append-only rule

Store one event per UTF-8 newline-delimited JSON (JSONL) line, normally under the selected local AetherMesh home. `append_local_audit_event(path, event)` validates an event and opens the file only in append mode; it never reads, replaces, edits, or deletes prior records. Consumers must treat an existing line as immutable evidence. Local filesystem access can still alter files outside this API, so this phase does not claim tamper resistance.

## Required fields

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | integer `1` | Event-format version. |
| `event_id` | non-empty string | Locally unique event identifier chosen by the caller. |
| `timestamp` | UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Human-readable timestamp recorded by the caller. |
| `event_type` | enum | Prototype action listed below. |
| `actor_node_id` | non-empty string | Node performing or recording the action. |
| `creator_node_id` | non-empty string or `null` | Original creator node when known; `null` explicitly records that it is not known. |
| `local_run_id` | non-empty string | Local invocation/run that produced the event. |

Supported event types are `node_initialized`, `manifest_created`, `work_submitted`, `validation_attempted`, `validation_result`, `lineage_linked`, and `contribution_record_updated`.

## Optional references

Omit optional fields when they do not apply. Their absence is valid and has no effect on unrelated events.

| Field | Type | Meaning |
| --- | --- | --- |
| `manifest_id` | non-empty string | Manifest reference. |
| `work_id` | non-empty string | Local work/job reference. |
| `validation_receipt_id` | non-empty string | Local validation receipt reference. |
| `lineage_parent_ids` | array of non-empty strings | Parent lineage references; an empty array is explicit root lineage. |
| `contribution_attribution_ids` | array of non-empty strings | Contribution attribution references. |
| `related_file_paths` | array of safe relative paths | Local supporting artifact paths; absolute and parent-traversal paths are rejected. |
| `hashes` | object of non-empty string pairs | Hashes already produced by local work or validation. |
| `signatures` | object of non-empty string pairs | Signatures already available locally. |

Hashes and signatures are optional. This format neither creates nor requires them unless existing local validation already produces them.

## Examples

A minimal initialization event intentionally has no optional references:

```json
{"actor_node_id":"local-node-a","creator_node_id":"local-node-a","event_id":"audit-init-001","event_type":"node_initialized","local_run_id":"run-001","schema_version":1,"timestamp":"2026-07-15T06:00:00Z"}
```

This validation-result event links local manifest, work, receipt, lineage, contribution attribution, and related artifacts without any network access:

```json
{"actor_node_id":"validator-local-a","contribution_attribution_ids":["local-contribution-work-001"],"creator_node_id":"creator-local-a","event_id":"audit-validation-001","event_type":"validation_result","hashes":{"result_hash":"sha256:example"},"lineage_parent_ids":["work-parent-001"],"local_run_id":"run-001","manifest_id":"manifest-work-001","related_file_paths":["data/manifests/work-001.json","data/receipts/work-001.json"],"schema_version":1,"timestamp":"2026-07-15T06:01:00Z","validation_receipt_id":"receipt-work-001","work_id":"work-001"}
```

The examples are individual JSONL lines. They remain readable with ordinary JSON tooling, and a local script can parse each non-empty line with `json.loads` before calling `validate_local_audit_event`.
