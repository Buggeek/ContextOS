# EPIC-005 — Knowledge Engine

- **Epic ID:** EPIC-005
- **Version:** v0.7/v0.8 — Context Health & Learning and Organizational Memory
- **Status:** Active for v0.8 planning
- **Owner:** Runtime Owner

---

## Product Journey Position

Knowledge Engine work is intentionally deferred until Context OS has a clear
structured-context path.

- v0.3 Context Readiness does not require unstructured interpretation.
- v0.5 Context Construction must first establish structured Discovery and
  Builder outputs.
- v0.7 Context Health & Learning introduces knowledge inputs where they help
  explain drift and remediation.
- v0.8 Organizational Memory expands this into durable knowledge and
  interpretation.
- Cocora knowledge-layer concepts converge into this epic. Memor.IA memory
  concepts converge into Context Memory, which the Knowledge Engine supports
  but does not replace.

---

## Objective

Build the **Knowledge Engine**: the Runtime component that ingests
unstructured organizational documents, indexes them as **Raw Knowledge**, and
produces structured **Interpretations** that feed the Context Builder.

The Knowledge Engine interprets meaning; Context Memory retains governed
beliefs, decisions, and historical context over time.

The canonical
[`Theory of the AI-Native Organization`](../../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md)
clarifies that Knowledge Engine is not Organizational Memory. It may produce
traceable interpretations for memory and construction, while Context Memory
owns continuity, temporal state, authority, supersession, retention, and prior
art.

---

## Problem

Most organizations carry meaningful context in unstructured form (READMEs,
specs, decks, runbooks, design docs). Discovery captures *what exists*; the
Knowledge Engine captures *what it means*. Without an interpretation layer,
the Builder must rely solely on structured Discovery and SSOT.

---

## Scope

v0.7 Context Health & Learning slice:

- Knowledge inputs that explain drift, stale context, and remediation
  opportunities.
- Provenance trail back to source documents.
- Clear separation between observed, inferred, and verified context.

v0.8 Organizational Memory expansion:

- Preserve Mission history, decisions, rationale, evidence, outcomes, and
  learning as governed memory inputs.
- Preserve context versions, temporal validity, supersession, retention, and
  governed forgetting.
- Keep retention governance separate from interpretation: policy resolution
  may constrain Knowledge inputs and outputs, but Knowledge Engine cannot
  classify sensitivity, resolve holds, or authorize forgetting autonomously.
- Produce prior-art and pattern/consolidation candidates with explicit
  applicability and provenance.
- Raw Knowledge ingestion (`contextos knowledge ingest`, surface declared
  as a CLI extension under EPIC-008 forward-looking).
- Document deduplication and stable identifiers.
- Interpretation pass producing typed drafts (entity candidates, role
  candidates, hypothesis candidates) with epistemic support `inferred`; any
  v0.x `belief_state` field is a compatibility alias for this axis only.
- Durable memory traversal support.

---

## Out of Scope

- General-purpose RAG agent.
- Conversational document Q&A.
- Long-term embeddings storage strategy beyond the first memory slice.
- GraphRAG unless memory retrieval evidence proves it is required.
- Automatic consolidation into canonical processes, skills, tools, roles,
  policies, or team patterns.
- Multilingual normalization beyond English baseline.
- Any v0.3 readiness dependency.

---

## Expected Outcomes

- A small organization's existing document corpus produces interpretation
  drafts that the Builder can consume to compose MOM artifacts.
- Every interpretation cites its source document and span.
- Inferred nodes are clearly distinguished from observed nodes at the
  graph level (see Context Graph Schema §Status Tags).

---

## Dependencies

- [`../../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md`](../../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md)
- [`../../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md`](../../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) §Step 4–5
- EPIC-008 (CLI skeleton) for ingestion surface.

---

## Success Criteria

- Ingestion is idempotent: identical input produces identical Raw Knowledge
  entries.
- Interpretation output validates against the declared draft schema.
- Every inferred node carries `provenance.from_artifact` and a non-null
  confidence score.
- Conflicts between inferred drafts and existing SSOT are reported, not
  silently overridden.

---

## Definition of Ready (DoR)

- Raw Knowledge index schema is frozen.
- Interpretation draft schema is frozen.
- Sample corpora identified under `examples/` for evaluation.
- Belief-state semantics match `0.7 Context Versioning and Memory`.

---

## Definition of Done (DoD)

- Ingestion + interpretation pipeline runs end-to-end on the
  `examples/sample_mid_size_org` corpus.
- All produced drafts traceable to source documents.
- Builder (EPIC-006) consumes the output without per-source branching.
- `knowledge.ingested` and `knowledge.interpreted` events emitted per the
  Runtime Event Model.

---

## Related Artifacts

- [`../../docs/0.x_foundations/0.5_COS_Context_Construction_Loops.md`](../../docs/0.x_foundations/0.5_COS_Context_Construction_Loops.md)
- [`../../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md`](../../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md)
- [`../../docs/1.x_architecture/1.0_COS_Architecture.md`](../../docs/1.x_architecture/1.0_COS_Architecture.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
