# External Adoption Profile Runtime

`contextos.adoption.profile/1` maps universal Context OS capabilities to an external organization's existing governed canon. It is a mapping and applicability artifact, not a copied SSOT and not authority over the target.

The profile preserves deterministic identity, target scope, mapping provenance, source authority/currentness, Validator applicability, selection semantics, evidence isolation, and invalidation rules. Suggested or unknown mappings never become canonical merely because they appear in a profile.

An optional `work_ownership` section maps target-native current-work source
concepts and lifecycle terms for derived Work Ownership Resolution. The Runtime
accepts only exact profile-mapped concept/locator pairs; absent mappings remain
unknown and never mean that work is unowned.

```python
from adoption_engine import AdoptionProfile

profile = AdoptionProfile("examples/adoption_profiles/lukspeed.json")
state = profile.state("/path/to/target")
```

Universal runtime logic lives under `tools/adoption/adoption_engine/`. Target-specific filenames and equivalence decisions live only in profile data.
