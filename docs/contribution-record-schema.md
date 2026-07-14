# Local Contribution Record Schema

Version 1 defines a small, local-first contribution record for attribution and later audit. The JSON Schema is `examples/schemas/contribution-record.schema.json`; the Python validator is `aethermesh_core.contribution_record.validate_contribution_record`.

This record is evidence metadata only. It does not award credits, calculate rewards, assert peer agreement, or claim consensus or decentralization.

## Required top-level fields

`schema_version`, `record_id`, `job_id`, `creator_node_id`, `contributor_node_id`, `created_at`, `work_type`, and `contribution_summary` identify what was recorded and who created or performed the work. `job_id` uses the existing local job-envelope identifier format. `source` requires either a safe local source path or artifact reference.

`manifest_links`, `validation`, `lineage`, and `attribution` are always present so their empty or unavailable state is explicit. References that are not applicable use `null`; lineage lists use `[]`. This lets a minimal local prototype emit an honest `unvalidated` record without inventing manifests or validation.

## Validation and lineage

`validation.status` is `unvalidated`, `passed`, or `failed`. Validator identity, receipt reference, and timestamp are optional when unavailable. A failed validation requires `failure_reason`; it preserves all contribution attribution and lineage rather than deleting the record.

`lineage` records parent contribution IDs, derived artifact IDs, input/output SHA-256 hashes, and optional deterministic reproduction notes. `manifest_links` can associate node, work, input, output, and validation manifests when they exist.

## Attribution

`attribution` records an `author_id`, whether that author is a `human` or `node`, its role, an optional declared tool or runtime, and a `manual` or `automatic` creation mode. These are attribution fields, not reward-accounting fields.

All local path and artifact references must be relative and must not contain absolute paths, parent traversal, backslashes, or URI schemes.

`examples/contributions/minimal-local-echo.json` is a valid minimal local record. `examples/contributions/failed-local-echo.json` demonstrates a failed validation that retains its manifest links, lineage, and attribution.
