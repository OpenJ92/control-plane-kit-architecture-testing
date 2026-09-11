Source: [tests/test_python_source_boundaries.py](../../../tests/test_python_source_boundaries.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

Owns [source analysis](../src/control_plane_kit_architecture_testing/python_source.py.md)
request/UTF-8-size/derived-name boundaries, categorical syntax errors, parser
exception identity and the distinction between syntax offsets and AST locations.
Hostile-string and captured-error helpers come from
[source_fact_fixture.py](../../../tests/source_fact_fixture.py); mocked parser
failures check propagation rather than running malicious source.

The test-side AST scan and prohibited-export checks describe this selected
module's dependency/effect boundary. They are static evidence, not an exhaustive
proof against dynamic execution in arbitrary future code. Use the owning gate;
this note records no fresh test result.
