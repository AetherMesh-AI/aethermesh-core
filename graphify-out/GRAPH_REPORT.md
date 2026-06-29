# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 34 files · ~15,893 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 430 nodes · 1076 edges · 14 communities (11 shown, 3 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 114 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `646df7da`
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
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 60 edges
2. `main()` - 42 edges
3. `JobResult` - 38 edges
4. `MeshMessage` - 36 edges
5. `CliTests` - 36 edges
6. `ContributionLedger` - 34 edges
7. `run_local_simulation()` - 33 edges
8. `ScheduledNode` - 31 edges
9. `LocalMessageBus` - 27 edges
10. `NodeIdentity` - 26 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `LocalMessageBus`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/message_bus.py
- `MessageLogTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_log.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (14 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.21
Nodes (10): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _remove_temp_file() (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (29): NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order. (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (35): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+27 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (33): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), build_message_log_document(), Build a deterministic version 1 audit document for local mesh messages., Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution. (+25 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (18): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+10 more)

### Community 6 - "Community 6"
Cohesion: 0.18
Nodes (15): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (15): load_message_log_messages(), _message_from_document_entry(), MessageLogPersistenceError, JSON-backed local message log persistence for batch simulations., Write a local message log via temp-file then atomic replace., Raised when a local message log JSON file cannot be safely loaded or saved., Load validated MeshMessage entries from a version 1 local message log.      The, _remove_temp_file() (+7 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (6): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (29): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype., Replay a saved local message log and process one node inbox., run_demo(), AetherMesh Core local prototype package. (+21 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 3`, `Community 12`, `Community 6`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 1`, `Community 12`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 3` to `Community 1`, `Community 2`, `Community 5`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `MeshMessage` (e.g. with `LocalMessageBus` and `MessageDelivery`) actually correct?**
  _`MeshMessage` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _102 weakly-connected nodes found - possible documentation gaps or missing edges._