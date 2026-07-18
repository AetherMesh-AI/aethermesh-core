# Local Audit Event Schema

`aethermesh_core.local_audit_event` defines the small, stable v2 event format for a local JSONL audit log. It makes prototype actions traceable on one machine. It is not a production security log, peer protocol, blockchain, consensus record, reward ledger, or claim of decentralized finality.

## Storage and append-only rule

Store one event per UTF-8 newline-delimited JSON (JSONL) line, normally under the selected local AetherMesh home. `append_local_audit_event(path, event)` sanitizes and validates an event before opening the file in append mode; it never reads, replaces, edits, or deletes prior records. Consumers must treat an existing line as immutable evidence. Local filesystem access can still alter files outside this API, so this phase does not claim tamper resistance.

## Log-safety policy

Audit events preserve intentionally safe accountability fields: node and work IDs, manifest hashes and references, validation receipt IDs, lineage, and contribution attribution. They should contain hashes, IDs, safe relative references, and short summaries instead of raw request or result content.

`sanitize_local_audit_event` recursively replaces values under secret-bearing keys (`token`, `secret`, `password`, `privateKey`, `apiKey`, `seed`, `credential`, and `authorization`, including common compound forms) with `[REDACTED]`. Environment maps and raw request payload fields are also redacted. Absolute Unix, home-relative, and Windows paths become `local-path/<name>` labels; callers should supply a project-relative artifact reference when that reference is needed for validation. Do not place environment-variable dumps, private keys, credentials, full prompts, request payloads, or node-local configuration bodies in audit fields.

Sanitization is a persistence boundary, not a general secret detector. Callers must still prefer the compact schema and must not hide arbitrary secret text inside an unrelated identifier or summary field.

## Required fields

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | integer `2` | Event-format version. |
| `event_id` | non-empty string | Locally unique event identifier chosen by the caller. |
| `timestamp` | UTC timestamp (`YYYY-MM-DDTHH:MM:SSZ`) | Human-readable timestamp recorded by the caller. |
| `event_type` | enum | Prototype action listed below. |
| `actor_node_id` | non-empty string | Node performing or recording the action. |
| `creator_node_id` | non-empty string or `null` | Original creator node when known; `null` explicitly records that it is not known. |
| `local_run_id` | non-empty string | Local invocation/run that produced the event. |
| `event_sequence` | positive integer | Stable ordering position of the event within its local run. |

Version 2 adds `event_sequence` so events from separate JSONL files can be reconstructed in flow order without relying on equal-second timestamps. Existing version 1 lines remain immutable historical evidence; the current validator accepts newly produced version 2 events.

Supported event types are `node_initialized`, `manifest_created`, `work_submitted`, `job_submitted`, `validation_attempted`, `validation_result`, `validation_receipt_created`, `lineage_linked`, `contribution_record_updated`, `capability_advertised`, and `node.shutdown`.

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

## Job submission events

A `job_submitted` event is appended to `data/audit/job-submissions.jsonl` before a local submission is queued. It requires `job_id`, `local_node_id`, `manifest_ref`, a `manifest_hash` in `hashes`, `lineage_refs`, `validation_expectation`, `contribution_attribution`, and `attribution_metadata_hash`. The attribution map preserves the job and creator IDs plus a digest of the submitted metadata. The metadata body and input payload are deliberately not copied into the audit log, preventing prompts, credentials, and other large or private request data from being exposed there.

## Capability advertisement events

A `capability_advertised` event records one validated local startup-manifest claim after startup artifacts have been created. It requires `capability_advertisement_action` (`created`, `refreshed`, or `replaced`), `node_id`, `capability_id`, `manifest_ref`, `manifest_digest`, `advertisement_payload_digest`, `validation_status`, `validation_receipt_refs`, `lineage_refs`, and a string-only `contribution_attribution` map. The event stores digests and safe relative references rather than the full advertisement payload, so local runtime details are not copied into the audit log.

Startup appends one event per capability advertisement. Normal repeat startup is `refreshed`; explicit creator-identity reset is `replaced`; creating or upgrading a manifest advertisement is `created`. Rejected manifests fail before this event is appended.

## Validation receipt creation events

A `validation_receipt_created` event is appended to `data/audit/validation-receipt-creations.jsonl` only after its local validation receipt is durably created. It requires the work and manifest references, receipt ID and reference, accepted or rejected validation result, validator node and validator name, lineage references, and available contribution attribution. The lineage references include the submitted-work manifest and any parent references already present in that manifest. A rejected receipt remains explicitly `rejected`; this log does not imply a successful validation, production security, or network consensus. If this append fails, receipt creation fails clearly rather than reporting the job as complete.

## Contribution ledger update events

`record_validated_contribution` appends exactly one `contribution_record_updated` event for each local attribution attempt beside its contribution journal, unless an explicit audit path is supplied. The event records the creator as known, the contributing node as the actor, work ID, validation receipt ID, available manifest ID, lineage parent IDs, and contribution record ID. Its deterministic `event_id`/`local_run_id` is derived from compact identifiers and the local outcome, making repeated attempts traceable without copying a prompt, result payload, credentials, or other sensitive data.

`validation_status` is deliberately limited to `recorded`, `already_recorded`, `rejected`, or `validation_failed`. These are local evidence states only; they do not assert consensus, finality, reputation, or a reward value. A rejected receipt or invalid evidence still receives an audit event, while only an accepted passed receipt can enter the contribution journal.

## Examples

A minimal initialization event intentionally has no optional references:

```json
{"actor_node_id":"local-node-a","creator_node_id":"local-node-a","event_id":"audit-init-001","event_sequence":1,"event_type":"node_initialized","local_run_id":"run-001","schema_version":2,"timestamp":"2026-07-15T06:00:00Z"}
```

This validation-result event links local manifest, work, receipt, lineage, contribution attribution, and related artifacts without any network access:

```json
{"actor_node_id":"validator-local-a","contribution_attribution_ids":["local-contribution-work-001"],"creator_node_id":"creator-local-a","event_id":"audit-validation-001","event_sequence":2,"event_type":"validation_result","hashes":{"result_hash":"sha256:example"},"lineage_parent_ids":["work-parent-001"],"local_run_id":"run-001","manifest_id":"manifest-work-001","related_file_paths":["data/manifests/work-001.json","data/receipts/work-001.json"],"schema_version":2,"timestamp":"2026-07-15T06:01:00Z","validation_receipt_id":"receipt-work-001","work_id":"work-001"}
```

The examples are individual JSONL lines. They remain readable with ordinary JSON tooling, and a local script can parse each non-empty line with `json.loads` before calling `validate_local_audit_event`.
