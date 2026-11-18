Source: [tests/test_python_source_values.py](../../../tests/test_python_source_values.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

This file checks exact nominal, frozen/slotted source-fact values and root
export identity. Source coordinates and names are bounded; aggregate facts
require exact tuples, matching paths and aliases derived from the import facts.
Nested constructor bypasses and hostile subclasses must be revalidated.

[Source fixture helpers](source_fact_fixture.py.md) construct hostile inputs
only for negative tests. Candidate-free exception checks and an example
excluding source literals from repr establish selected retention laws; accepted
caller-supplied path/name text is still retained and is not universally redacted.
Extraction semantics belong to the adjacent analysis tests and the
[source owner](../src/control_plane_kit_architecture_testing/python_source.py.md).
