# AetherMesh Core Persistent Goal

AetherMesh Core is the foundation for a decentralized AI network where people can run nodes, contribute useful compute/work, improve the system, and eventually receive access, usage benefits, credits, or earnings from the network they help support.

AetherMesh should grow from zero into a real, runnable, open-source prototype, then gradually evolve into a decentralized AI platform built around **Adaptive Expert Routing**.

The long-term goal is not just to host AI models. The goal is to create a people-owned AI mesh where intelligence, compute, validation, improvement, and rewards are distributed across the network instead of controlled by one central entity.

Every run, PR, commit, and planning step should move the project toward that goal.

---

## North Star

Build a decentralized AI mesh where:

- Anyone can run a node.
- Nodes connect into a shared network.
- Nodes advertise what work they can perform.
- The network assigns useful AI-related work.
- Nodes complete work and report results.
- The system measures meaningful contributions.
- Work can be validated instead of blindly trusted.
- Useful contributors can eventually earn usage, access, credits, or rewards.
- The project remains understandable, testable, and open.

The smallest version of this should prove that a node can join, receive work, complete work, report results, and be measured.

The long-term version should evolve into a decentralized AI network powered by **AER: Adaptive Expert Routing**.

---

## Long-Term Architecture Vision

AetherMesh should eventually use **AER — Adaptive Expert Routing**.

AER is not traditional Mixture-of-Experts. Instead of one monolithic model with internal experts, AER routes tasks across a decentralized fabric of replicated expert models, validators, aggregators, and supporting nodes.

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

AetherMesh should feel like one AI system to the user, but internally it should be a coordinated network of specialized, replicated, and validated components.

---

## Core Terms

### AER — Adaptive Expert Routing

AER is the main architecture pattern for AetherMesh.

Its purpose is to route each task to the best available expert model, verifier, tool runner, or node based on:

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

AER should begin simple and become smarter over time.

Early versions may route basic jobs manually or with simple rules. Later versions may use a router model.

---

### REVA Pipeline

The core AetherMesh request pipeline should eventually follow the **REVA** pattern:

```text
Router → Expert → Validator → Aggregator
```

Each part has a clear role.

#### Router

The router decides where work should go.

It may choose:

- one expert
- multiple experts
- a verifier
- a tool-running node
- a cheaper model
- a stronger model
- a local/private node
- a fallback route

#### Expert

An expert is a specialized model, adapter, tool, or service that handles a specific type of task.

Examples:

- coding expert
- Linux expert
- Unity expert
- reasoning expert
- writing expert
- safety expert
- data-cleaning expert
- model-improvement expert

Experts should eventually be replicated across many nodes.

#### Validator

A validator checks whether work was done correctly.

Validation may include:

- output checking
- unit tests
- linting
- benchmark scoring
- duplicate detection
- safety checks
- factual checks
- comparison against other outputs
- hidden evaluation tests

The system should avoid trusting node output without some form of validation.

#### Aggregator

The aggregator combines or finalizes results.

It may:

- merge multiple expert outputs
- resolve conflicts
- choose the strongest answer
- format the final response
- enforce user instructions
- include validation results
- reject poor or unsafe outputs

---

### AEF — Aether Expert Fabric

The **Aether Expert Fabric** is the long-term distributed layer where expert models, adapters, validators, routers, aggregators, and supporting services are hosted by the network.

Experts should not depend on a single node.

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

---

## Development Philosophy

Build in layers.

Avoid jumping to the full AER/REVA/AEF architecture too early. The goal is to grow toward it through small, working, testable systems.

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
- Useful work before economic complexity

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

---

## Build Direction

The system should evolve by identifying gaps and implementing the smallest meaningful improvement.

At any point, it should:

- Run locally
- Demonstrate real behavior, even if minimal
- Be understandable to new contributors
- Be extendable without major rewrites
- Move toward real node coordination
- Move toward useful work execution
- Move toward measurable contributions
- Move toward validation and trust

Rather than rigid phases, grow by layering capabilities such as:

- A runnable node
- Local node identity
- Basic configuration
- Basic communication
- Simple job execution
- Result reporting
- Contribution tracking
- Work validation
- Basic routing
- Node capability advertisement
- Expert/job type registration
- Easy deployment
- System visibility
- Gradual introduction of AI workloads
- Replicated expert services
- Validator nodes
- Aggregator services
- Router improvements
- Expansion beyond local environments

Each addition should build on existing work without adding unnecessary complexity.

---

## Early Prototype Target

The first real prototype should prove the smallest useful version of AetherMesh.

A good early target is:

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

This does not need to involve large AI models at first.

Useful early jobs may include:

- echo/test jobs
- file hashing jobs
- simple compute jobs
- HTTP check jobs
- container health jobs
- script execution jobs
- small local model inference jobs
- validation jobs

The project should prove the network mechanics before attempting complex AI behavior.

---

## AI Direction

AetherMesh should gradually expand into AI workloads.

The AI roadmap should move in this order:

1. Simple non-AI jobs
2. Simple validation
3. Basic contribution tracking
4. Small local AI inference jobs
5. Model capability registration
6. Simple rule-based routing
7. Multiple expert job types
8. Replicated expert services
9. Validator nodes for AI outputs
10. Aggregator/synthesis services
11. Router model experiments
12. AER-based routed expert workflows
13. AEF-based replicated expert network
14. Training, fine-tuning, and improvement workflows

Do not start by trying to train a frontier model.

Start by building the network that can eventually route, validate, improve, and reward AI work.

---

## Expert Direction

Experts should eventually become versioned, replicated services.

Examples of future experts:

- AEX-General
- AEX-Coder
- AEX-Linux
- AEX-Unity
- AEX-Reasoning
- AEX-Writing
- AEX-Safety
- AEX-Data
- AEX-Validator
- AEX-Meta

AEX-Meta may eventually help improve other experts by analyzing failures, proposing datasets, suggesting evaluations, and identifying weak spots.

However, no expert should be allowed to directly approve its own changes without independent validation.

The safe improvement loop should be:

```text
Failure or opportunity is detected
↓
Meta/improvement expert proposes a change
↓
Training or implementation creates a candidate version
↓
Validators test old vs new
↓
Results are recorded
↓
Improved version is promoted only if validation proves value
```

---

## Validation Direction

Validation is a core part of AetherMesh.

The system should assume that nodes may be unreliable, misconfigured, low quality, or eventually malicious.

Validation should start simple and grow over time.

Early validation may include:

- checking that a job returned the expected format
- checking that a command completed successfully
- checking hashes
- checking deterministic outputs
- comparing duplicate work from multiple nodes

Later validation may include:

- unit tests
- benchmark tests
- hidden evals
- model-vs-model comparison
- verifier models
- reputation scoring
- fraud detection
- safety checks
- contribution quality scoring

Rewards or credits should eventually be based on validated usefulness, not raw activity.

---

## Contribution Tracking Direction

AetherMesh should track meaningful contribution.

Early contribution tracking can be simple.

Track things like:

- node ID
- job ID
- job type
- start time
- finish time
- success/failure
- result hash
- validation result
- runtime
- reported capabilities

Later, contribution tracking may include:

- uptime
- reliability
- task quality
- validation accuracy
- model hosted
- expert version served
- compute provided
- data contributed
- evals contributed
- improvement proposals
- accepted model upgrades

Do not add tokenomics before the system has useful work and validation.

---

## Decision Rule For Every Interval

Before choosing work, ask:

1. What key foundation is missing?
2. What small step improves runnability?
3. What small step improves clarity?
4. What small step enables future AER routing?
5. What small step enables future expert hosting?
6. What small step enables future validation?
7. What small step enables future contribution tracking?
8. What can be completed cleanly in one PR?

Then choose the best option.

The best interval is usually the one that makes AetherMesh more real, more runnable, more measurable, or easier to extend.

---

## Expected Output Every Interval

Each interval should produce one focused result:

- A clear plan
- A small implementation
- A PR or commit
- Tests or validation when appropriate
- Documentation if it clarifies the change

Every change should have a purpose and move the project closer to a working decentralized AI mesh.

Avoid unrelated changes, premature polish, or skipping validation.

---

## Current Priority Bias

When uncertain, prioritize:

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

---

## Final Vision

AetherMesh should become an open decentralized AI network where participants help host, route, validate, improve, and use the intelligence it produces.

The final system should not depend on one company, one server, one model, or one owner.

It should evolve toward:

- decentralized node participation
- replicated expert services
- adaptive expert routing
- validation-based trust
- measurable contribution
- community-improved AI
- usage benefits or rewards for useful work
- open infrastructure that people can understand and run

Start small.

Build real components.

Keep it open and understandable.

Validate work before rewarding it.

Route intelligently before claiming intelligence.

Ensure every interval moves the project toward AER, the REVA pipeline, and the Aether Expert Fabric.
