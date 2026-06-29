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

The repository currently contains project direction and architecture notes. It does not yet contain a runnable node, package manifest, test runner, or network implementation.

The next meaningful step is to make the project runnable with a minimal local node model or validation path. That first runnable slice should demonstrate real behavior without trying to solve networking, distributed coordination, rewards, or production security all at once.

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

## Architecture

See [docs/architecture.md](docs/architecture.md) for the current architecture direction.
