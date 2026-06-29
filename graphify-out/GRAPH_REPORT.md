# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 24 files · ~8,400 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 251 nodes · 583 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 57 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `be34ee03`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 43 edges
2. `JobResult` - 34 edges
3. `run_local_simulation()` - 27 edges
4. `main()` - 21 edges
5. `ContributionLedger` - 21 edges
6. `JobManifestTests` - 21 edges
7. `validate_job_result()` - 20 edges
8. `ScheduledNode` - 17 edges
9. `CliTests` - 17 edges
10. `LocalRunner` - 16 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `ContributionLedgerTests` --uses--> `ContributionRecord`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py
- `ContributionLedgerTests` --uses--> `LedgerPersistenceError`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py
- `ValidationTests` --uses--> `Job`  [INFERRED]
  tests/test_validation.py → src/aethermesh_core/models.py
- `JobManifestTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/scheduler.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (16): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., Contribution ledger helpers for local job results., Core data models for the local AetherMesh prototype., build_text_stats_output(), Local in-memory runner for the first AetherMesh executable slice., Build deterministic text statistics for a local ``text_stats`` job., _coerce_simulation_node() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (28): LocalJobBatch, ManifestError, _parse_node_entry(), _parse_nodes(), Versioned JSON manifest loading for local batch simulation., Raised when a local job manifest cannot be loaded or validated., Validated local batch inputs for the local simulation path., Return manifest node IDs in deterministic manifest order. (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (25): Run a local simulation from a validated JSON manifest., run_local_batch(), _parse_job_entry(), _parse_jobs(), ContributionRecord, LedgerPersistenceError, load_ledger_document(), Serialize the ledger into the small local JSON file shape. (+17 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (14): _accounted_units(), ContributionLedger, ContributionSummary, Aggregated contribution totals for one local node., Small in-memory ledger for prototype contribution accounting., Record one result and return its local contribution record.          Only comple, Return deterministic aggregate totals for one local node., _string_output() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (9): MeshMessage, Local mesh message envelopes for deterministic simulation output., JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (15): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), run_demo(), Job, NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., A small in-memory job assigned to a local node. (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (4): build_parser(), main(), ArgumentParser, CliTests

### Community 13 - "Community 13"
Cohesion: 0.21
Nodes (3): load_job_manifest(), Load and validate a version 1 local job-batch manifest., JobManifestTests

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 0`, `Community 2`, `Community 6`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `LocalSimulationResult`) actually correct?**
  _`ContributionLedger` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _67 weakly-connected nodes found - possible documentation gaps or missing edges._