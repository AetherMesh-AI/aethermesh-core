# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 21 files · ~4,550 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 167 nodes · 336 edges · 12 communities (10 shown, 2 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `665f676f`
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

## God Nodes (most connected - your core abstractions)
1. `Job` - 29 edges
2. `JobResult` - 28 edges
3. `run_local_simulation()` - 20 edges
4. `ContributionLedger` - 16 edges
5. `validate_job_result()` - 15 edges
6. `LocalRunner` - 13 edges
7. `LocalSimulationResult` - 13 edges
8. `LocalScheduler` - 12 edges
9. `MeshMessage` - 11 edges
10. `NodeIdentity` - 11 edges

## Surprising Connections (you probably didn't know these)
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `LocalSimulationTests` --uses--> `Job`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `LocalSimulationTests` --uses--> `JobAssignment`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py
- `ContributionLedgerTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py

## Import Cycles
- None detected.

## Communities (12 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (13): build_parser(), main(), Command-line interface for the local AetherMesh prototype., Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), AetherMesh Core local prototype package., In-memory contribution ledger for local job results., Core data models for the local AetherMesh prototype. (+5 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (17): _coerce_node(), JobAssignment, LocalScheduler, NoAvailableNodesError, NodeStatus, Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Availability states needed by the local scheduler. (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (16): _accounted_units(), ContributionRecord, ContributionSummary, Audit record derived from one local job result., Serialize the record into a JSON-compatible dictionary., Aggregated contribution totals for one local node., Serialize the summary into a JSON-compatible dictionary., Record one result and return its local contribution record.          Only comple (+8 more)

### Community 3 - "Community 3"
Cohesion: 0.27
Nodes (11): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., Run one local job and return a structured result., _invalid(), Deterministic outcome from validating one reported job result., Validate a reported result against the assigned local job.      The current prot (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.23
Nodes (8): MeshMessage, Local mesh message envelopes for deterministic simulation output., JSON-compatible message envelope for local mesh communication records., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests, ValueError

### Community 6 - "Community 6"
Cohesion: 0.27
Nodes (9): run_demo(), NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., LocalRunner, Execute the single supported local job type for a node., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation. (+1 more)

### Community 7 - "Community 7"
Cohesion: 0.31
Nodes (4): ContributionLedger, Small in-memory ledger for prototype contribution accounting., _summary_to_simulation_dict(), ContributionLedgerTests

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (4): Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation(), _validation_summary(), LocalSimulationTests

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalSimulationResult` connect `Community 6` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 7`, `Community 8`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Why does `JobResult` connect `Community 3` to `Community 0`, `Community 2`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 8` to `Community 0`, `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Job` (e.g. with `LocalRunner` and `LocalSimulationResult`) actually correct?**
  _`Job` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `LocalSimulationResult`) actually correct?**
  _`ContributionLedger` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._