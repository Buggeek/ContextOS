# Toolbox

The Toolbox defines the **operational capabilities** available to agents.

Tools enable agents to **act on the world**:
- read,
- write,
- execute,
- query,
- or interact with external systems.

Tools are permissioned and environment-dependent.

---

## What a Tool Is

A tool:
- performs actions,
- produces side effects,
- requires access control.

Examples:
- repository readers
- test runners
- database queries
- API clients

---

## What a Tool Is Not

A tool is not:
- a reasoning capability,
- a decision-maker,
- or a workflow.

If it thinks, it is not a tool.  
If it acts, it is not a skill.

---

## Tool Assignment

Tools are:
- enabled per mission,
- assigned by the Orchestrator,
- never assumed by default.

Least-privilege access applies.

---

## Governance

- Tools are audited
- Tool usage is traceable
- Tools are revoked if risk exceeds value

The Toolbox optimizes for **control over convenience**.