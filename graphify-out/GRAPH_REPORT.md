# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 21 files · ~5,456 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 190 nodes · 406 edges · 16 communities (14 shown, 2 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 45 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f86766c3`
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
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]

## God Nodes (most connected - your core abstractions)
1. `JobResult` - 30 edges
2. `Job` - 29 edges
3. `ContributionLedger` - 21 edges
4. `run_local_simulation()` - 20 edges
5. `validate_job_result()` - 15 edges
6. `ContributionLedgerTests` - 14 edges
7. `LocalRunner` - 13 edges
8. `LocalSimulationResult` - 13 edges
9. `LocalScheduler` - 12 edges
10. `LedgerPersistenceError` - 11 edges

## Surprising Connections (you probably didn't know these)
- `ContributionLedgerTests` --uses--> `ContributionRecord`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py
- `ContributionLedgerTests` --uses--> `LedgerPersistenceError`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py
- `LocalRunnerTests` --uses--> `Job`  [INFERRED]
  tests/test_runner.py → src/aethermesh_core/models.py
- `ContributionLedgerTests` --uses--> `JobResult`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/models.py
- `LocalSimulationTests` --uses--> `JobAssignment`  [INFERRED]
  tests/test_simulation.py → src/aethermesh_core/scheduler.py

## Import Cycles
- None detected.

## Communities (16 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.19
Nodes (7): AetherMesh Core local prototype package., Core data models for the local AetherMesh prototype., Local in-memory runner for the first AetherMesh executable slice., Local multi-node simulation for the AetherMesh prototype., _simulation_message(), _summary_to_simulation_dict(), Local validation gate for reported AetherMesh job results.

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (17): _coerce_node(), JobAssignment, LocalScheduler, NoAvailableNodesError, NodeStatus, Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Availability states needed by the local scheduler. (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (9): LedgerPersistenceError, Deserialize a ledger from the local JSON file shape., Raised when a local ledger JSON file cannot be safely loaded or saved., Deserialize one JSON-compatible contribution record., _record_from_json_value(), _require_record_field(), Serialize the result into a JSON-compatible dictionary., Serialize the validation result into a JSON-compatible dictionary. (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (17): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., Run one local job and return a structured result., Run local jobs across local node identities using scheduler assignment.      Thi (+9 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (9): MeshMessage, Local mesh message envelopes for deterministic simulation output., JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (10): run_demo(), NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs., LocalRunner, Execute the single supported local job type for a node., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation. (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.43
Nodes (3): ContributionLedger, Small in-memory ledger for prototype contribution accounting., ContributionLedgerTests

### Community 8 - "Community 8"
Cohesion: 0.26
Nodes (5): build_parser(), main(), Command-line interface for the local AetherMesh prototype., ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.28
Nodes (7): _accounted_units(), Contribution ledger helpers for local job results., Write a JSON-backed local ledger via temp-file then atomic replace., Record one result and return its local contribution record.          Only comple, _remove_temp_file(), save_ledger_document(), _string_output()

### Community 13 - "Community 13"
Cohesion: 0.25
Nodes (5): ContributionSummary, Serialize the ledger into the small local JSON file shape., Aggregated contribution totals for one local node., Serialize the summary into a JSON-compatible dictionary., Return deterministic aggregate totals for one local node.

### Community 14 - "Community 14"
Cohesion: 0.33
Nodes (3): ContributionRecord, Audit record derived from one local job result., Serialize the record into a JSON-compatible dictionary.

### Community 15 - "Community 15"
Cohesion: 0.53
Nodes (3): load_ledger_document(), Load a JSON-backed local ledger, treating a missing file as empty.      The retu, Path

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LocalSimulationResult` connect `Community 6` to `Community 0`, `Community 1`, `Community 3`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `JobResult` connect `Community 3` to `Community 0`, `Community 2`, `Community 6`, `Community 7`, `Community 12`, `Community 13`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.135) - this node is a cross-community bridge._
- **Why does `run_local_simulation()` connect `Community 3` to `Community 0`, `Community 1`, `Community 5`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `Job` (e.g. with `LocalRunner` and `LocalSimulationResult`) actually correct?**
  _`Job` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ContributionLedger` (e.g. with `JobResult` and `LocalSimulationResult`) actually correct?**
  _`ContributionLedger` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _60 weakly-connected nodes found - possible documentation gaps or missing edges._