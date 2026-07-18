# Model and Expert Manifest v0

A model or expert stored locally may carry an adjacent `*.manifest.json` file. This is a small, hand-authored audit document, not a registry, network advertisement, capability guarantee, consensus proof, or reward record.

`aethermesh_core.expert_manifest.load_expert_manifest()` validates the exact JSON v0 shape. `expert_is_usable()` is deliberately stricter: it returns true only when validation is `passed`, the adjacent artifact exists and matches its SHA-256 hash, and the recorded local validation receipt exists. A `receipt_path` must be `null` until a real local validation creates it; the sample remains `unvalidated` and does not invent one.

## Required top-level fields

| Field | Meaning |
| --- | --- |
| `manifest_version` | Exactly `aethermesh-expert-manifest/v0`. |
| `expert_id`, `display_name` | Stable local identity and human label; neither is a capability claim. |
| `creator_node_id`, `created_at` | Originating local node and UTC creation timestamp. |
| `artifact` | Adjacent/local relative `reference` plus lowercase `sha256:` content hash. |
| `supported_task_categories` | Non-empty, bounded labels for tasks the operator intends to support. |
| `runtime_requirements` | Non-empty local requirements such as a runner or model format. |
| `lineage` | Source model, optional adapter/template references, local-change note, parent IDs, and derived artifact references. |
| `validation` | Test command, expected input reference, receipt path, timestamp, status, and validator node ID. All evidence fields are required for `passed`; they may be `null` before validation. |
| `contribution_attribution` | Creator (matching the top level), modifiers, validator, and receipt references. It records attribution only—never rewards, credits, or token accounting. |

All references are safe relative paths, and usability checks reject references that resolve outside the manifest directory. Validation and contribution attribution must name the same validator and receipt. The format rejects unknown fields so a handoff or copy keeps the same complete provenance shape. `examples/model-experts/echo-expert-v0/manifest.json` sits next to its artifact and is a parseable, deliberately unvalidated root example.
