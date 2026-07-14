# Local Contribution Record Schema

Version 5 defines a small, local-first contribution record for attribution and later audit. The JSON Schema is `examples/schemas/contribution-record.schema.json`; the Python validator is `aethermesh_core.contribution_record.validate_contribution_record`.

Version 5 retains the canonical completed-result SHA-256 hash and its algorithm from version 4, and requires validation status history, contributor identity, and the declared creation mode. Earlier records remain identifiable by version and must be migrated explicitly rather than silently reinterpreted.

This record is evidence metadata only. It does not award credits, calculate rewards, assert peer agreement, or claim consensus or decentralization.

## Required top-level fields

`schema_version`, `record_id`, `job_id`, `validation_receipt_id`, `result_hash_algorithm`, `result_hash`, `creator_node_id`, `contributor_node_id`, `created_at`, `work_type`, `job_type`, `capability`, and `contribution_summary` identify what was recorded and who created or performed the work. `result_hash_algorithm` is `sha256`; `result_hash` is the algorithm-prefixed canonical hash of the linked completed result document. `job_type` must match `work_type`, and `capability` must be the corresponding registered Phase 1 runtime capability. `job_id` uses the existing local job-envelope identifier format. `source` requires either a safe local source path or artifact reference.

`created_at` is the required record-creation timestamp, written once as UTC RFC 3339 in `YYYY-MM-DDTHH:MM:SSZ` form. It is local audit evidence, not a global ordering, consensus, ranking, reward, or tokenomics signal. Readers and validation must preserve it rather than regenerate it.

## Ledger records

The local JSON `ContributionLedger` also writes `created_at` when `record()` creates a new record. Its clock is injectable for stable local tests. Existing timestamp-less ledger entries remain readable as historical records and are not assigned a timestamp during a read or rewrite.

`manifest_links`, `validation`, `lineage`, and `attribution` are always present so their empty or unavailable state is explicit. References that are not applicable use `null`; lineage lists use `[]`. The schema can still represent an explicitly `unvalidated` metadata state, while local evidence acceptance requires linked completed result and validation artifacts.

## Validation and lineage

`validation.status` is `unvalidated`, `passed`, or `failed`. Validator identity, receipt reference, and timestamp are optional when unavailable. A failed validation requires `failure_reason`; it preserves all contribution attribution and lineage rather than deleting the record.

`lineage` records parent contribution IDs, derived artifact IDs, input/output SHA-256 hashes, and optional deterministic reproduction notes. `manifest_links` can associate node, work, input, output, and validation manifests when they exist.

Local evidence validation recomputes the linked result document's canonical hash and requires that the contribution record, result payload, validation receipt, output lineage, creator/contributor identities, job, validation receipt ID, and work manifest all agree. A mismatch prevents the contribution from being treated as validated.

## Attribution

`attribution` records an `author_id`, whether that author is a `human` or `node`, its role, an optional declared tool or runtime, and a `manual` or `automatic` creation mode. These are attribution fields, not reward-accounting fields.

All local path and artifact references must be relative and must not contain absolute paths, parent traversal, backslashes, or URI schemes.

`examples/contributions/minimal-local-echo.json` is a valid minimal local record. `examples/contributions/failed-local-echo.json` demonstrates a failed validation that retains its manifest links, lineage, and attribution.
