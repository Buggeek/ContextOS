# Context OS

**Context OS is an Organizational Context Runtime for human-agent systems.**

The canonical first-principles definition lives in
[`docs/0.x_foundations/0.8_COS_GENESIS.md`](docs/0.x_foundations/0.8_COS_GENESIS.md).

Not a tool.  
Not a framework for writing specs.  
Not a productivity hack.

Context OS is an attempt to formalize a layer that always existed in organizations, but was never designed explicitly:  
**the context in which intelligence operates.**

It does this by making context assessable, bootstrapable, constructable,
activatable, learnable, and usable for governed reasoning.

---

## Why Context OS exists

For a long time, intelligence was treated as an individual trait.

Talent.  
Experience.  
Good judgment.

But when working with teams, organizations, and now AI agents, a pattern becomes impossible to ignore:

> The same intelligent actors behave very differently depending on the context they operate in.

People, teams, and agents don’t “think” in isolation.  
They think **inside an environment of constraints, narratives, rules, and implicit knowledge**.

When that environment is unclear, fragmented, or implicit, intelligence degrades.  
When it is well designed, intelligence compounds.

Context OS starts from a simple premise:

> **Context is not documentation.  
> Context is infrastructure.**

---

## Intelligence scales with context, not talent

Organizations often rely on intuition, heroics, and institutional memory to function.

This works at small scale.  
It breaks as complexity grows.

AI doesn’t create this problem — it **reveals it**.

AI systems don’t compensate for missing context the way humans do.  
They amplify whatever is already there: clarity or ambiguity.

This is why many organizations experience more confusion after introducing AI, not less.

Context OS addresses this root issue.

---

## Context as an operating system

An operating system doesn’t do the work for you.

It defines:
- what can run,
- how components communicate,
- what is valid,
- and what is out of bounds.

Context works the same way for intelligence.

Context OS treats organizations as **distributed cognitive systems**, where humans and agents make decisions based on shared (or missing) context.

Design the context well, and intelligence aligns.  
Ignore it, and intelligence fragments.

---

## The Minimum Operational Map (MOM)

Context OS is intentionally minimal.

It introduces the concept of a **Minimum Operational Map** — the smallest set of contextual artifacts required for coherent operation:

- Vision
- Product Map
- System Map
- Core Data Entities
- Definition of Ready
- Definition of Done

If something doesn’t exist in the MOM, it does not exist operationally.

This is not bureaucracy.  
It’s cognitive alignment.

---

## Governance in an agentic world

When agents enter the picture, a critical shift happens.

Reasoning quality is no longer the main risk.  
**Verification is.**

Agents can reason well and still act incorrectly if context is incomplete or implicit.

This leads to a key principle of Context OS:

> **Governance must be evidence-based, not trust-based.**

Agents don’t “claim” correctness.  
They demonstrate it.

This is enforced through:
- explicit boundaries,
- proof-based execution,
- diff-based changes,
- and human review gates where necessary.

---

## How Context OS relates to other approaches

Context OS does not compete with existing specification frameworks.  
It operates at a different level.

### Spec-Driven Development
Spec-driven approaches improve execution by clarifying intent before implementation.

Context OS assumes this is valuable — but incomplete.

Specs need a **contextual environment** to make sense.

### OpenSpec
OpenSpec standardizes how specifications are written.

Context OS can *use* OpenSpec, but does not replace it.

OpenSpec defines artifacts.  
Context OS defines the system they live in.

### Context.space
Context.space recognizes the importance of context at a conceptual level.

Context OS extends this into:
- operational governance,
- agent execution,
- and evidence-based validation.

---

## What Context OS is (and is not)

Context OS **is**:
- an Organizational Context Runtime,
- a contextual operating system for intelligence,
- a governance model for agentic systems,
- a memory and activation layer for human-agent work,
- and a way to design intelligence environments.

Context OS **is not**:
- a SaaS product,
- a task manager,
- or a replacement for engineering discipline.

It is the layer above tools, specs, and agents.

---

## Open by design

Context OS is open source by intention.

Context should be inspectable.  
Governance should be auditable.  
Intelligence should be composable.

This repository contains:
- foundational concepts,
- document taxonomies,
- operational templates,
- runtime contracts,
- validator and CLI tooling,
- and example implementations.

---

## Repo Structure (Framework vs SSOT)

This repository contains **two distinct layers**:

- **Framework (this repo’s design)**: the conceptual and operational model in `/docs/`.
- **Implementation (an organization’s context)**: an `SSOT/` tree built using `/templates/`.

If you are adopting Context OS for an organization, you should create an `SSOT/` folder in your own repo (or a dedicated repo) and treat it as the governable system of record.

---

## The arc so far

Context OS is built around three core insights:

1. **Context is the operating system of intelligence.**
2. **AI amplifies the context it operates in.**
3. **Agents must be governed by evidence, not trust.**

Everything in this repository flows from those principles.

---

## Where this goes next

Context OS is still early.

Future work includes:
- Context Readiness Assessment implementation,
- guided bootstrap,
- context construction,
- activation surfaces,
- context memory,
- and governed human-agent workflows.

But none of that matters if the foundation is wrong.

This project starts at the root.

---

If you are exploring AI, agents, or complex organizations and feel that “something fundamental is missing,”  
this repository is an invitation to design that missing layer.

Context is no longer optional.  
It’s infrastructure.

---

## Getting Started

1. Read the foundational documents in `/docs/0.x_foundations/`
   - Start with `0.8_COS_GENESIS.md` for the canonical model
2. Review the architecture in `/docs/1.x_architecture/`
3. Understand taxonomy in `/docs/2.x_taxonomy/`
4. Build your Minimum Operational Map using `/docs/3.x_operation/`
5. Follow the Adoption Playbook in `/docs/4.x_adoption/`

Start simple.

Make your system visible.

Then evolve.

---

## Guiding Rule

Do not automate confusion.

Formalize context.
Then enable intelligence.
