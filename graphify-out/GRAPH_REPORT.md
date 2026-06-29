# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 28 files · ~9,645 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 298 nodes · 686 edges · 12 communities (9 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9328e68`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 43 edges
2. `JobResult` - 34 edges
3. `run_local_simulation()` - 28 edges
4. `main()` - 25 edges
5. `ContributionLedger` - 21 edges
6. `CliTests` - 21 edges
7. `JobManifestTests` - 21 edges
8. `LocalMessageBus` - 20 edges
9. `validate_job_result()` - 20 edges
10. `NodeIdentity` - 19 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `LocalSimulationTests` --uses--> `Job`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `JobManifestTests` --uses--> `NodeStatus`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/scheduler.py

## Import Cycles
- None detected.

## Communities (12 total, 3 thin omitted)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (28): _coerce_node(), JobAssignment, LocalScheduler, NoAvailableNodesError, NodeStatus, Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Availability states needed by the local scheduler. (+20 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (26): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_ledger_document(), Contribution ledger helpers for local job results., Serialize the ledger into the small local JSON file shape. (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.19
Nodes (14): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result., Build deterministic text statistics for a local ``text_stats`` job., _invalid() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (20): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+12 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (19): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_job_entry(), _parse_jobs(), _parse_node_entry() (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (7): build_parser(), main(), Command-line interface for the local AetherMesh prototype., Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (20): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+12 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalSimulationResult` connect `Community 1` to `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 1` to `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 12`, `Community 7`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Job` (e.g. with `LocalJobBatch` and `ManifestError`) actually correct?**
  _`Job` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _77 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.07755102040816327 - nodes in this community are weakly interconnected._