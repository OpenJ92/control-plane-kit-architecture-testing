Source: [tests/test_architecture_policy_evaluation.py](../../../tests/test_architecture_policy_evaluation.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

These tests own interpretation laws for exact import/call surfaces: multiplicity
matters, single-target mismatch rejects, a missing batch target yields a finding,
and duplicate target coordinates or policy IDs reject before interpretation.
Findings have deterministic ordering and retain policy-owned messages.

Selected mock witnesses check admission order, once-per-value deep validation,
and the aggregate occurrence-work ceiling before expensive dispatch or partial
findings. They are local algorithm/evidence checks, not performance measurements
or a blanket complexity guarantee. Actual surfaces may exceed the policy-entry
cap while remaining inside the aggregate work bound.

Read [policy_fixture.py](policy_fixture.py.md) for synthesized facts/expectations
and the [policy owner](../src/control_plane_kit_architecture_testing/architecture_policy.py.md)
before changing these laws. Categorical errors are tested separately from
unexpected internal failures, which must propagate. No consumer's architecture
policy or deployed application's correctness is established here.
