# Phase 1 Local API Schema Contract

`phase-1-api-schema-contract.json` is the versioned, human-readable contract for the Phase 1 domain API surface. It has one narrow purpose: make local prototype changes deliberate and reproducible. It does not add remote registration, result-upload, consensus, token, or reward APIs.

## Contract ownership and versioning

- `contract_version` uses semantic versioning. The per-artifact `version` fields documented there remain their existing integer schema versions.
- The contract lists the supported local node-startup boundary and the four provenance-sensitive operations: work submission, validation-receipt lookup, and contribution lookup.
- The FastAPI-generated `/openapi.json` document remains the published contract for the dashboard/status route inventory in `route_inventory`. It must contain that inventory; this avoids hand-copying generic status shapes while keeping route exposure testable.
- The local node boundary has no HTTP registration endpoint. Its response preserves a creator node ID, startup manifest, validation receipt, and lineage reference.
- `POST /api/jobs` requires `creator_node_id`, `job_type`, object `payload`, and `requested_validation_mode`. Lineage and attribution inputs are optional only because an origin may have no parent work or supplemental metadata; the accepted manifest always contains `lineage` and `contribution_attribution` objects.
- Validation result recording is intentionally internal to the deterministic local execution helper. `/api/validation-receipts` is read-only, and its response retains creator, manifest, lineage, validator, validation, and contribution-attribution evidence.

## Examples and local validation

The examples live beside this contract in `examples/api-schema/`:

- `local-node-startup.json`
- `local-job-submission.json`
- `local-validation-receipt-query.json`
- `local-contribution-lookup.json`

Run the deterministic validator from the repository root:

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_api_schema_contract.py --receipt validation-receipts/phase-1-step-36.json
```

It validates every static example, executes the documented local flow in a temporary runtime, verifies the runtime responses and the published OpenAPI route inventory, and writes a local JSON receipt. `validation-receipts/` is ignored generated evidence; remove it after inspection if it is not needed locally.

## Compatibility decisions

Schema changes are compatibility decisions, not incidental edits:

1. Add an optional field only with an updated contract and example.
2. For a breaking removal, rename, type change, or newly required field, increment the contract major version, add a short entry to `migration_notes`, and update every affected example and validator expectation.
3. Keep old artifact readers fail-closed when provenance fields (creator ID, manifest, validation receipt, lineage, or attribution) are missing or malformed.

There are no recorded breaking changes at contract version `1.0.0`.
