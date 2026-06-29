# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 30 files · ~10,952 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 343 nodes · 783 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 72 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `03c21acd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 43 edges
2. `JobResult` - 34 edges
3. `main()` - 32 edges
4. `run_local_simulation()` - 28 edges
5. `CliTests` - 27 edges
6. `ContributionLedger` - 25 edges
7. `NodeRegistry` - 24 edges
8. `ScheduledNode` - 24 edges
9. `JobManifestTests` - 21 edges
10. `LocalMessageBus` - 20 edges

## Surprising Connections (you probably didn't know these)
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `JobManifestTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/scheduler.py
- `LocalSimulationTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py
- `LocalSimulationTests` --uses--> `ScheduledNode`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (13): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., Core data models for the local AetherMesh prototype., Local in-memory runner for the first AetherMesh executable slice., Local multi-node simulation for the AetherMesh prototype., _send_simulation_message(), _summary_to_simulation_dict(), _validation_summary() (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (34): LocalJobBatch, Validated local batch inputs for the local simulation path., Return manifest node IDs in deterministic manifest order., NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports. (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (35): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (15): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result. (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (19): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (6): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (12): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_entry(), _parse_nodes() (+4 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalSimulationResult` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 12`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 12`, `Community 13`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 12`, `Community 13`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _88 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.12666666666666668 - nodes in this community are weakly interconnected._