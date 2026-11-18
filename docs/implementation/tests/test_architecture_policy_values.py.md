Source: [tests/test_architecture_policy_values.py](../../../tests/test_architecture_policy_values.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

These tests protect the exact frozen/slotted public policy values, canonical
duplicate-preserving surfaces, tagged call targets and bounded machine
identifiers. They check nested forged values and hostile subclasses as well as
ordinary constructor inputs. Root exports must refer to the same owner types.

The fixtures deliberately exercise invalid construction; their bypass helpers
are not public construction guidance. Finding text is bounded policy-authored
material. Candidate-free rejection messages and absent source fields do not
turn arbitrary accepted policy text into a secret sanitizer.
[architecture_policy.py](../src/control_plane_kit_architecture_testing/architecture_policy.py.md)
owns this value contract; evaluation and consumer policy choice are separate.
