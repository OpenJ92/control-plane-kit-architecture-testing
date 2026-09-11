Source: [tests/test_python_source_analysis.py](../../../tests/test_python_source_analysis.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

This file checks source-to-fact extraction for ordinary, dotted, aliased,
relative and wildcard imports and the closed resolved/unresolved call sum.
Repeated imports/calls remain repeated; AST source order and UTF-8 byte columns
remain visible. Explicit same-root aliases differ from implicit dotted-import
binding.

Comments and string literals produce no import/call facts. Wildcards and
conflicting aliases conservatively leave certain calls unresolved. These are
lexical facts under the executing Python AST grammar, not proof of which
callable will execute after scope, assignment or control flow is considered.
Read the [source owner](../src/control_plane_kit_architecture_testing/python_source.py.md)
before interpreting a resolved target as anything stronger. Provider operations
are not exercised by these examples.
