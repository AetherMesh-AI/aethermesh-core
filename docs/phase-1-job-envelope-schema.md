# Phase 1 Job Envelope Schema

`examples/schemas/phase-1-job-envelope.schema.json` defines the local-only, version-1 envelope for one runnable job. It is an artifact contract, not a network protocol or scheduler request. Phase 1 has no separate task-record schema: each envelope is the single local runnable job (task) record.

Serialize envelopes as UTF-8 JSON with lexicographically sorted object keys, compact separators, and one trailing newline. `aethermesh_core.job_envelope.canonical_job_envelope_json` provides that representation for fixtures and receipt inputs.

## Required fields

| Field | Purpose |
| --- | --- |
| `job_id` | Stable local job identifier, separate from `creator_node_id`. |
| `schema_version` | Integer `1`. |
| `creator_node_id` | Node that created the job. |
| `created_at` | UTC creation timestamp in `YYYY-MM-DDTHH:MM:SSZ` form. It is set when the local record is created and remains unchanged during validation, retries, reporting, and export; it is not proof of global ordering or network consensus. |
| `job_type` | Required local worker capability: one of `echo`, `keyword_extract`, `text_chunk`, `text_embed`, `text_retrieve`, or `text_stats`. |
| `input_manifest` | File references only; never inline large input payloads. |
| `expected_outputs` | Expected artifact paths and media types. |
| `validation_requirements` | Checks, receipt paths, and explicit pass criteria. |
| `lineage` | Parent job IDs, source manifests, and prior validation receipts. Empty arrays express root lineage. |
| `contribution` | Creator, known executor (or `null`), and produced artifact paths. |

Each `input_manifest.files` entry contains a safe relative `path`, a `sha256:<64 lowercase hex>` digest, byte `size_bytes`, and optional JSON-object `metadata`. Paths in manifests, expected outputs, receipts, lineage, and contribution are safe relative local paths: no absolute paths, URIs, or `..` segments.

Each validation check requires `check_id`, `receipt_path`, and a non-empty object `pass_criteria`. A receipt is expected at the declared local path only when the check has run; the envelope records the requirement and does not claim that validation already passed.

`job_type` is the explicit target capability for local routing. Validators reject missing, empty, and unsupported values before execution; the local scheduler assigns the job only to an available node that declares the same capability.

`job_id` is generated before work starts and remains immutable for its lifetime. Accepted local-first formats are a lowercase local ID (the runtime generates `local-job-` plus a UUID-style hexadecimal suffix) or a deterministic `sha256:<64 lowercase hex>` content ID. Whitespace, paths, uppercase characters, and other malformed values are rejected; an active manifest cannot reuse an ID. Task/result records, validation receipts, manifests, lineage, and contribution attribution preserve the same ID, while `creator_node_id` remains separate authorship metadata.

The contribution creator must match the envelope creator. `executor_node_id` is a node ID when known and `null` before local execution. `produced_artifacts` identifies artifact paths without assigning rewards, credits, or tokens.

## Local example

`examples/job-envelopes/local-echo.json` references the small input fixture at `examples/job-envelope-inputs/local-echo-input.json`, declares its digest and byte size, declares an expected local output and receipt, and uses empty root-lineage arrays. `tests/test_job_envelope.py` validates the example, required-field rejection, the explicit hash and local references, and deterministic serialization.
