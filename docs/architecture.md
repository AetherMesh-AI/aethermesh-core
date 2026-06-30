# AetherMesh Core Architecture

## Purpose

AetherMesh Core is the foundation for a decentralized AI mesh where people can run nodes, contribute useful compute/work, improve the system, and eventually receive access, usage benefits, credits, or earnings from the network they help support.

The architecture should grow from a small local prototype into a decentralized AI platform built around **AER: Adaptive Expert Routing**. Early code should stay simple, testable, and runnable before the project adds public networking, economics, dashboards, or production deployment complexity.

The persistent project directive is mirrored in [persistent-goal.md](persistent-goal.md). This architecture document explains how the current repo should move toward that directive.

## Current prototype layer

The current repo is a local-first proof of the mechanics AetherMesh needs later:

- Node identity and node metadata
- Manifest-defined local jobs
- Node capability advertisement in local manifests and heartbeat messages
- Deterministic local scheduling
- Local job execution
- Result reporting through structured messages
- Validation-gated contribution accounting
- Local ledgers and receipts
- Local message logs
- File-backed local transport inboxes
- Flow auditing
- Strict tests for deterministic behavior and coverage

This is intentionally not public networking yet. It should prove real node/work/contribution/validation behavior before claiming decentralization.

## North-star request flow

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

AetherMesh should feel like one AI system to users, but internally it should be a coordinated network of specialized, replicated, validated components.

## AER: Adaptive Expert Routing

**AER — Adaptive Expert Routing** is the main architecture pattern for AetherMesh.

AER routes each task to the best available expert model, verifier, tool runner, or node based on signals such as:

- task type
- model capability
- node reputation
- latency
- cost
- availability
- hardware capacity
- validation requirements
- safety requirements
- user preference or privacy needs

AER is not traditional Mixture-of-Experts inside one monolithic model. It is routed expert networking across decentralized replicas and supporting services.

Early AER can be rule-based and local. Later AER can use learned routing and richer scoring.

## REVA pipeline

The core AetherMesh request pipeline should evolve toward **REVA**:

```text
Router → Expert → Validator → Aggregator
```

### Router

The router decides where work should go. Early routers may be deterministic schedulers or rules. Later routers may account for expert type, capability, reputation, cost, privacy, latency, and validation needs.

### Expert

An expert is a specialized model, adapter, tool, or service that handles a specific task type. Early experts may be simple deterministic workloads. Later experts may include coding, Linux, Unity, reasoning, writing, safety, data, validation, and meta-improvement experts.

### Validator

A validator checks whether work was done correctly. Early validation should use deterministic output checks, schemas, hashes, duplicate work, tests, or benchmark-style assertions. Later validation may include hidden evals, model comparisons, verifier models, fraud detection, and safety checks.

### Aggregator

The aggregator combines or finalizes results. It may merge multiple expert outputs, resolve conflicts, select the strongest answer, format the final response, include validation results, or reject poor output.

## AEF: Aether Expert Fabric

**AEF — Aether Expert Fabric** is the long-term distributed layer where expert models, adapters, validators, routers, aggregators, and supporting services are hosted by the network.

A mature AEF should support:

- replicated experts
- versioned experts
- model hashes
- adapter hashes
- node reputation
- routing scores
- contribution tracking
- validation scores
- upgrade proposals
- rollback when quality drops

An expert should be treated as a network service with many possible replicas, not as one machine owned by one person.

## Core responsibilities

AetherMesh Core should own the shared foundation for:

- Node identity and basic node metadata
- Node lifecycle states
- Capability advertisement
- Peer or neighbor descriptions
- Job and expert-type definitions
- Job assignment and execution records
- Result reporting
- Contribution accounting
- Validation of outputs and state transitions
- Local-first execution paths that can later expand into networked behavior
- Routing primitives that can eventually become AER
- Validation and aggregation primitives that can eventually become REVA

## Prototype evolution path

Build in layers:

1. Runnable local node behavior
2. Basic local identity
3. Manifest-driven local jobs
4. Local communication/message logs
5. Result reporting
6. Validation-gated contribution records
7. Local transport seams
8. Capability advertisement
9. Simple routing
10. AI-like deterministic workloads
11. Small local AI inference jobs
12. Expert/job type registration
13. Validator node roles
14. Aggregator/synthesis behavior
15. Replicated expert services
16. Router improvements toward AER
17. AEF-based expert fabric

Each step should produce a focused PR with tests or validation.

## Non-goals for the current prototype

The current prototype should not try to solve:

- Production peer discovery
- Distributed consensus
- Public network security
- Token or reward economics
- Marketplace behavior
- Dashboard polish
- Cloud orchestration
- Frontier model training
- Claims of decentralization before nodes actually coordinate
- Traditional MoE framing when the target is routed expert networking

These may become important later, but they should not block the runnable proof.

## Validation direction

Validation is a core part of the architecture. AetherMesh should assume nodes may be unreliable, misconfigured, low quality, or eventually malicious.

Early validation should include schema checks, deterministic output checks, hashes, format checks, and duplicate work where useful. Later validation can include unit tests, hidden evals, verifier models, reputation scoring, fraud detection, safety checks, and contribution quality scoring.

Rewards or credits should eventually be based on validated usefulness, not raw activity.

## Contribution tracking direction

Early contribution tracking should remain practical and local:

- node ID
- job ID
- job type
- success/failure
- result hash or receipt
- validation result
- runtime or processing metadata when available
- reported capabilities

Later contribution tracking may include uptime, reliability, validation accuracy, model hosted, expert version served, compute provided, evals contributed, improvement proposals, and accepted model upgrades.

Tokenomics should wait until useful work and validation are real.

## Decision rule for new work

Before choosing work, ask:

1. What key foundation is missing?
2. What small step improves runnability?
3. What small step improves clarity?
4. What small step enables future AER routing?
5. What small step enables future expert hosting?
6. What small step enables future validation?
7. What small step enables future contribution tracking?
8. What can be completed cleanly in one PR?

The best interval is usually the one that makes AetherMesh more real, more runnable, more measurable, or easier to extend.
