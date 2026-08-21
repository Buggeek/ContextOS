# E.5 Evolution Inbox
## Version: 0.1.0
Last Updated: 2026-08-21
Owner: Context OS Maintainers
Status: Active

---

## Purpose

Capture ideas, discoveries, risks, technical debt, opportunities, and
hypotheses that emerge during Context OS execution without allowing them to
disrupt the active mission.

The Evolution Inbox is not a roadmap, backlog, or approval queue. It is a
quarantine and triage surface for context that may deserve future action.

---

## Intake Rules

1. Inbox items must not change the scope of the active mission.
2. Every item must declare a source mission or source observation.
3. Items must be triaged before they become roadmap, epic, release, or mission
   work.
4. Items that require authority must remain `decision-needed` until a human
   owner accepts, rejects, or defers them.
5. Items promoted to execution must link to a Mission Packet.
6. Items may be deleted only through a recorded governance decision; otherwise
   they should be marked `rejected` or `superseded`.

---

## Triage States

| State | Meaning |
|---|---|
| new | Captured but not reviewed |
| accepted | Worth preserving, but not yet scheduled |
| decision-needed | Requires human authority before action |
| linked-to-mission | Promoted into a Mission Packet |
| deferred | Intentionally postponed |
| rejected | Reviewed and declined |
| superseded | Replaced by a better item or completed artifact |

---

## Inbox Items

| ID | Type | State | Source | Summary | Suggested disposition |
|---|---|---|---|---|---|
| INBOX-001 | technical-debt | accepted | SELFHOST-001 | Mission Packet and Evolution Inbox templates are missing. | Defer until two mission packets have been executed and audited. |
| INBOX-002 | architecture | linked-to-mission | SELFHOST-001 | Guided Bootstrap apply must define approval, evidence, and rollback before any write-capable `init` behavior. | Represented by V04-BOOTSTRAP-APPLY-001. |
| INBOX-003 | product-risk | accepted | SELFHOST-001 | Mission Runtime and `contextos mission` are tempting but premature for v0.4. | Revisit during Activate or Human-Agent Runtime releases. |
| INBOX-004 | governance | decision-needed | SELFHOST-001 | Mission closure could eventually require a first-class authority ledger entry for L3+ agent actions. | Decide before automating Mission Runtime. |
| INBOX-005 | taxonomy | accepted | SELFHOST-001 | E.4 and E.5 were added before templates exist. | Keep explicit template deferral until mission artifact shape stabilizes. |
| INBOX-006 | implementation | accepted | V04-BOOTSTRAP-APPLY-001 | A read-only Bootstrap Proposal generator is needed before any apply implementation. | Promote to the next v0.4 mission. |
| INBOX-007 | governance | accepted | V04-BOOTSTRAP-APPLY-001 | Apply approval needs durable Decision Record and Ledger support, but Mission Runtime does not exist yet. | Use mission evidence and commit history temporarily; require ledger integration before automated Mission Runtime. |
| INBOX-008 | product-risk | accepted | V04-BOOTSTRAP-APPLY-001 | Users may expect `contextos init` to write files. | Preserve read-only default and require an explicit proposal-approved apply surface. |
| INBOX-009 | technical-debt | accepted | V04-BOOTSTRAP-APPLY-001 | Proposal canonical hashing and repository fingerprinting need deterministic implementation rules. | Define during Bootstrap Proposal Engine implementation. |
| INBOX-010 | governance | deferred | V04-BOOTSTRAP-APPLY-001 | Replacement or overwrite actions are prohibited for v0.4 but may be needed later for repair workflows. | Revisit after create-only apply is proven. |
| INBOX-011 | implementation | superseded | V04-BOOTSTRAP-PROPOSAL-001 | Proposal persistence and CLI exposure are not implemented. | CLI exposure and user-selected JSON-out implemented by V04-BOOTSTRAP-PROPOSAL-REVIEW-001; durable approval storage remains future work. |
| INBOX-012 | technical-debt | accepted | V04-BOOTSTRAP-PROPOSAL-001 | Proposal identity currently depends on canonical JSON hashing and repository fingerprints; schema changes must preserve compatibility or version the proposal. | Treat breaking hash changes as proposal schema changes. |
| INBOX-013 | governance | accepted | V04-BOOTSTRAP-PROPOSAL-001 | Future proposal approval should require a clean repository state or an explicit dirty-state waiver. | Decide in the approval/persistence mission before apply. |
| INBOX-014 | implementation | superseded | V04-BOOTSTRAP-PROPOSAL-001 | Proposal engine has no human renderer yet. | Implemented by V04-BOOTSTRAP-PROPOSAL-REVIEW-001. |
| INBOX-015 | governance | accepted | V04-BOOTSTRAP-PROPOSAL-REVIEW-001 | Approval needs a read-only Decision/Approval record that binds proposal id, identity hash, approvers, authority mode, and expiry before apply exists. | Promote to the next v0.4 mission. |
| INBOX-016 | implementation | accepted | V04-BOOTSTRAP-PROPOSAL-REVIEW-001 | Proposal review has JSON-out preservation but no first-class approval-state transition command. | Define approval record before apply implementation. |
| INBOX-017 | governance | linked-to-mission | V04-BOOTSTRAP-APPROVAL-001 | Approval record draft exists, but accepted approval still requires an explicit human authority action. | Represented by V04-BOOTSTRAP-APPROVAL-ACCEPT-001. |
| INBOX-018 | implementation | superseded | V04-BOOTSTRAP-APPROVAL-001 | Approval records are generated from proposal files but are not yet persisted as immutable Decision Records. | Accepted decision output now embeds `contextos.decision/1`; durable ledger storage remains future work. |
| INBOX-019 | technical-debt | accepted | V04-BOOTSTRAP-APPROVAL-001 | Proposal drift comparison previously used path tree hash instead of full fingerprint hash. | Fixed in this mission; keep regression coverage. |
| INBOX-020 | implementation | linked-to-mission | V04-BOOTSTRAP-APPROVAL-ACCEPT-001 | Future apply must consume an accepted decision artifact and revalidate proposal identity, source plan hash, repository fingerprint, file hashes, and drift before any mutation. | Represented by V04-BOOTSTRAP-APPLY-PREFLIGHT-001. |
| INBOX-021 | governance | accepted | V04-BOOTSTRAP-APPROVAL-ACCEPT-001 | Accepted decisions are portable JSON artifacts but not yet written to an Accountability Ledger. | Require ledger integration before automated Mission Runtime or multi-actor apply. |
| INBOX-022 | implementation | linked-to-mission | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | Future apply should consume a fresh eligible preflight report, not an accepted decision directly. | Represented by V04-BOOTSTRAP-APPLY-CREATE-ONLY-001. |
| INBOX-023 | governance | linked-to-mission | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | A successful preflight establishes eligibility but still does not provide final human apply confirmation. | Represented by V04-BOOTSTRAP-APPLY-CREATE-ONLY-001. |
| INBOX-024 | governance | decision-needed | V04-BOOTSTRAP-APPLY-CREATE-ONLY-001 | A real apply against the canonical Context OS repository requires target-specific human authorization bound to exact proposal, accepted decision, and fresh preflight. | Decide after release verification; do not infer from implementation authority. |
| INBOX-025 | product-risk | deferred | V04-BOOTSTRAP-APPLY-CREATE-ONLY-001 | Repair, overwrite, replacement, and deletion workflows are intentionally excluded from v0.4 create-only apply. | Revisit after create-only apply is proven in real target use. |
| INBOX-026 | governance | decision-needed | V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001 | v0.4 is release-ready without canonical Context OS apply, but maintainers may still choose to run canonical apply as a separate target-specific decision. | Do not block release; require exact target authorization if pursued. |
| INBOX-027 | product | accepted | V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001 | v0.5 should start from construction tasks derived from readiness/bootstrap evidence rather than broad Knowledge Engine scope. | Promote to v0.5 planning mission. |
| INBOX-028 | implementation | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | `contextos.construction.plan/1` needs a future Runtime CLI surface before non-developer users can request construction plans directly. | Consider after the planning engine is audited; do not add before the first Builder draft mission is shaped. |
| INBOX-029 | architecture | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | Construction planning currently uses the standard MOM artifact set; future organizational operations will need domain-specific artifact mappings without changing the lifecycle model. | Defer until the first non-technology operating-domain construction slice. |
| INBOX-030 | implementation | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | Full Discovery Bundle remains required before Builder draft generation can safely use source observations beyond existing inventory/readiness/bootstrap evidence. | Promote to the next v0.5 mission. |
| INBOX-031 | implementation | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | `contextos scan` and source registry remain absent even though the local Discovery Bundle engine exists. | Defer until the engine is consumed by the first Builder draft mission or a user-facing construction CLI mission. |
| INBOX-032 | architecture | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | Discovery currently captures literal local links and containment only; semantic relationships must wait for Knowledge/Graph maturity. | Preserve as a boundary for v0.5; revisit in Organizational Memory. |
| INBOX-033 | implementation | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | Builder draft generation now has a stable local discovery input and should be shaped next without external connectors. | Promote to the next v0.5 mission. |
| INBOX-034 | implementation | accepted | V05-BUILDER-DRAFT-PLAN-001 | Builder Draft Plan has no Runtime CLI surface, so users cannot request it directly yet. | Consider a read-only construction CLI only after the first Builder write boundary is decided. |
| INBOX-035 | governance | accepted | V05-BUILDER-DRAFT-PLAN-001 | Write-capable Builder draft creation will require an explicit authority and no-overwrite model similar to Guided Bootstrap apply. | Promote before any `build-mom` or `build-ssot` write behavior. |
| INBOX-036 | architecture | accepted | V05-BUILDER-DRAFT-PLAN-001 | Confidence/support levels are planning aids and need a stable taxonomy before cross-domain Builder expansion. | Defer until first non-technology context construction slice or Builder draft generation hardening. |
| INBOX-037 | implementation | accepted | V05-BUILDER-DRAFT-AUTHORITY-001 | Builder draft writes need an implementation object equivalent to preflight/authorization before any file creation occurs. | Promote to the next v0.5 mission if write-capable draft behavior is authorized. |
| INBOX-038 | governance | decision-needed | V05-BUILDER-DRAFT-AUTHORITY-001 | The exact draft surface for future Builder writes is not yet selected. | Human authority should choose branch/worktree/scratch/draft directory before implementation. |
| INBOX-039 | implementation | accepted | V05-BUILDER-DRAFT-AUTHORITY-001 | Builder Draft Authority should eventually be enforced by tests and runtime preflight rather than documentation only. | Implement in the next Builder write-boundary mission. |
| INBOX-040 | implementation | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Local Draft Workspace support needs a runtime object that resolves `.contextos/drafts/` paths and enforces non-canonical scope. | Promote before first draft write implementation. |
| INBOX-041 | governance | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Draft retention, cleanup, and expiration policy needs more precise defaults after drafts exist. | Defer until draft artifacts are produced and audited. |
| INBOX-042 | architecture | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Future non-filesystem Draft Workspace adapters should preserve the same conceptual model across document, CRM, legal, finance, people, and data systems. | Defer until Activation or connector work. |
| INBOX-043 | implementation | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Future Builder draft creation should consume `contextos.builder.draft_workspace_preflight/1` rather than a raw Builder Draft Plan. | Promote when explicit write-capable Builder authority is granted. |
| INBOX-044 | product | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Builder Draft Plan and Draft Workspace preflight remain developer-only surfaces without Runtime CLI exposure. | Consider after first write-capable draft behavior is proven. |
| INBOX-045 | technical-debt | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Draft Workspace local mapping is fixed to `.contextos/drafts/`; future configurable workspace mappings need authority and adapter rules. | Defer until non-filesystem or multi-workspace runtime appears. |
| INBOX-046 | product | accepted | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | Builder draft creation exists as an engine but has no user-facing CLI surface. | Promote to a governed CLI/review mission only after canonical target authorization is decided. |
| INBOX-047 | implementation | accepted | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | The first draft artifact is a non-canonical envelope without generated domain content. | Future Builder content generation must remain evidence-supported and separately authorized. |
| INBOX-048 | governance | decision-needed | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | Creating a real draft in the canonical Context OS repository requires target-specific authority bound to exact preflight, draft item, and path. | Do not infer from implementation authority; require explicit human decision. |
| INBOX-049 | product | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | Draft review exists as an engine/human renderer but has no CLI or user-facing workflow surface. | Consider after review-decision authority is defined. |
| INBOX-050 | governance | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | A future review decision must persist separately from review rendering and must not imply approval or promotion. | Promote before any approval/promotion mission. |
| INBOX-051 | UX | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | Future review surfaces should visually separate observed, inferred, suggested, drafted, unknown, and approved truth states. | Defer to CLI/web/IDE review surface design. |
| INBOX-052 | product | accepted | V05-BUILDER-DRAFT-REVIEW-DECISION-001 | Review Decision exists as an engine/object but has no user-facing CLI or workflow surface. | Consider after the next lifecycle transition is defined. |
| INBOX-053 | governance | accepted | V05-BUILDER-DRAFT-REVIEW-DECISION-001 | Approval and promotion must consume exact Review Decisions without regenerating draft intent or treating review as approval. | Promote before any draft approval or canonical SSOT mutation mission. |
| INBOX-054 | product | accepted | V05-BUILDER-DRAFT-APPROVAL-DECISION-001 | Approval Decision exists as an engine/object but has no user-facing CLI or workflow surface. | Consider after promotion preflight is defined. |
| INBOX-055 | governance | accepted | V05-BUILDER-DRAFT-APPROVAL-DECISION-001 | Promotion must consume exact Approval Decisions and still require separate authority, validation, and canonical write boundaries. | Promote before any SSOT or canonical context mutation mission. |
| INBOX-056 | governance | accepted | V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001 | Promotion Preflight can establish eligibility, but human promotion confirmation and canonical mutation authority remain separate. | Promote before any Builder canonical write mission. |
| INBOX-057 | implementation | accepted | V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001 | Promotion Preflight, Approval Decision, Review Decision, and Draft Review remain engine-only surfaces without Runtime CLI workflow. | Consider a construction workflow CLI after promotion execution boundaries are decided. |
| INBOX-058 | governance | accepted | V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001 | Existing canonical targets remain blocked because governed replacement execution is not yet defined. | Promote only when replacement/overwrite authority is explicitly required. |
| INBOX-059 | product | accepted | V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001 | Promotion execution exists as an engine but has no user-facing construction CLI workflow. | Consider after v0.5 release verification clarifies the minimum usable construction surface. |
| INBOX-060 | product | accepted | V05-CONTEXT-CONSTRUCTION-RELEASE-VERIFY-001 | v0.5 is release-ready as an engine/API lifecycle, but the construction journey is not yet exposed as a user-facing CLI workflow. | Defer to a post-release construction UX mission or v0.6 activation planning; do not block v0.5 release cut. |
| INBOX-061 | governance | accepted | V05-CONTEXT-CONSTRUCTION-RELEASE-VERIFY-001 | Existing canonical targets are intentionally blocked from replacement; governed replacement promotion remains outside v0.5 scope. | Define only when an explicit user need requires replacement rather than create-only construction. |
| INBOX-062 | product | accepted | V06-CONTEXT-ACTIVATION-PLAN-001 | Activation Package exists as an engine/API but has no Runtime CLI surface. | Promote to the next v0.6 mission as a narrow read-only CLI surface. |
| INBOX-063 | architecture | accepted | V06-CONTEXT-ACTIVATION-PLAN-001 | Activation source selection is intentionally heuristic and local; richer relevance, audience profiles, and context budgeting need evidence from actual package use. | Defer until CLI dogfooding produces usage evidence; do not add Knowledge Engine or Graph selection yet. |
| INBOX-064 | product | accepted | V06-CONTEXT-ACTIVATION-PLAN-001 | IDE, Claude Code, Codex, workflow, and non-technology organizational adapters will need the same package identity and invalidation model. | Defer adapters until the package CLI is stable and audited. |
| INBOX-065 | product | accepted | V06-ACTIVATION-PACKAGE-CLI-001 | The package CLI can produce and check working context, but Context OS has not yet executed a mission that formally starts from a package artifact. | Promote to the next v0.6 mission to prove package-first self-hosted execution. |
| INBOX-066 | UX | accepted | V06-ACTIVATION-PACKAGE-CLI-001 | Activation Package human output is inspectable but not yet optimized as a compact prompt handoff for Codex, Claude Code, or IDE assistants. | Defer until package-first mission execution reveals the minimum handoff format. |
| INBOX-067 | architecture | accepted | V06-ACTIVATION-PACKAGE-CLI-001 | Package selection currently records exclusions but does not explain per-source ranking scores. | Defer until selection tuning is needed; avoid broad RAG or Graph selection in v0.6 slice 2. |
| INBOX-068 | UX | accepted | V06-ACTIVATION-PACKAGE-USE-001 | Package-first execution works, but future consumers need a compact package-backed handoff format that names package id, validity, goal, selected sources, gaps, and allowed actions. | Promote to the next v0.6 mission before IDE or agent adapters. |
| INBOX-069 | implementation | accepted | V06-ACTIVATION-PACKAGE-USE-001 | Source edits during a package-first Mission invalidate the package used to start that Mission. | Require a fresh package check before a follow-on Mission uses changed context. |
| INBOX-070 | UX | accepted | V06-ACTIVATION-HANDOFF-FORMAT-001 | Package-backed handoff exists, but future consumers may need adapter-specific renderers for Codex, Claude Code, IDE assistants, web, or workflow surfaces. | Defer until the universal handoff is proven in another real Mission; adapters must preserve the same machine schema. |
| INBOX-071 | architecture | accepted | V06-ACTIVATION-HANDOFF-FORMAT-001 | Current activation selection can orient product and contract work, but implementation missions still need runtime/test file reads outside selected canonical sources. | Consider a bounded source-selection improvement before v0.6 release verification; do not add broad RAG or Graph runtime. |
| INBOX-072 | product | accepted | V06-ACTIVATION-HANDOFF-FORMAT-001 | Handoff-first execution should be measured against a future Mission that starts from a handoff id/reference plus a short instruction. | Promote to the next v0.6 mission. |
| INBOX-073 | architecture | accepted | V06-ACTIVATION-HANDOFF-USE-001 | Handoff-first execution showed that governing context and execution context are distinct layers; implementation work required runtime/test files beyond the selected governing package. | Consider a bounded governing/execution context-layer mission before release verification if needed; preserve one coherent Mission context model. |
| INBOX-074 | product | accepted | V06-ACTIVATION-HANDOFF-USE-001 | Saved handoff checks now exist, but v0.6 still lacks release-level verification across package, handoff, handoff check, and a real handoff-first Mission journey. | Promote after any required context-layer refinement. |
| INBOX-075 | architecture | accepted | V06-ACTIVATION-CONTEXT-LAYERS-001 | Future activation may need ranked execution-context retrieval suggestions, but v0.6 should not add broad RAG, Graph runtime, Knowledge Engine ranking, or adapters. | Defer until release verification proves a real blocker; preserve bounded retrieval evidence first. |
| INBOX-076 | product | accepted | V06-ACTIVATION-CONTEXT-LAYERS-001 | v0.6 now has package, check, handoff, handoff check, handoff-first execution, and Mission Context layers; release verification is the next product gate. | Promote to V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001. |
| INBOX-077 | architecture | accepted | V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001 | The canonical Activation Package Contract must not be displaced by keyword-rich prior-release Mission history in a bounded governing package. | Keep the contract as baseline activation authority and preserve the release-verification selector test. |
| INBOX-078 | product | accepted | V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001 | Consumer-specific adapters, IDE integrations, agent orchestration, Graph, Knowledge ranking, broad RAG, learned ranking, and background synchronization are not required for the v0.6 product promise. | Keep deferred; admit only through evidence-backed future release Missions. |
| INBOX-079 | product | accepted | V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001 | v0.6 is release-ready through the universal CLI/API, package, handoff, checks, and self-hosted consumers. | Require explicit human release-cut authority; then re-anchor on v0.7 Context Health & Learning. |
| INBOX-080 | product | accepted | V06-RELEASE-CUT-001 | v0.6 release authority was granted after fresh package/handoff and full regression evidence remained green. | Close v0.6 and re-anchor on V07-CONTEXT-HEALTH-PLAN-001 without beginning implementation during release cut. |
| INBOX-081 | architecture | accepted | V07-CONTEXT-HEALTH-PLAN-001 | Integrity, usefulness, and learning are explainable dimensions of one Health Report; separate engines and an aggregate score are not justified. | Preserve one read-only `contextos.health.report/1`; add scoring only after calibrated decision evidence exists. |
| INBOX-082 | evidence | accepted | V07-CONTEXT-HEALTH-PLAN-001 | Mission learning and activation use are mostly narrative, so Health cannot prove per-source consumption or causal effectiveness. | Promote to V07-CONTEXT-USE-EVIDENCE-001 before trend or effectiveness claims. |
| INBOX-083 | governance | accepted | V07-CONTEXT-HEALTH-PLAN-001 | Health candidates must not become a second path to canonical truth. | Route accepted candidates through the existing v0.5 Construction lifecycle with human review. |
| INBOX-084 | product | deferred | V07-CONTEXT-HEALTH-PLAN-001 | A `contextos health` CLI would make the report directly user-accessible. | Consider after the Health schema and Mission-use evidence input are validated; do not duplicate engine logic. |
| INBOX-085 | architecture | deferred | V07-CONTEXT-HEALTH-PLAN-001 | Trends, degradation, and improvement require explicit prior reports or structured historical evidence. | Do not infer trends from one report; define comparison only after evidence capture exists. |
| INBOX-086 | evidence | accepted | V07-CONTEXT-USE-EVIDENCE-001 | Explicit access and contribution records improve traceability but cannot prove cognitive consumption or causal usefulness. | Preserve `usefulness_effect: unknown` until an explicit declared or independently observed usefulness assertion exists. |
| INBOX-087 | product | accepted | V07-CONTEXT-USE-EVIDENCE-001 | Health and Mission-use evidence remain API/report surfaces without a user-facing Runtime CLI. | Promote a narrow `contextos health` surface as the next v0.7 product Mission; do not duplicate engine logic. |
| INBOX-088 | architecture | deferred | V07-CONTEXT-USE-EVIDENCE-001 | The Mission-bound Activation Package oriented the work but omitted the exact Health contract required for execution. | Use this as future selector evidence; do not add ranking, Graph, or broad retrieval in the active Mission. |
| INBOX-089 | product | accepted | V07-CONTEXT-HEALTH-CLI-001 | Context Health is now directly consumable as a read-only human and machine report through the Runtime CLI. | Verify the complete v0.7 product journey before adding more Health capability. |
| INBOX-090 | evidence | deferred | V07-CONTEXT-HEALTH-CLI-001 | Structured Mission-use evidence is accepted as an explicit report input, but no automatic capture workflow exists. | Do not introduce telemetry; evaluate whether explicit capture ergonomics block release during v0.7 verification. |
| INBOX-091 | UX | deferred | V07-CONTEXT-HEALTH-CLI-001 | Large evidence lists are accurate but may need progressive disclosure in future interactive surfaces. | Preserve complete CLI evidence now; defer dashboards and adapter-specific presentation until demonstrated need. |
| INBOX-092 | architecture | deferred | V07-CONTEXT-HEALTH-RELEASE-VERIFY-001 | Historical comparison and trend reporting are not required to truthfully assess present Health or produce evidence-backed update candidates. | Defer until multiple preserved reports demonstrate a decision need; do not expand v0.7. |
| INBOX-093 | UX | accepted | V07-CONTEXT-HEALTH-RELEASE-VERIFY-001 | Human evidence lists were accurate but too diagnostic for first-pass assessment. | Keep bounded evidence previews in human output and preserve complete references in JSON. |
| INBOX-094 | product | accepted | V07-CONTEXT-HEALTH-RELEASE-VERIFY-001 | v0.7 satisfies its read-only Health & Learning promise without remediation, canonical updates, or historical comparison. | Require explicit human release-cut authority, then re-anchor on v0.8 Organizational Memory. |
| INBOX-095 | product | superseded | V07-RELEASE-CUT-001 | v0.7 release authority was granted after the package-bound release decision and full regression evidence remained green. | v0.7 was closed and the separate foundational authority was exercised through THEORY-AI-NATIVE-ORGANIZATION-V01. |
| INBOX-096 | architecture | accepted | THEORY-AI-NATIVE-ORGANIZATION-V01 | Direction, Context and Memory, Sense and Activate, Organize and Execute, Measure and Learn, and Govern and Evolve are six concurrent organizational planes rather than a sequential architecture. | Use the six-plane theory to evaluate v0.8-v1.0 without replacing GENESIS or Runtime architecture. |
| INBOX-097 | architecture | deferred | THEORY-AI-NATIVE-ORGANIZATION-V01 | GraphRAG may support relationship-aware retrieval and reasoning, but current evidence does not prove it is required for Organizational Memory. | Admit GraphRAG only through a future evidence-backed Mission; keep Context Graph derived and Activation authoritative for packaging. |
| INBOX-098 | hypothesis | accepted | THEORY-AI-NATIVE-ORGANIZATION-V01 | The universal organizational model is mapped across domains but has not been validated through a non-Technology Context OS implementation. | Preserve as not-yet-tested until a governed external domain implementation produces evidence. |
| INBOX-099 | governance | decision-needed | THEORY-AI-NATIVE-ORGANIZATION-V01 | v0.8 requires operational retention and forgetting semantics across continuity, privacy, legal, cost, and audit needs. | Resolve policy boundaries before any destructive compaction or forgetting behavior is implemented. |
| INBOX-100 | product | accepted | THEORY-AI-NATIVE-ORGANIZATION-V01 | The first v0.8 capability should establish governed memory continuity from existing Missions, decisions, evidence, outcomes, learning, and context versions before unstructured interpretation or graph retrieval. | Promote to V08-ORGANIZATIONAL-MEMORY-PLAN-001 under separate human authority. |
| INBOX-101 | architecture | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | The fresh v0.8 Activation Package omitted the newly canonical Theory and Context Versioning and Memory foundation despite their explicit roadmap authority. | Treat both as bounded Execution Context now; improve selection only through a future evidence-backed Activation Mission. |
| INBOX-102 | governance | decision-needed | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | Retention cannot mean either silent deletion or unconditional permanent storage; sensitivity, ownership, expiration, legal hold, archival, recovery, and deliberate forgetting remain undecided. | Prohibit destructive retention behavior and resolve policy before any retention/forgetting implementation. |
| INBOX-103 | product | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | The Memory Continuity API/report proves the model, but a user still needs a bounded retrieval surface for prior decisions, rationale, learning, supersession, and Mission prior art. | Promote to V08-MEMORY-RETRIEVAL-SURFACE-001 without adding semantic reasoning or GraphRAG. |
| INBOX-104 | evidence | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | Mission artifacts do not consistently cite immutable context-version objects, so historical governing context cannot always be reconstructed exactly. | Preserve as an explicit continuity gap; define capture requirements before claiming complete historical replay. |
| INBOX-105 | hypothesis | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | Deterministic term overlap can surface explainable prior art, but selection does not prove applicability or usefulness. | Test through the next user-facing Memory retrieval Mission; do not introduce learned ranking yet. |
| INBOX-106 | hypothesis | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | Recurring authority, evidence, drift, read-only, and truth-boundary themes appear across Mission Learning records. | Keep as non-canonical pattern candidates until governed review and external reuse evidence exist. |
| INBOX-107 | evidence | accepted | V08-ORGANIZATIONAL-MEMORY-PLAN-001 | v0.3 and v0.4 predate explicit release-cut Mission records, while v0.5-v0.7 preserve release transitions through closed Mission evidence. | Keep the historical gap explicit; do not reconstruct missing release decisions from Git chronology alone. |
| INBOX-108 | architecture | accepted | V08-MEMORY-RETRIEVAL-SURFACE-001 | The fresh retrieval-Mission Activation Package selected the Memory Continuity Mission but omitted the canonical Theory and current Memory contracts. | Use explicit authorities as bounded Execution Context; improve Activation selection only through separate evidence-backed work. |
| INBOX-109 | evidence | accepted | V08-MEMORY-RETRIEVAL-SURFACE-001 | Structured retrieval explains why a candidate was selected but cannot independently prove applicability or causal usefulness. | Preserve applicability as candidate and usefulness as unproven; capture explicit consumer use evidence before stronger claims. |
| INBOX-110 | architecture | accepted | V08-MEMORY-RETRIEVAL-SURFACE-001 | Mission lineage, evidence references, and context-version relationships are not uniformly structured across historical Mission records. | Keep deterministic term/metadata retrieval bounded; improve capture contracts before adding Graph or semantic ranking. |
| INBOX-111 | evidence | accepted | V08-MEMORY-RETRIEVAL-SURFACE-001 | Memor.IA convergence is canonical in GENESIS and architecture, but earlier personal-memory rationale is not preserved as explicit Mission memory. | Treat current canon as Governing Context and record historical rationale as unavailable; do not reconstruct it from recency or narrative fragments. |
| INBOX-112 | architecture | deferred | V08-MEMORY-RETRIEVAL-SURFACE-001 | Bounded structured retrieval surfaces relevant continuity and explicit supersession without GraphRAG, embeddings, vector search, or Knowledge reasoning. | Keep advanced retrieval deferred until measured use evidence demonstrates a concrete failure of structured retrieval. |
| INBOX-113 | governance | decision-needed | V08-MEMORY-RETRIEVAL-SURFACE-001 | v0.8 now exposes continuity and retrieval, but retention, sensitivity, expiration, archival, legal/compliance, recovery, and deliberate forgetting remain undecided. | Promote to V08-MEMORY-RETENTION-GOVERNANCE-001 under separate human governance authority. |

---

## Change Log

- 2026-08-11 - v0.1.0 - Added Guided Bootstrap apply approval follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Engine follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Review Surface follow-up
  items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Approval Record follow-up items.
- 2026-08-11 - v0.1.0 - Created Evolution Inbox for self-hosted execution.
- 2026-08-11 - v0.1.0 - Added Context Construction planning follow-up items.
- 2026-08-11 - v0.1.0 - Added Local Discovery Bundle follow-up items.
- 2026-08-11 - v0.1.0 - Added Builder Draft Planning follow-up items.
- 2026-08-11 - v0.1.0 - Added Builder Draft Authority follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Workspace decision follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Workspace runtime follow-up items.
- 2026-08-11 - v0.1.0 - Added create-only Builder draft write follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Review Surface follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Review Decision follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Approval Decision follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Promotion Preflight follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Promotion Execute follow-up items.
- 2026-08-11 - v0.1.0 - Added Context Construction release verification follow-up items.
- 2026-08-11 - v0.1.0 - Added Context Activation Package follow-up items.
- 2026-08-11 - v0.1.0 - Added Activation Package CLI follow-up items.
- 2026-08-11 - v0.1.0 - Added package-first Mission execution follow-up items.
- 2026-08-11 - v0.1.0 - Added package-backed Activation Handoff follow-up items.
- 2026-08-11 - v0.1.0 - Added handoff-first Mission execution follow-up items.
- 2026-08-11 - v0.1.0 - Added Mission Context layers follow-up items.
- 2026-08-13 - v0.1.0 - Added Context Activation release verification
  decisions and deferrals.
- 2026-08-13 - v0.1.0 - Recorded the v0.6 release cut and v0.7 re-anchor.
- 2026-08-15 - v0.1.0 - Added first Context Health & Learning findings and
  next evidence dependency.
- 2026-08-16 - v0.1.0 - Added Mission-use observability limits, Health CLI
  opportunity, and bounded selector evidence.
- 2026-08-20 - v0.1.0 - Recorded Health CLI delivery, explicit evidence-input
  ergonomics, and future presentation opportunity.
- 2026-08-20 - v0.1.0 - Recorded v0.7 release decisions, bounded human
  evidence previews, and historical comparison deferral.
- 2026-08-20 - v0.1.0 - Recorded the v0.7 release cut, preserved intentional
  deferrals, and re-anchored on v0.8 Organizational Memory.
- 2026-08-20 - v0.1.0 - Recorded the AI-native organizational model,
  GraphRAG boundary, universal-model hypothesis, retention decision, and first
  v0.8 Mission dependency.
- 2026-08-21 - v0.1.0 - Recorded first Organizational Memory continuity
  evidence, retention boundaries, selector gap, prior-art hypothesis, and next
  retrieval Mission.
- 2026-08-21 - v0.1.0 - Recorded bounded Memory retrieval evidence,
  applicability limits, structured-lineage gaps, GraphRAG deferral, and the
  retention-governance dependency.
