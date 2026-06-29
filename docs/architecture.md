# AetherMesh Core Architecture

## Purpose

AetherMesh Core defines the smallest shared model needed to reason about an AetherMesh network independent of any specific language, runtime, transport, or deployment environment.

The core should make foundational mesh concepts explicit and testable so later adapters and applications can build on the same rules instead of duplicating assumptions.

## Scope

AetherMesh Core is responsible for:

- Defining mesh node identity at the domain level.
- Defining peer endpoint concepts at the domain level.
- Validating core inputs so invalid identities or endpoints fail predictably.
- Providing minimal reusable behavior that other AetherMesh components can call.
- Recording architecture decisions that shape the core boundary.

The core should be usable by future command-line tools, daemons, services, tests, and integrations, but it should not assume any one of those consumers exists yet.

## Non-goals

AetherMesh Core does not currently own:

- Peer discovery behavior.
- Network transport protocols or wire formats.
- Routing, gossip, consensus, or synchronization algorithms.
- Persistence, configuration file formats, secrets handling, or key storage.
- CLI, daemon, service, UI, or deployment scaffolding.
- Package manager, CI provider, hosting, or release automation choices.

These may become separate modules or consumers later, but they should not be added to the core until the boundary is validated.

## Core concepts

### Mesh node

A mesh node is one participant in an AetherMesh network. At the core layer, a node should be represented by a stable identity and any minimal metadata required to validate that identity. The core should not decide how a node is hosted, discovered, persisted, or authenticated until those responsibilities are explicitly designed.

### Peer endpoint

A peer endpoint is a validated way to refer to another node as a possible connection target. At the core layer, an endpoint should capture only the information needed to identify and validate a peer address conceptually. It should not imply a specific transport, socket implementation, discovery process, or connection lifecycle.

### Validation result

A validation result is the predictable outcome of checking domain input. The first implementation should make valid and invalid node identities or peer endpoints easy to distinguish without requiring networking or persistence.

### Core boundary

The core boundary separates domain rules from runtime behavior. Code inside the core should remain small, deterministic, and easy to test. Runtime components should depend on the core rather than forcing the core to depend on runtime infrastructure.

## Expected future repository layout

The repository may grow toward a layout like this once implementation choices are made:

```text
README.md
docs/
  architecture.md
src/ or packages/
  core-domain-module
tests/ or equivalent validation suite
```

This is a proposal only. Do not create empty directories, package manifests, source folders, or test scaffolding until the language, runtime, and test approach are chosen for a real implementation PR.

## First implementation seam

The next PR should be small and testable:

- Add a minimal core library/module.
- Model one mesh node identity.
- Model one validated peer endpoint.
- Provide one executable validation path or unit test suite.
- Prove valid and invalid inputs are handled predictably.

The seam should avoid networking, persistence, discovery, transport behavior, daemon scaffolding, and configuration formats. It should also avoid committing to a broader architecture than the first model and validation path require.

## Open questions

- Which implementation language and runtime should own the first core module?
- What is the minimum acceptable shape for a node identity?
- What is the minimum acceptable shape for a peer endpoint before transport choices are made?
- Should validation failures be represented as exceptions, result values, error collections, or another pattern?
- Which test runner or validation command should become the first standard project check?
- What external consumers are expected to depend on AetherMesh Core first?
