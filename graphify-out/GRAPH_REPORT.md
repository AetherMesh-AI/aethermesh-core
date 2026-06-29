# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 26 files · ~9,135 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 272 nodes · 633 edges · 14 communities (11 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 59 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `61ef94fc`
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
1. `Job` - 43 edges
2. `JobResult` - 34 edges
3. `run_local_simulation()` - 27 edges
4. `main()` - 25 edges
5. `ContributionLedger` - 21 edges
6. `CliTests` - 21 edges
7. `JobManifestTests` - 21 edges
8. `validate_job_result()` - 20 edges
9. `NodeIdentity` - 19 edges
10. `ScheduledNode` - 17 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `ValidationTests` --uses--> `Job`  [INFERRED]
  tests/test_validation.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `JobManifestTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/scheduler.py
- `LocalSimulationTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py

## Import Cycles
- None detected.

## Communities (14 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (8): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., Core data models for the local AetherMesh prototype., Local in-memory runner for the first AetherMesh executable slice., Local multi-node simulation for the AetherMesh prototype., _simulation_message(), _summary_to_simulation_dict(), _validation_summary()

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (19): _coerce_node(), JobAssignment, LocalScheduler, NoAvailableNodesError, NodeStatus, Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Availability states needed by the local scheduler. (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (26): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_ledger_document(), Contribution ledger helpers for local job results., Serialize the ledger into the small local JSON file shape. (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (12): JobResult, Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result., Build deterministic text statistics for a local ``text_stats`` job., _invalid(), Local validation gate for reported AetherMesh job results., Deterministic outcome from validating one reported job result. (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (9): MeshMessage, Local mesh message envelopes for deterministic simulation output., JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (16): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), run_demo(), Job, NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., A small in-memory job assigned to a local node. (+8 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (19): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_entry() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (4): build_parser(), main(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.21
Nodes (10): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _remove_temp_file() (+2 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Community 6` to `Community 0`, `Community 3`, `Community 7`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 0`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `LocalSimulationResult` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _70 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.10804597701149425 - nodes in this community are weakly interconnected._