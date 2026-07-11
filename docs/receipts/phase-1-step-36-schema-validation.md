# Phase 1 Step 36 Schema Validation Receipt

- Contract: `docs/phase-1-api-schema-contract.md`, schema contract version `1`.
- Validation command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest tests.test_phase1_api_schema_contract tests.test_runtime_service_api_cli tests.test_audit_inspection`
- Result: `Ran 32 tests` — `OK`.
- API contract coverage: documented JSON examples parse; the submission example is accepted and executed locally; the recorded validation receipt and contribution summary expose their documented provenance fields.
- Required-field rejection coverage: missing `creator_node_id`, `lineage_parent_refs`, and `attribution_metadata` are rejected before a submission manifest is created. `requested_validation_mode` and payload validation remain covered by the same local submission tests.
- Full local gate: `PYTHONDONTWRITEBYTECODE=1 python scripts/full_test.py --mode fast --base origin/main --keep-going` completed successfully: `581 passed, 366 subtests passed`, 100% branch coverage, Ruff, strict mypy, desktop tests, and repository quality gates passed.
