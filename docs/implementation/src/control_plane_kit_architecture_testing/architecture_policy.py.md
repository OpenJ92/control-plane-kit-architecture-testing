Source: [src/control_plane_kit_architecture_testing/architecture_policy.py](../../../../src/control_plane_kit_architecture_testing/architecture_policy.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

## Owned contract

This pure interpreter compares exact import or lexical-call occurrence surfaces
with explicit policies. Consumers own which expectations are appropriate; this
module does not discover policies, read repositories, rewrite code or define CPK
application semantics. Its dependency is the
[PythonSourceFacts language](python_source.py.md), whose lexical limitations
remain true after evaluation.

Expected surfaces are canonical sorted tuples with multiplicity preserved.
Imports project to module/imported-name/alias without source location; calls
project to resolved/unresolved target values. Duplicate occurrences matter:
set comparison would change the contract. Finding output contains policy-owned
message/identity and a module anchor, not raw mismatched source or arguments.
Messages remain caller-owned text; length validation does not make secrets safe
to place in a policy.

`evaluate_policy` rejects a target mismatch. `evaluate_policies` instead emits
one policy finding when the target facts are absent. It rejects duplicate fact
coordinates and duplicate policy IDs, validates bounded work before full
evaluation, and returns deterministic sorted findings. Multiple rules do not
permit reuse of a policy ID within that batch. Fact/path names are passed as
values; they do not prove that a corresponding source file exists.

## Validation and change guidance

The policy owner revalidates exact fact values through their constructor. Only
the expected categorical fact errors become invalid-request outcomes; unexpected
errors propagate. Keep that boundary when changing validation rather than
catching every exception as an ordinary policy mismatch.

[Evaluation tests](../../../../tests/test_architecture_policy_evaluation.py)
protect exact projections, missing-target/batch semantics and bounded ordering;
[value tests](../../../../tests/test_architecture_policy_values.py) own closed
policy values; [boundary tests](../../../../tests/test_architecture_policy_boundaries.py)
check the selected pure dependency/effect surface. These prove a generic tooling
contract, not that a consumer's chosen architecture policy is correct or that
matching lexical calls establish runtime safety. No new executable result is
claimed here.
