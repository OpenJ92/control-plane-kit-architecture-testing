Source: [tests/policy_fixture.py](../../../tests/policy_fixture.py).
Maintain this document alongside its source file. When the source or relevant imported contracts change, verify and update this companion in the same change.

This fixture composes synthetic source facts and exact import/call policies for
the policy tests. Expected surfaces are canonically sorted while retaining
duplicates. Small examples isolate the policy language; they are not a reusable
registry of consumer architecture rules.

The module loader tolerates only absence of the requested policy module, then
require_policy_language turns that absence into a test failure. Missing
transitive dependencies propagate. Shared forge/captured_error helpers come
from [source_fact_fixture.py](source_fact_fixture.py.md); hostile scalar/tuple
subclasses make accidental method dispatch visible. Do not use these constructor
bypasses in production or infer runtime imports from synthetic lexical facts.
