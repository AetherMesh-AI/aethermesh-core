# Model and Expert Manifest v0

A model or expert stored locally may carry an adjacent `*.manifest.json` file. This is a small, hand-authored audit document, not a registry, network advertisement, capability guarantee, consensus proof, or reward record.

`aethermesh_core.expert_manifest.load_expert_manifest()` validates the exact JSON v0 shape. `expert_is_usable()` is deliberately stricter: it returns true only when validation is `passed`, the adjacent artifact exists and matches its SHA-256 hash, and the recorded local validation receipt preserves the manifest's accepted local identifier(s), artifact hash, validation time, and validator. A `receipt_path` must be `null` until a real local validation creates it; the sample remains `unvalidated` and does not invent one.

## Required top-level fields

| Field | Meaning |
| --- | --- |
| `manifest_version` | Exactly `aethermesh-expert-manifest/v0`. |
| `model_id` or `expert_id` | At least one stable, non-empty, whitespace-free local identifier. Both identifiers are permitted when a model is packaged as an expert. Use a clear local ID such as `local-echo-fixture-v0`, and retain it across local validation runs unless the model/expert meaningfully changes. These IDs are not global registry identifiers or capability claims. |
| `name` | Required non-empty, local-first human-readable descriptive metadata for logs, validation output, and manifest summaries, such as `Local Echo Fixture Expert`. It is not a primary lookup key or an immutable identifier; use `model_id` or `expert_id` for lookup and provenance. |
| `creator_node_id`, `created_at` | Originating local node and UTC creation timestamp. |
| `artifact` | Adjacent/local relative `reference` plus lowercase `sha256:` content hash. |
| `supported_task_categories` | Non-empty, bounded labels for tasks the operator intends to support. |
| `runtime_requirements` | Non-empty local requirements such as a runner or model format. |
| `lineage` | Source model, optional adapter/template references, local-change note, parent IDs, and derived artifact references. |
| `validation` | Test command, expected input reference, receipt path, timestamp, status, and validator node ID. All evidence fields are required for `passed`; they may be `null` before validation. |
| `contribution_attribution` | Creator (matching the top level), modifiers, validator, and receipt references. It records attribution only—never rewards, credits, or token accounting. |

All references are safe relative paths, and usability checks reject references that resolve outside the manifest directory. Validation and contribution attribution must name the same validator and receipt. The format rejects unknown fields so a handoff or copy keeps the same complete provenance shape. `examples/model-experts/echo-expert-v0/manifest.json` sits next to its artifact and is a parseable, deliberately unvalidated root example.

A passed manifest's receipt is an exact JSON object with `receipt_version` set to `aethermesh-expert-validation-receipt/v0`, `status` set to `passed`, and matching `name`, `model_id` and/or `expert_id`, `artifact_sha256`, `validated_at`, and `validator_node_id` values. The receipt displays the descriptive name alongside stable IDs; it never treats the name as a primary lookup key. Merely creating a file at `receipt_path` does not make an expert usable.
