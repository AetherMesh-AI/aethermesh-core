# Phase 1 API Schema Stability

The versioned machine-readable contract is `docs/phase-1-local-api-contract.json`. It documents the supported local runtime and localhost HTTP boundaries; it deliberately does not describe a remote node-registration, manifest-upload, receipt-writing, or peer-network API.

## Compatibility rule

`contract_version` is currently `1`. Additive optional fields may remain at version 1. Removing or renaming required fields, changing a field type or meaning, or changing a stable status/error value is breaking: increment `contract_version`, add a dated migration note here, and update every example in the contract before code lands.

The `creator_node_id` is required for job submissions and is copied into contribution attribution. Submission manifests always retain their version, manifest type, creator, lineage object, and contribution-attribution object. Validation receipt lookup records retain creator, manifest, lineage, validator, validation evidence, and contribution-attribution fields. A caller may omit optional `lineage_parent_refs` or `attribution_metadata`, but the persisted submission still contains `lineage.parent_refs` and `contribution_attribution` objects so provenance has a stable shape.

## Local examples

The validator exercises examples for:

- local node create/load response (creator identity, startup manifest, receipt, and lineage);
- `POST /api/jobs` request, accepted response, and persisted submission manifest;
- validation-receipt lookup response; and
- contribution lookup response.

Run this from the repository root:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python scripts/validate_api_contract.py
```

It validates the examples and checks the contract's published route list against FastAPI's generated OpenAPI paths. It also verifies negative fixtures missing required creator, manifest, validation, lineage, or attribution fields. The command emits a JSON receipt suitable for local step evidence; no runtime artifact is written.

## Migration notes

- Contract version 1: initial Phase 1 local schema contract. No prior published schema version requires migration.
