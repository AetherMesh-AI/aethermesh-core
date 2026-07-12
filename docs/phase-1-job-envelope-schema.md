# Phase 1 Job Envelope Schema

`examples/schemas/phase-1-job-envelope.schema.json` defines the local-only, version-1 envelope for one runnable job. It is an artifact contract, not a network protocol or scheduler request.

Serialize envelopes as UTF-8 JSON with lexicographically sorted object keys, compact separators, and one trailing newline. `aethermesh_core.job_envelope.canonical_job_envelope_json` provides that representation for fixtures and receipt inputs.

## Required fields

| Field | Purpose |
| --- | --- |
| `job_id` | Local job identifier. |
| `schema_version` | Integer `1`. |
| `creator_node_id` | Node that created the job. |
| `created_at` | UTC creation timestamp in `YYYY-MM-DDTHH:MM:SSZ` form. |
| `job_type` | Runnable local work type. |
| `input_manifest` | File references only; never inline large input payloads. |
| `expected_outputs` | Expected artifact paths and media types. |
| `validation_requirements` | Checks, receipt paths, and explicit pass criteria. |
| `lineage` | Parent job IDs, source manifests, and prior validation receipts. Empty arrays express root lineage. |
| `contribution` | Creator, known executor (or `null`), and produced artifact paths. |

Each `input_manifest.files` entry contains a safe relative `path`, a `sha256:<64 lowercase hex>` digest, byte `size_bytes`, and optional JSON-object `metadata`. Paths in manifests, expected outputs, receipts, lineage, and contribution are safe relative local paths: no absolute paths, URIs, or `..` segments.

Each validation check requires `check_id`, `receipt_path`, and a non-empty object `pass_criteria`. A receipt is expected at the declared local path only when the check has run; the envelope records the requirement and does not claim that validation already passed.

The contribution creator must match the envelope creator. `executor_node_id` is a node ID when known and `null` before local execution. `produced_artifacts` identifies artifact paths without assigning rewards, credits, or tokens.

## Local example

`examples/job-envelopes/local-echo.json` references the small input fixture at `examples/job-envelope-inputs/local-echo-input.json`, declares its digest and byte size, declares an expected local output and receipt, and uses empty root-lineage arrays. `tests/test_job_envelope.py` validates the example, required-field rejection, the explicit hash and local references, and deterministic serialization.
