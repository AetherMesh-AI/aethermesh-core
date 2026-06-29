# AetherMesh Core

AetherMesh Core is the early-stage home for the implementation-neutral core of AetherMesh: the shared concepts, validation rules, and minimal domain behavior needed to describe mesh nodes and their peer relationships before any transport, runtime, or deployment model is chosen.

This repository is intentionally small right now. It should establish the project boundary first, then add runnable code only after the core model and validation seam are agreed on.

## What belongs here

- Core mesh identity concepts, such as nodes and peer endpoints.
- Validation rules that make those concepts predictable and testable.
- Small library/module behavior that can be reused by future adapters, CLIs, daemons, or services.
- Architecture notes that clarify what the core owns and what remains outside it.

## What does not belong here yet

- Runtime networking, peer discovery, transport protocols, or daemon behavior.
- Persistence, configuration formats, deployment manifests, or service scaffolding.
- Package manager, framework, CI, or language-specific setup before those decisions are documented.
- Application-specific integrations that should depend on the core rather than live inside it.

## Current status

AetherMesh Core is at the documentation foundation stage. There is no runnable implementation, package manifest, test runner, or public API yet.

The initial project charter is in [docs/architecture.md](docs/architecture.md). The first core module seam is defined in [docs/decisions/0001-first-core-module-seam.md](docs/decisions/0001-first-core-module-seam.md).

## Next implementation target

The next small implementation step should add the minimal TypeScript/Node.js core module and validation tests described by [decision 0001](docs/decisions/0001-first-core-module-seam.md). That module should model one mesh node identity, one parsed/validated peer endpoint, and deterministic validation success/failure results without adding networking, discovery, persistence, daemon behavior, or cryptographic key management.
