# AetherMesh Core

AetherMesh Core is the foundation for a decentralized AI network where people can run nodes, contribute useful compute or work, improve the system, and eventually receive access or usage benefits from the network they support.

The project is early-stage. The immediate goal is not to design the perfect decentralized AI platform. The goal is to build the smallest real, runnable, open-source prototype that proves the concept one layer at a time.

## North star

AetherMesh should grow into a decentralized AI mesh where:

- Anyone can run a node.
- Nodes connect into a shared network.
- The network assigns useful AI-related work.
- Nodes complete work and report results.
- The system measures meaningful contributions.
- Contributors can eventually earn usage, access, or credits.
- The project remains understandable, testable, and open.

## Development approach

Build in layers. Each change should make the project more real, runnable, testable, or easier to understand.

Prefer:

- Small working systems over large unfinished ones
- Simple protocols before complex ones
- Local development before distributed deployment
- Testable code over clever code
- Practical contribution tracking before tokenomics
- Security-minded design before public exposure

Avoid:

- Empty boilerplate
- Placeholder-only systems
- Unused abstractions
- Marketing-heavy documentation without technical value
- Token or reward logic before useful work exists
- Dashboard polish before core functionality
- Unsupported technical claims

## Current status

The repository contains project direction, architecture notes, and a first runnable local-only prototype. It includes a package manifest, a simple node identity model, an in-memory echo job runner, a local echo result validation gate, a CLI demo command, deterministic local simulation, and unit tests.

The next meaningful step is to strengthen the local node model and validation path without trying to solve networking, distributed coordination, rewards, or production security all at once.

## Near-term build direction

AetherMesh Core should grow toward:

1. A runnable local node
2. Basic local communication or message modeling
3. Simple job execution
4. Result reporting
5. Contribution tracking
6. Work validation
7. Easy local deployment
8. System visibility
9. Gradual introduction of AI workloads
10. Expansion beyond local environments

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

The simulation output includes per-result validation details and a compact `validation_summary`. Contribution credit is recorded only for validated completed `echo` results; invalid or unsupported results remain visible in the output for local audit/debugging and earn zero contribution units.

Run the unit tests without installing anything:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest discover -s tests -v
```

The demo is local-only. It creates an in-memory node identity, executes the built-in `echo` job, and prints one JSON result. Contribution units are fixed demo accounting only; rewards and token economics are out of scope.

To also print a local in-memory contribution summary for the demo result, add `--include-ledger`. This preserves the default single-result JSON output unless the ledger summary is explicitly requested. Ledger credit is recorded through the same local validation gate and the extended output includes the validation outcome.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the current architecture direction.
