# Local Contribution Record Schema

Version 1 defines a small, local-first contribution record for attribution and later audit. The JSON Schema is `examples/schemas/contribution-record.schema.json`; the Python validator is `aethermesh_core.contribution_record.validate_contribution_record`.

This record is evidence metadata only. It does not award credits, calculate rewards, assert peer agreement, or claim consensus or decentralization.

## Required top-level fields

`schema_version`, `record_id`, `creator_node_id`, `contributor_node_id`, `created_at`, `work_type`, `job_type`, `capability`, and `contribution_summary` identify what was recorded and who created or performed the work. `result_hash_algorithm` is `sha256` and `result_hash` is the canonical `sha256:<digest>` for the completed result payload. `source` requires either a safe local source path or artifact reference.

`job_type` and `capability` are required when the record is created; they are not inferred from logs. `job_type` is one of the Phase 1 local work types: `echo`, `hash`, `basic_compute`, `schema_transform`, `keyword_extract`, `text_chunk`, `text_embed`, or `text_stats`. `capability` must be the matching local node manifest identifier (`work.<job_type>`). This preserves the capability used for the job alongside the validation receipt reference without asserting network eligibility.

`manifest_links`, `validation`, `lineage`, and `attribution` are always present alongside the result hash, so their empty or unavailable state is explicit. References that are not applicable use `null`; lineage lists use `[]`. This lets a minimal local prototype retain a deterministic result proof without inventing manifests or validation.

## Validation and lineage

`validation.status` is `unvalidated`, `passed`, or `failed`. Validator identity, receipt reference, and timestamp are optional when unavailable. A failed validation requires `failure_reason`; it preserves all contribution attribution and lineage rather than deleting the record.

`lineage` records parent contribution IDs, derived artifact IDs, input/output SHA-256 hashes, and optional deterministic reproduction notes. `manifest_links` can associate node, work, input, output, and validation manifests when they exist.

Use `validate_contribution_result_hash(record, result_document)` when loading local evidence to verify that the stored hash still matches the canonical result payload. A mismatch raises `ContributionRecordError`, so the record cannot be treated as validated evidence.

## Attribution

`attribution` records an `author_id`, whether that author is a `human` or `node`, its role, an optional declared tool or runtime, and a `manual` or `automatic` creation mode. These are attribution fields, not reward-accounting fields.

All local path and artifact references must be relative and must not contain absolute paths, parent traversal, backslashes, or URI schemes.

`examples/contributions/minimal-local-echo.json` is a valid minimal local record. `examples/contributions/failed-local-echo.json` demonstrates a failed validation that retains its manifest links, lineage, and attribution.
