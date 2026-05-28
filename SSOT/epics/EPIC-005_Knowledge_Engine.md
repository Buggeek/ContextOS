# EPIC-005 — Knowledge Engine

- **Epic ID:** EPIC-005
- **Version:** v0.3 — Runtime Foundation
- **Status:** Planned
- **Owner:** Runtime Owner

---

## Objective

Build the **Knowledge Engine v0**: the Runtime component that ingests
unstructured organizational documents, indexes them as **Raw Knowledge**, and
produces structured **Interpretations** that feed the Context Builder.

---

## Problem

Most organizations carry meaningful context in unstructured form (READMEs,
specs, decks, runbooks, design docs). Discovery captures *what exists*; the
Knowledge Engine captures *what it means*. Without an interpretation layer,
the Builder must rely solely on structured Discovery and SSOT.

---

## Scope

- Raw Knowledge ingestion (`contextos knowledge ingest`, surface declared
  as a CLI extension under EPIC-008 forward-looking).
- Document deduplication and stable identifiers.
- Interpretation pass producing typed drafts (entity candidates, role
  candidates, hypothesis candidates) with `belief_state = inferred`.
- Provenance trail back to source documents.

---

## Out of Scope

- General-purpose RAG agent.
- Conversational document Q&A.
- Long-term embeddings storage strategy (deferred to v0.5+).
- Multilingual normalization beyond English baseline.

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
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
