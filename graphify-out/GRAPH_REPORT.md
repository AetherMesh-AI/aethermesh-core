# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 32 files · ~13,058 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 388 nodes · 952 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84e9018b`
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
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 56 edges
2. `JobResult` - 38 edges
3. `main()` - 32 edges
4. `ContributionLedger` - 32 edges
5. `run_local_simulation()` - 32 edges
6. `ScheduledNode` - 31 edges
7. `MeshMessage` - 28 edges
8. `CliTests` - 27 edges
9. `LocalMessageBus` - 26 edges
10. `NodeIdentity` - 25 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `LocalMessageBus`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/message_bus.py
- `LocalNodeServiceTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `NodeIdentity`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/models.py

## Import Cycles
- None detected.

## Communities (13 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (21): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., _accounted_units(), ContributionSummary, Contribution ledger helpers for local job results., Record one result and return its local contribution record.          Only comple, Aggregated contribution totals for one local node., _string_output() (+13 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (37): NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order. (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (46): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+38 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (18): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally. (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (17): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., MeshMessage, JSON-compatible message envelope for local mesh communication records. (+9 more)

### Community 6 - "Community 6"
Cohesion: 0.47
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (6): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (22): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+14 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 12`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 12`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 12`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `InboxProcessResult`) actually correct?**
  _`ContributionLedger` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _95 weakly-connected nodes found - possible documentation gaps or missing edges._