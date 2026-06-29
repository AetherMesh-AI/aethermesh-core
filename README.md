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

The initial project charter is in [docs/architecture.md](docs/architecture.md).

## Next implementation target

The next small implementation step should add a minimal core library/module that models one mesh node identity and one validated peer endpoint, plus a single executable validation path or unit test suite proving valid and invalid inputs are handled predictably. See [docs/architecture.md](docs/architecture.md) for scope, non-goals, and open questions before choosing a language or runtime.
