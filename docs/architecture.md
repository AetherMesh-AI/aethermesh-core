# AetherMesh Core Architecture

## Purpose

AetherMesh Core is the foundation for a decentralized AI mesh. It should provide the smallest set of concepts and behavior needed to run nodes, assign useful work, report results, and measure contribution over time.

The architecture should grow from working local behavior toward distributed behavior. Early code should be simple, testable, and runnable before the project adds networking, rewards, dashboards, or production deployment complexity.

## Design principles

- Build small working layers.
- Keep local development useful before distributed deployment.
- Make behavior testable before making it scalable.
- Prefer clear data models and validation over broad abstractions.
- Treat contribution tracking as practical accounting first, not tokenomics.
- Keep security in mind before exposing public network behavior.
- Avoid adding components that do not connect to the current runnable path.

## Core responsibilities

AetherMesh Core should eventually own the shared foundation for:

- Node identity and basic node metadata
- Node lifecycle states
- Peer or neighbor descriptions
- Job definitions
- Job assignment and execution records
- Result reporting
- Contribution accounting
- Validation of core data and state transitions
- Local-first execution paths that can later expand into networked behavior

The first implementation does not need all of these pieces. It should introduce the smallest useful subset that can run locally and be tested.

## Non-goals for the first prototype

The first prototype should not try to solve:

- Production peer discovery
- Distributed consensus
- Public network security
- Token or reward economics
- Complex scheduling
- Cloud orchestration
- Dashboard polish
- Marketplace behavior
- Persistent identity or key management beyond simple local placeholders

These may become important later, but they should not block the first runnable proof.

## Suggested first runnable slice

A good first implementation target is a local-only node prototype that can:

1. Create or load a simple node identity.
2. Define a small job type.
3. Execute a local mock job.
4. Record the result.
5. Track a simple contribution value for completed work.
6. Expose one validation or test command proving the behavior works.

This slice does not need networking. It only needs to prove the project can model a node doing useful work and recording the result in a way that future networking can build on.

## Growth path

After the first runnable local slice exists, the project can grow by adding one capability at a time:

1. Stronger node model
2. Job schema and validation
3. Result validation
4. Contribution ledger
5. Local CLI
6. Basic peer message format
7. Local multi-node simulation
8. Real transport
9. Deployment packaging
10. AI workload adapters

Each step should include tests or validation and should keep the system understandable to new contributors.

## Open questions

- What runtime should the first runnable prototype use?
- What is the smallest useful job type that proves contribution without requiring real AI workloads?
- What contribution record is useful before rewards or tokenomics exist?
- What should be stored locally, and what should remain in memory for the first prototype?
- How should local simulation prepare for eventual networked nodes without overengineering the first version?
