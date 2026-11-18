Source: [src/control_plane_kit_architecture_testing/__init__.py](../../../../src/control_plane_kit_architecture_testing/__init__.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This public facade exports the version plus explicit source-fact and policy
types/functions from [python_source.py](python_source.py.md) and
[architecture_policy.py](architecture_policy.py.md). Importing it loads those
pure modules; it does not analyze source or apply a consumer policy.

The root README's version-only genesis description is historical. The actual
`__all__` and [installed-package check](../../../../test_support/installed_package.py)
define the current export expectation. Review both owners and installation
checks before changing the facade; keep this tooling out of production package
dependencies as required by AGENTS.md.
