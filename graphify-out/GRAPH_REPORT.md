# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 24 files · ~7,660 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 238 nodes · 531 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 48 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc19321f`
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
1. `Job` - 42 edges
2. `JobResult` - 34 edges
3. `run_local_simulation()` - 23 edges
4. `ContributionLedger` - 21 edges
5. `validate_job_result()` - 20 edges
6. `main()` - 19 edges
7. `LocalRunner` - 16 edges
8. `CliTests` - 15 edges
9. `JobManifestTests` - 15 edges
10. `NodeIdentity` - 14 edges

## Surprising Connections (you probably didn't know these)
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `LocalSimulationTests` --uses--> `JobAssignment`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `ContributionLedgerTests` --uses--> `ContributionRecord`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (9): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., Core data models for the local AetherMesh prototype., Local in-memory runner for the first AetherMesh executable slice., Local multi-node simulation for the AetherMesh prototype., _simulation_message(), _summary_to_simulation_dict(), _validation_summary() (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (17): _coerce_node(), JobAssignment, LocalScheduler, NoAvailableNodesError, NodeStatus, Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Availability states needed by the local scheduler. (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_ledger_document(), Contribution ledger helpers for local job results., Serialize the ledger into the small local JSON file shape. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (18): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result. (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (9): MeshMessage, Local mesh message envelopes for deterministic simulation output., JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.21
Nodes (10): run_demo(), NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., LocalRunner, Execute supported local job types for a node., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation. (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.20
Nodes (4): build_parser(), main(), ArgumentParser, CliTests

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (13): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_ids() (+5 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Community 3` to `Community 0`, `Community 13`, `Community 6`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 6`, `Community 13`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `LocalSimulationResult`) actually correct?**
  _`ContributionLedger` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _66 weakly-connected nodes found - possible documentation gaps or missing edges._