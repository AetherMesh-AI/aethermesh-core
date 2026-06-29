# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 32 files · ~12,244 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 372 nodes · 903 edges · 13 communities (10 shown, 3 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 107 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0b04e186`
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
1. `Job` - 48 edges
2. `JobResult` - 38 edges
3. `main()` - 32 edges
4. `ContributionLedger` - 32 edges
5. `run_local_simulation()` - 30 edges
6. `MeshMessage` - 27 edges
7. `CliTests` - 27 edges
8. `LocalMessageBus` - 26 edges
9. `NodeIdentity` - 25 edges
10. `NodeRegistry` - 24 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `NodeIdentity`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/models.py
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py

## Import Cycles
- None detected.

## Communities (13 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (15): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type() (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (32): NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order. (+24 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (33): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+25 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (21): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., Serialize the result into a JSON-compatible dictionary., build_text_stats_output() (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (25): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., MeshMessage, JSON-compatible message envelope for local mesh communication records. (+17 more)

### Community 6 - "Community 6"
Cohesion: 0.18
Nodes (14): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_entry() (+6 more)

### Community 8 - "Community 8"
Cohesion: 0.11
Nodes (6): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.13
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 2`, `Community 5`, `Community 6`, `Community 12`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 5`, `Community 12`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 12`, `Community 6`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `InboxProcessResult`) actually correct?**
  _`ContributionLedger` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _93 weakly-connected nodes found - possible documentation gaps or missing edges._