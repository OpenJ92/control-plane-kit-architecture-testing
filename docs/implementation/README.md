# Agent implementation companions

Follow the agreed [CPK convention and maintenance decision](https://github.com/OpenJ92/control-plane-kit/issues/1799).
This repository's work is [#15](https://github.com/OpenJ92/control-plane-kit-architecture-testing/issues/15).

Map each covered repository-relative source path to the same path below this
directory, with `.md` appended. Each companion begins with its source link and
maintenance reminder. Read the owner and selected imported contracts; notes are
navigation aids, not a replacement implementation or permission to run effects.
Update companions alongside source, including moves/removals. Record review or
no semantic change in the existing PR, using its actual diff. No hash ledger or
new CI framework is required. Initial coverage is tracked in [coverage.md](coverage.md).

## Reading order and known limits

[Python source facts](src/control_plane_kit_architecture_testing/python_source.py.md)
describe lexical occurrences. [Policy interpretation](src/control_plane_kit_architecture_testing/architecture_policy.py.md)
compares those facts with consumer-selected expected surfaces. The consumer owns
which policies should apply; a matching lexical surface does not establish
runtime safety or semantic correctness. The installed package does not read
repositories or execute the analyzed text. Test/gate machinery has separate
filesystem, installation and Docker effects.

The root README's "Genesis Surface" describes historical version-only exports.
Current source and installation checks also expose source facts and policies.
Do not use that paragraph as the current export contract. This discrepancy is
recorded under #15; these companions do not silently change package behavior.
