Source: [tests/test_architecture_policy_boundaries.py](../../../tests/test_architecture_policy_boundaries.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

Checks the [policy module](../src/control_plane_kit_architecture_testing/architecture_policy.py.md)
against its selected stdlib/fact-language import surface, prohibited effect names,
absent discovery/rewrite extensions and absence of CPK/provider-specific names.
The test reads and parses source; the installed policy interpreter does not.

These exact checks belong to this package's deliberate generic/pure boundary.
Do not copy them into consumers as a mandate to police unrelated helper layout
or encode application state machines. A passing lexical scan is limited static
evidence; policy evaluation/value semantics live in their separate test files.
