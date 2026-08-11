# Context OS Bootstrap Tools

This folder contains read-only bootstrap planning components for Release v0.4
Guided Bootstrap.

Slice 1 implements **Bootstrap Planning** only:

- no CLI integration
- no apply mode
- no manifest creation
- no SSOT, governance, or scaffold writes

Slice 2 exposes that plan through the Runtime CLI:

```bash
./contextos init --root .
./contextos init --root . --format json
./contextos init --root . --json-out /tmp/contextos-bootstrap-plan.json
./contextos init --root . --proposal
./contextos init --root . --proposal --format json
./contextos init --root . --proposal --json-out /tmp/contextos-bootstrap-proposal.json
./contextos init --root . --approval-record /tmp/contextos-bootstrap-proposal.json
./contextos init --root . --approval-record /tmp/contextos-bootstrap-proposal.json --format json
./contextos init --root . --accept-approval /tmp/contextos-bootstrap-approval.json --accepted-by "Human Name" --accepted-role "Mission Owner"
./contextos init --root . --accept-approval /tmp/contextos-bootstrap-approval.json --accepted-by "Human Name" --accepted-role "Mission Owner" --format json
```

`contextos init` is still a read-only planning command. It does not create
manifests, directories, templates, or Context OS artifacts.

Public API:

```python
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine
from bootstrap_engine.acceptance_engine import BootstrapApprovalAcceptanceEngine
from bootstrap_engine.report_builder import render_human

plan = BootstrapPlanEngine(".").run()
proposal = BootstrapProposalEngine(".").run(plan)
human = render_human(plan)
```

Machine report schema:

```text
contextos.bootstrap.plan/1
contextos.bootstrap.proposal/1
contextos.bootstrap.approval_record/1
contextos.bootstrap.accepted_decision/1
```

The plan explains required, skipped, blocked, and manual future bootstrap
actions. The proposal freezes one exact future apply candidate, including the
plan hash, repository fingerprint, authority requirements, action
classifications, rollback metadata, and drift invalidation conditions. Proposal
generation is read-only and does not imply approval. The CLI proposal surface
exists for review and preservation only; it does not apply changes.

The approval record draft binds a preserved proposal to required authority,
drift checks, blockers, and a Decision Record draft. It is still read-only and
does not approve or authorize apply.

The accepted decision binds a valid approval record draft to an explicit human
identity and authority role. It embeds a `contextos.decision/1` Decision Record
and approves the preserved proposal as future apply intent, but it still does
not authorize or perform apply. It is designed to be consumed by later v0.4
apply/CLI slices.
