Source: [src/control_plane_kit_architecture_testing/python_source.py](../../../../src/control_plane_kit_architecture_testing/python_source.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

## Owned transformation

`analyze_source` turns supplied Python text and caller-supplied path/module
coordinates into immutable lexical import, alias and call facts. It uses the
executing Python's `ast` grammar; it does not open the named path, resolve installed
modules, import analyzed code or execute it. The facts omit the AST, source text
and argument literals. The downstream [policy owner](architecture_policy.py.md)
decides which occurrence surfaces are acceptable.

## Constraints an editor must preserve

Fact values require exact nominal types, bounded text and valid coordinates.
`PythonSourceFacts` requires its alias tuple to equal the bindings derived from
its import tuple, and each fact's path to match the enclosing source path.
Do not supply arbitrary aliases as a shortcut to favorable policy results.

Import and call occurrences retain source order and multiplicity. Import
locations use AST alias locations; call locations use AST call locations.
`SourceLocation` uses AST line/column semantics; syntax-error offsets are copied
from `SyntaxError` and are not normalized to that same coordinate convention.

Call resolution is lexical, not scope/dataflow analysis: aliases are collected
across the module; conflicting aliases produce unresolved targets. Star imports
make otherwise unbound roots unresolved. Attribute chains rooted in a simple
name can be qualified; more complex expressions cannot. Assignment, control-flow
and local shadowing are not modeled. `ResolvedCallTarget` therefore names syntax,
not proof of the object eventually called at runtime.

## Limits and evidence

Input text is capped by UTF-8 byte size before parsing. Invalid request types
and shapes produce categorical errors; ordinary syntax failures become bounded
analysis errors without retaining the parser exception/source context. Unexpected
parser exceptions propagate. This is not a universal sanitizer: caller-supplied
path/module/name text still appears in admitted facts and must be suitable for
its intended use.

[Analysis tests](../../../../tests/test_python_source_analysis.py) cover lexical
interpretation, [value tests](../../../../tests/test_python_source_values.py)
cover nominal immutability/admission, and
[boundary tests](../../../../tests/test_python_source_boundaries.py) cover limits,
error disclosure and the selected static dependency/effect surface. They do not
prove runtime call targets or sandbox arbitrary Python. The source's explicit
lexical model is the rationale recorded here; no inferred author intention is
needed to explain a more powerful analyzer that does not exist.
