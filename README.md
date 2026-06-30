# AetherMesh Core

AetherMesh Core is the foundation for a decentralized AI network where people can run nodes, contribute useful compute/work, improve the system, and eventually receive access, usage benefits, credits, or earnings from the network they help support.

The project is still early-stage. The near-term goal is a real, runnable, open-source prototype that proves nodes can join locally, advertise capabilities, receive useful work, complete work, report results, record contribution, and validate output. The long-term goal is a people-owned AI mesh built around **AER: Adaptive Expert Routing**, not a centralized model host and not traditional monolithic MoE.

The persistent goal used by the automation loop is mirrored in [docs/persistent-goal.md](docs/persistent-goal.md). Every plan, PR, and commit should move the project toward that goal while staying small, testable, and understandable.

## North star

Build a decentralized AI mesh where:

- Anyone can run a node.
- Nodes connect into a shared network.
- Nodes advertise what work they can perform.
- The network assigns useful AI-related work.
- Nodes complete work and report results.
- The system measures meaningful contribution.
- Work can be validated instead of blindly trusted.
- Useful contributors can eventually earn usage, access, credits, or rewards.
- The project remains understandable, testable, and open.

The smallest useful prototype should prove the local version of this loop:

```text
Node starts
↓
Node registers locally or with a simple coordinator
↓
Node advertises capabilities
↓
System assigns a simple job
↓
Node executes the job
↓
Node reports the result
↓
System records the contribution
↓
System validates the result in a basic way
```

## Architecture direction

AetherMesh should grow toward **AER — Adaptive Expert Routing**. AER routes work across a decentralized fabric of replicated expert models, validators, aggregators, tool runners, and supporting nodes. It is not traditional Mixture-of-Experts inside one monolithic model.

The long-term request flow should become:

```text
User Request
   ↓
AetherMesh Gateway
   ↓
AER Router
   ↓
Selected Expert Replica(s)
   ↓
Validator Node(s)
   ↓
Aggregator / Synthesis Layer
   ↓
Final Answer
```

The core request pipeline should follow the **REVA** pattern:

```text
Router → Expert → Validator → Aggregator
```

The long-term hosting layer is the **AEF — Aether Expert Fabric**, where expert models, adapters, validators, routers, aggregators, and support services are versioned, replicated, measured, and validated across the network.

See [docs/architecture.md](docs/architecture.md) for the architecture map and [docs/persistent-goal.md](docs/persistent-goal.md) for the full north-star directive.

## Development approach

Build in layers. Each change should make the project more real, runnable, measurable, validated, or easier to extend.

Prefer:

- Small working systems over large unfinished systems
- Simple protocols before complex ones
- Local development before distributed deployment
- Clear documentation over vague ambition
- Testable code over clever code
- Practical contribution tracking before tokenomics
- Security-minded design before public exposure
- Real node behavior before dashboard polish
- Real validation before reward logic
- Simple routing before AI-powered routing

Avoid:

- Empty boilerplate
- Placeholder-only systems
- Unnecessary large rewrites
- Unused abstractions
- Marketing-heavy documentation without technical value
- Token or reward logic before useful work exists
- Dashboard polish before core functionality
- Unsupported technical claims
- Pretending the system is decentralized before nodes actually coordinate
- Calling the system MoE when it is currently routed expert networking

## Current status

The repository contains project direction, architecture notes, and a first runnable local-only prototype. It includes local node identity, deterministic local jobs, manifest-driven batch execution, local message logs, local transport inboxes, contribution accounting, validation gates, receipts, peer heartbeat summaries, flow auditing, and strict tests.

This is still a local prototype. It proves the mechanics that future distributed behavior can build on, but it does not yet provide public networking, production peer discovery, distributed consensus, real reward logic, or hosted AI experts.

## Near-term build direction

When uncertain, prioritize work that moves the prototype toward the persistent goal:

1. Making the project runnable
2. Clarifying the architecture
3. Making the node real
4. Enabling basic node identity
5. Enabling node communication
6. Implementing simple jobs
7. Reporting job results
8. Tracking contributions
9. Validating work
10. Advertising node capabilities
11. Adding simple routing
12. Simplifying Docker setup
13. Improving onboarding
14. Expanding into AI workloads
15. Introducing expert-style job categories
16. Replicating expert services
17. Adding validator roles
18. Adding aggregator/synthesis behavior
19. Improving routing toward AER
20. Growing toward the Aether Expert Fabric

Each addition should be small, validated, and useful on its own.

## Run locally

Run one local demo node job from the repository root without installing anything:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-demo --node-id local-demo-node --message "hello mesh"
```

Run the deterministic local multi-node simulation:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli simulate-local
```

Run a custom local job batch from a versioned JSON manifest:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-local-batch --manifest examples/local-batch.json
```

A minimal manifest lists ordered local node IDs and ordered jobs. Node entries may use the original string form, which defaults to `available`, or an object form with `node_id` and optional `status` (`available` or `offline`). Offline nodes stay visible in the output `node_roster` but do not receive work:

```json
{
  "version": 1,
  "nodes": [
    "local-node-a",
    {"node_id": "local-node-b", "status": "offline"},
    {"node_id": "local-node-c", "status": "available"}
  ],
  "jobs": [
    {"job_id": "echo-1", "job_type": "echo", "payload": {"message": "hello mesh"}},
    {"job_id": "text-stats-1", "job_type": "text_stats", "payload": {"text": "hello mesh\nhello node"}},
    {"job_id": "keyword-extract-1", "job_type": "keyword_extract", "payload": {"text": "AetherMesh nodes process useful local work for the mesh.", "limit": 5}},
    {"job_id": "text-chunk-1", "job_type": "text_chunk", "payload": {"text": "AetherMesh prepares local text chunks for future AI processing.", "max_chars": 24}},
    {"job_id": "text-embed-1", "job_type": "text_embed", "payload": {"text": "AetherMesh nodes prepare deterministic local feature vectors.", "dimensions": 8}}
  ]
}
```

The simulation output includes per-result validation details and a compact `validation_summary`. Contribution credit is recorded only for validated completed `echo`, deterministic `text_stats`, deterministic `keyword_extract`, deterministic `text_chunk`, and deterministic `text_embed` text-preprocessing results. Invalid or unsupported results remain visible in the output for local audit/debugging and earn zero contribution units.

Prototype contribution scoring is deterministic, integer-only, capped, and local-only. The current rules are intentionally simple: `echo` earns 1 unit; `text_stats` earns 1 base unit plus 1 unit per 100-character output bucket capped at 5; `keyword_extract` earns 1 base unit plus 1 unit per 5 extracted unique-keyword bucket capped at 5; `text_chunk` earns 1 base unit plus 1 unit per 2 emitted chunks capped at 5; and `text_embed` earns 1 base unit plus bounded token-count and vector-dimension bucket units capped at 6. These units are prototype accounting for local auditability only; they are not rewards, payments, reputation, tokenomics, payouts, or an economic fairness model.

The `text_chunk` workload accepts plain input text plus optional `max_chars` (default 120, range 1-1000), preserves input character order, prefers whitespace boundaries, and splits long continuous spans at the character limit. The `text_embed` workload is prototype-only deterministic local feature extraction, not a real semantic ML embedding model; it accepts non-empty text plus optional `dimensions` (default 8, range 2-64) and returns exact integer SHA-256 token-bucket counts such as `{"dimensions": 4, "token_count": 3, "unique_terms": 2, "vector": [0, 2, 1, 0]}`.

The local-only `node_roster` includes each node's `node_id`, `status`, assignment count, contribution units, and deterministic heartbeat metadata. `heartbeat_sequence` and `heartbeat_count` are in-memory simulation counters recorded when available nodes start a local run; they are not real network heartbeats or wall-clock liveness timestamps.

To opt in to local JSON-backed contribution persistence for a manifest batch, pass `--ledger-path`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-local-batch --manifest examples/local-batch.json --ledger-path ./local-ledger.json
```

When enabled, batch runs append validation-gated contribution records to the same version 1 local ledger JSON shape used by `run-demo` and print per-node persisted ledger summaries. New records include the validation outcome (`validation_valid`, `validation_reason`) and lightweight `job_type` metadata for local auditability; older ledger records that lack those fields still load. Without `--ledger-path`, batch output and file writes are unchanged.

To opt in to local JSON-backed message trace persistence for a manifest batch, pass `--message-log-path`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-local-batch --manifest examples/local-batch.json --message-log-path ./local-messages.json
```

When enabled, the batch overwrites the requested version 1 local-only message log with a deterministic audit document. The document preserves ordered mesh message entries (`message_id`, `message_type`, sender, recipient, payload, and correlation id) plus run metadata such as message count, job count, completion/failure totals, validation summary, node ids, job ids, and total contribution units. Writes use a temp file and atomic replace; without `--message-log-path`, no message log file is written.

Dispatch a manifest batch into an assignment-only local message log without running workers or writing contribution records:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli dispatch-local-batch --manifest examples/local-batch.json --message-log-path ./local-dispatch.json
```

The dispatch log contains deterministic `node_heartbeat` messages for available nodes and `job_assigned` messages for scheduled jobs. Heartbeat payloads include each available node's manifest capabilities. Use `process-local-inbox` to consume the dispatch log later for one node and record validation-gated contribution.

To test the file-backed local transport seam, materialize addressed dispatch messages into per-node inbox files, have a node consume only its own inbox, optionally write that node's emitted messages to a per-node outbox, then collect worker outboxes into one coordinator-side message log:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli materialize-local-inboxes --message-log-path ./local-dispatch.json --transport-dir ./local-transport
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli process-local-inbox --node-id local-node-a --transport-dir ./local-transport --ledger-path ./local-ledger.json --write-transport-outbox
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli collect-local-outboxes --transport-dir ./local-transport --message-log-path ./collected-worker-output.json
```

This writes version 1 inbox documents at `./local-transport/inboxes/<node-id>.json` only for nodes with addressed messages; empty inboxes are omitted. Transport processing reuses the same validation, ledger, receipt/output-message, and node-state behavior as message-log replay, but reads only the requested node's inbox file. When `--write-transport-outbox` is used, the worker writes emitted result/contribution messages to `./local-transport/outboxes/<node-id>.json`. `collect-local-outboxes` reads those outboxes without deleting, acknowledging, or rewriting them and writes a deterministic version 1 message log ordered by node id and outbox message order. Missing or empty transport/outbox directories are valid no-op collections that write an empty message log with `message_count: 0` metadata.

Inspect the heartbeat-derived local peer roster from an existing version 1 message log without rewriting it:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli peer-summary --message-log-path ./local-dispatch.json
```

This is local message-log peer discovery only: it summarizes recorded `node_heartbeat` messages into deterministic JSON and does not imply real networking, production peer discovery, or wall-clock health monitoring.

Replay a saved local message log into an in-memory bus and process exactly one node's assigned inbox work:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli process-local-inbox --node-id local-node-a --message-log-path ./local-messages.json --ledger-path ./local-ledger.json
```

This command is a local development replay path: it reads the version 1 message log without rewriting it, registers senders and recipients from the log, processes only the requested node's `job_assigned` inbox messages, optionally persists validation-gated contribution records to the existing version 1 ledger format, and prints deterministic JSON with processed counts, ignored message ids, emitted result/contribution messages, validation outcomes, and ledger totals.

Run the full local dispatch-plus-workers prototype flow into one deterministic artifact directory:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-local-flow --manifest examples/local-batch.json --output-dir /tmp/aethermesh-local-flow
```

The flow writes `dispatch-message-log.json`, a merged run-level `flow-message-log.json`, one shared `ledger.json`, deterministic per-job `receipts.json`, per-node state files under `node-state/`, and per-node replay/output logs under `worker-message-logs/`. The flow log is a deterministic local audit transcript: dispatch messages appear once, followed by worker-emitted result/contribution messages in stable available-node order. Receipts compactly tie each processed assignment to its result, validation decision, contribution record, credited units, and output summary. Offline manifest nodes stay visible in the JSON summary but are not processed as workers.

Run the equivalent one-command file-backed transport proof, where dispatch is first materialized into isolated per-node inbox files and workers read only their own inbox:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-local-transport-flow --manifest examples/local-batch.json --output-dir /tmp/aethermesh-local-transport-flow
```

This writes the same core flow artifacts plus `transport/inboxes/<node-id>.json` for available nodes with assignments. The command remains local-only: it proves the transport seam without sockets, daemons, distributed consensus, or production networking.

Audit an existing local flow artifact directory without modifying it:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli audit-local-flow --output-dir /tmp/aethermesh-local-flow
```

The audit command reads the dispatch log, flow log, ledger, and receipts, verifies that receipts reference assignment/result/contribution messages and that credited receipt units match ledger totals, then prints deterministic JSON counts. Missing, malformed, unsupported-version, or inconsistent artifacts return a concise nonzero CLI error without rewriting the artifact directory.

Replay local assignment and result logs through an independent validator artifact without running workers or mutating the input logs/ledger:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli validate-local-results --assignment-log-path /tmp/aethermesh-local-flow/dispatch-message-log.json --result-log-path /tmp/aethermesh-local-flow/flow-message-log.json --validation-log-path /tmp/aethermesh-local-flow/validation-message-log.json
```

The validation replay command reads `job_assigned` and `job_result_reported` messages, matches them by correlation/job id, rebuilds the assigned job and reported result, recomputes `validate_job_result`, and writes a version 1 `local_validation_report` with deterministic `job_result_validated` entries. It refuses to overwrite an existing validation report and returns a concise nonzero error for malformed logs, missing assignments, duplicate assignment keys, duplicate result claims, or absent required payload fields. Invalid worker results are recorded in the report with `valid: false` instead of crashing the command.

To make repeated local inbox replays resumable for one node, pass `--node-state-path`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli process-local-inbox --node-id local-node-a --message-log-path ./local-messages.json --ledger-path ./local-ledger.json --node-state-path ./local-node-a-state.json
```

When enabled, the CLI loads a version 1 local node-state JSON file before processing, skips assignment messages already recorded for that same node, and saves the updated processed-message list only after ledger/output-message persistence succeeds. If the state file is missing it is created after a successful pass; malformed, wrong-node, duplicate-id, or unsupported-version state fails before ledger, output-log, or state writes. The default output shape is unchanged when `--node-state-path` is omitted.

To also persist the node's replay output as a new version 1 local-only message log, pass `--output-message-log-path`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli process-local-inbox --node-id local-node-a --message-log-path ./local-messages.json --ledger-path ./local-ledger.json --output-message-log-path ./local-node-a-output-messages.json
```

When enabled, the output log contains the validated input messages in their original order followed by the messages emitted while the requested node processed its assignments. Writes use the same temp-file and atomic replace path as batch message logs. Without `--output-message-log-path`, no output message log file is written and the default JSON response shape is unchanged.

Inspect an existing local contribution ledger without writing to it:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli ledger-summary --ledger-path ./local-ledger.json
```

Run the unit tests without installing anything:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -v
```

The demo is local-only. It creates an in-memory node identity, executes the built-in `echo` job, and prints one JSON result. When ledger output is requested, contribution units are assigned through the same validation-gated prototype scorer; rewards and token economics are out of scope.

To reuse the same local demo node id across runs, pass `--identity-path` instead of `--node-id`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-demo --identity-path ./local-node.json --message "hello mesh"
```

When the identity file is missing, the demo creates a minimal version 1 local-only JSON identity with a generated `local-...` node id. Later runs reuse the same node id. `--node-id` and `--identity-path` are mutually exclusive.

To also print a local in-memory contribution summary for the demo result, add `--include-ledger`. This preserves the default single-result JSON output unless the ledger summary is explicitly requested. Ledger credit is recorded through the same local validation gate and the extended output includes the validation outcome.

To opt in to local JSON-backed contribution persistence for the demo, pass `--ledger-path`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m aethermesh_core.cli run-demo --node-id local-demo-node --message "hello mesh" --ledger-path ./local-ledger.json
```

When enabled, the demo loads the ledger file if it exists, treats a missing file as an empty ledger, records one validated demo result, writes the updated JSON with a temp-file-and-replace path, and prints the validation result plus the persisted per-node summary. This is intentionally local-only storage for development and auditability; it is not networking, rewards, or a production database layer.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the current architecture direction.
