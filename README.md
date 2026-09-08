# Context OS

**An Organizational Context Runtime for human-agent work.**

Teams and AI agents need current context, governing sources and clear action
authority. Context OS makes those boundaries inspectable before work begins.

**Design-partner alpha:** a local Python CLI and engine APIs for technical
maintainers, founders and small software teams. v1.0 is released; self-service
adoption and measurable business value remain unproven.

## What it does

- Checks context integrity and readiness, with evidence and explicit gaps.
- Selects bounded governing context for a Mission and produces a working brief.
- Checks saved context for source changes and preserves provenance.
- Reports context health, policy-aware prior art and advisory reasoning.
- Supports approved, create-only native bootstrap and construction.

Humans own intent, authority, approval and outcomes. Context OS does not
launch agents or execute the Mission.

## How to try it

Requires Git and Python 3.9+; no third-party Python packages. Checked on macOS
with Python 3.9.6; broader platform support is unproven.

```bash
git clone https://github.com/Buggeek/ContextOS.git
cd ContextOS
./contextos --version
./contextos assess --root .
./contextos activate --root . --goal "Orient one bounded Mission" --handoff
./contextos health --root .
```

This read-only demo assesses this repository. Inspect the brief's sources,
bounds and gaps: exit 0 can coexist with warnings or unknowns. See
[installation](docs/4.x_adoption/4.5_COS_Runtime_Installation.md) for target use,
report checks and advanced APIs.

To resume one bounded front across processes, see the assisted
[local work continuity route](docs/4.x_adoption/4.7_COS_Local_Work_Continuity.md).
It prepares a sourced brief and rechecks saved context; technical setup and
human interpretation remain explicit, and the user trial is pending.

## Adoption journey

Map one work need and its sources → assess gaps → prepare a checked brief →
perform authorized work → record outcomes and recheck context before reuse.

**Native bootstrap:** init plans setup with optional templates; writes need
approval and a fresh preflight. **External Adoption:** a governed profile maps
existing sources and controls without migration or a new SSOT directory.
Mapping and policy preparation currently need technical help.
See the [Adoption Playbook](docs/4.x_adoption/4.0_COS_Adoption_Playbook.md).

## Evidence and limits

[Released integration and self-hosting](SSOT/E.4_Mission_V10-ORGANIZATIONAL-CONTEXT-RUNTIME-RELEASE-VERIFY-001_Release_Verification.md)
prove a bounded, human-operated Runtime loop.
[External Adoption evidence](SSOT/E.4_Mission_POST-V1-EXTERNAL-ADOPTION-PROFILE-001_External_Adoption_Portability.md)
covers one software organization's distributed canon; later
[Mission evidence](SSOT/E.4_Mission_POST-V1-EXTERNAL-MISSION-RUNTIME-HARDENING-001_External_Mission_Runtime_Hardening.md)
records a bounded external documentation Mission.

Discovery, Builder, Context Versions and Work Ownership require Python APIs.
Memory needs an applicable policy; reasoning is advisory. Connectors, hosting,
orchestration and automatic canonical mutation are absent. Enterprise and
cross-domain outcomes remain unproven.

Next: [current product and value gates](docs/5.x_strategy/5.6_COS_Current_Product_Definition.md),
[post-v1 Productization Roadmap](SSOT/P.2_Product_Roadmap.md#post-v1-productization-roadmap),
[architecture](docs/1.x_architecture/1.0_COS_Architecture.md).

Long-term outcome: **Context OS enables AI-native organizations to govern
their own evolution.** The [Theory](docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md)
distinguishes ambition from current evidence.
