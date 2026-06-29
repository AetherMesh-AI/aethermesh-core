# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 32 files · ~12,155 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 371 nodes · 895 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 105 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `549a9205`
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
1. `Job` - 47 edges
2. `JobResult` - 38 edges
3. `main()` - 32 edges
4. `ContributionLedger` - 32 edges
5. `run_local_simulation()` - 28 edges
6. `MeshMessage` - 27 edges
7. `CliTests` - 27 edges
8. `LocalMessageBus` - 26 edges
9. `NodeIdentity` - 25 edges
10. `NodeRegistry` - 24 edges

## Surprising Connections (you probably didn't know these)
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `NodeIdentity`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/models.py
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `LocalNodeServiceTests` --uses--> `LocalRunner`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/runner.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (14): AetherMesh Core local prototype package., NodeIdentity, Core data models for the local AetherMesh prototype., Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., LocalRunner, Local in-memory runner for the first AetherMesh executable slice., Execute supported local job types for a node. (+6 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (32): NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order. (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (35): Run a local simulation from a validated JSON manifest., run_demo(), run_local_batch(), _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (18): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., Serialize the result into a JSON-compatible dictionary., build_text_stats_output(), Run one local job and return a structured result., Build deterministic text statistics for a local ``text_stats`` job. (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.06
Nodes (33): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+25 more)

### Community 8 - "Community 8"
Cohesion: 0.10
Nodes (9): build_parser(), main(), Command-line interface for the local AetherMesh prototype., Run the fixed local simulation demo used by the CLI command., Load an existing ledger and return read-only aggregate totals., run_default_local_simulation(), summarize_ledger(), ArgumentParser (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.21
Nodes (10): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _remove_temp_file() (+2 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (13): load_job_manifest(), LocalJobBatch, ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_entry(), _parse_nodes(), Versioned JSON manifest loading for local batch simulation. (+5 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalSimulationResult` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 8`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 2`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `InboxProcessResult`) actually correct?**
  _`ContributionLedger` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _93 weakly-connected nodes found - possible documentation gaps or missing edges._