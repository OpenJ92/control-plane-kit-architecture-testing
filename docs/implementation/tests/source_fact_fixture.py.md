Source: [tests/source_fact_fixture.py](../../../tests/source_fact_fixture.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

This is test-only support for the source-fact language. Import discovery catches
only ModuleNotFoundError naming the requested language module; require_language
then asserts implementation presence. It does not skip missing behavior or hide
a missing transitive dependency.

forge deliberately bypasses constructors to test that nested values are
revalidated. Hostile scalar and tuple subclasses expose accidental dispatch
before exact-type admission. captured_error additionally requires no cause or
context on the captured exception. This selected assertion does not establish
that every unexpected internal failure is sanitized; the boundary tests
deliberately preserve some unexpected exceptions.
