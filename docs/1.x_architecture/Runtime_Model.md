# 1.1 — Context OS Runtime Model

> Status: historical operational-flow artifact. The canonical architecture is
> [`1.0 Context OS Architecture`](1.0_COS_Architecture.md), and the canonical
> Runtime component view is
> [`1.4 Context Runtime Architecture`](1.4_COS_Context_Runtime_Architecture.md).
> This document is retained for traceability of the original repository
> runtime flow.

## Purpose

This document explains how **Context OS operates when installed inside a real project repository**. While the core framework defines the philosophy, architecture, and operational components of Context OS, the **Runtime Model** describes how those elements activate and interact with a live codebase.

In simple terms:

> The Runtime Model explains how Context OS moves from *framework* to *operational system*.

It defines how a repository is scanned, how context is constructed, how the Minimum Operational Map is established, and how agents operate on top of that structured context.

---

# Conceptual Runtime Flow

When Context OS is installed inside a project repository, the system follows a structured operational flow:

1. Context Discovery
2. Context Normalization
3. Context Graph Construction
4. Minimum Operational Map Bootstrapping
5. SSOT Initialization
6. Agentic Operating Model Activation
7. Governed Execution

The diagram below summarizes the runtime pipeline.

```
Project Repository
        │
        ▼
Context Discovery
        │
        ▼
Context Normalization
        │
        ▼
Context Graph
        │
        ▼
Minimum Operational Map
        │
        ▼
SSOT
        │
        ▼
Agentic Operating Model
        │
        ▼
Governed Execution
```

---

# 1. Context Discovery

The first stage of runtime execution is **repository discovery**.

Context OS scans the repository to identify relevant sources of context such as:

- Documentation
- Architecture files
- Product definitions
- Data models
- Agent definitions
- Code structure
- Configuration files

Typical inputs include:

- Markdown documents
- Architecture diagrams
- Database schemas
- Code modules
- Operational playbooks

The goal of this stage is to extract **raw contextual artifacts** from the repository.

This stage does **not attempt to interpret the project yet** — it simply discovers available knowledge.

---

# 2. Context Normalization

Once the repository has been scanned, the discovered artifacts must be mapped into the **Context OS taxonomy**.

Examples of normalization include:

```
Vision.md                → S.1_Vision
Architecture.md         → A.1_System_Map
DataModel.md            → A.4_Data_Entities
Roadmap.md              → P.1_Product_Map
```

If a required artifact is missing, Context OS identifies the gap and may request input from the user.

Example:

```
Missing artifact detected:
Definition_of_Ready
```

Normalization ensures that context is transformed from **unstructured documentation** into **structured system knowledge**.

---

# 3. Context Graph Construction

After normalization, Context OS constructs the **Context Graph**.

The Context Graph represents the relationships between core system elements such as:

- Vision
- Product capabilities
- System architecture
- Data entities
- Operational workflows

Example conceptual structure:

```
Vision
   │
   ├── Product Map
   │       ├── Feature A
   │       ├── Feature B
   │       └── Feature C
   │
   ├── System Map
   │       ├── Service Layer
   │       ├── Data Layer
   │       └── Integration Layer
   │
   └── Data Entities
           ├── Entity A
           ├── Entity B
           └── Entity C
```

This graph becomes the **semantic backbone of the project context**.

Agents use this structure to reason about dependencies, relationships, and system impact.

---

# 4. Minimum Operational Map Bootstrapping

Before agents can operate safely, the project must reach a **bootable context state**.

Context OS defines this minimal state as the **Minimum Operational Map (MOM)**.

The MOM requires the following artifacts:

- Vision
- Product Map
- System Map
- Data Entities
- Definition of Ready
- Definition of Done

If any of these components are missing, the system prompts the user to define them.

This ensures that the project reaches a **minimum level of contextual coherence** before execution begins.

---

# 5. SSOT Initialization

Once the MOM exists, Context OS establishes the **Single Source of Truth (SSOT)**.

The SSOT represents the **authoritative state of project context**.

Typical structure:

```
SSOT/

S.1_Vision.md
P.1_Product_Map.md
A.1_System_Map.md
A.4_Data_Entities.md
G.1_Definition_of_Ready.md
G.2_Definition_of_Done.md
```

From this point onward:

- All reasoning must reference SSOT
- Changes to system context must update SSOT
- Agents cannot override SSOT without validation

This mechanism prevents **context drift**.

---

# 6. Agentic Operating Model Activation

Once SSOT exists, the **Agentic Operating Model (AOM)** becomes active.

The core runtime roles include:

- Orchestrator
- Analysis Agent
- Execution Agent
- Verification Agent
- Context Guardian

Each agent operates under defined responsibilities:

### Orchestrator
Coordinates agent interaction and task flow.

### Analysis Agent
Interprets requests and evaluates system impact.

### Execution Agent
Applies modifications to artifacts, documentation, or code.

### Verification Agent
Ensures compliance with DoR, DoD, and architectural integrity.

### Context Guardian
Protects contextual coherence and prevents SSOT violations.

Together, these agents create a **structured reasoning loop**.

---

# 7. Governed Execution

With the runtime fully active, Context OS can safely process change requests.

Example workflow:

```
User request

"Add a new module for aerodynamic simulation"

Analysis Agent
        ↓
Evaluate impact on Product Map and System Map

Execution Agent
        ↓
Create artifacts and update architecture

Verification Agent
        ↓
Validate DoR and DoD

Context Guardian
        ↓
Confirm SSOT consistency

Result

Pull Request generated
```

This ensures that execution remains **context-aware and governed**.

---

# Runtime Design Principles

The Context OS Runtime Model follows several principles:

### Context First

Agents reason from structured context rather than improvisation.

### Minimum Bootable Context

Projects must reach the MOM state before agent execution begins.

### SSOT Authority

All system context must converge into a single authoritative representation.

### Evidence-Based Governance

Changes are validated through structural checks rather than trust.

### Human Alignment

Humans remain the strategic decision layer while agents augment execution.

---

# Relationship to Context Construction Loops

The runtime model interacts directly with the **Context Construction Loops** described in the Foundations layer.

| Loop | Runtime Interaction |
|-----|-----|
| Loop 0 | Anchors system purpose |
| Loop 1 | Discovery of repository context |
| Loop 2 | Guided construction of MOM and SSOT |
| Loop 3 | Continuous validation and drift detection |

Together, these loops ensure that context evolves **incrementally and coherently**.

---

# Runtime vs Framework

It is important to distinguish between:

Framework Layer

Defines concepts, structures, and operational rules.

Runtime Layer

Executes those rules inside a real project repository.

In this sense:

> Context OS is both a framework and a runtime system.

The framework defines how context should work.

The runtime ensures that context **actually governs execution**.

---

# Runtime CLI and Activation Layer

Context OS now has a Runtime CLI entry surface and a canonical Activation
Layer. The CLI begins with validation and expands through the product journey
as readiness, bootstrap, construction, activation, learning, and reasoning
slices mature.

Example commands:

```
contextos init
contextos scan
contextos build-mom
contextos build-ssot
contextos validate
```

This layer allows Context OS capabilities to become invokable inside a
repository while preserving governance and validation gates.

---

# Summary

The Runtime Model explains how Context OS moves from theory to operation.

The system activates through a sequence of steps:

1. Discover repository context
2. Normalize artifacts
3. Build the Context Graph
4. Establish the Minimum Operational Map
5. Initialize SSOT
6. Activate the Agentic Operating Model
7. Execute changes under governance

This structure allows Context OS to function as an **Organizational Context
Runtime** for complex projects and human-agent systems.
