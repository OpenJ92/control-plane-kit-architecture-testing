Source: [pyproject.toml](../../pyproject.toml).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This authored metadata declares a standard-library-only distribution, a pinned build backend, the supported minimum Python version, and the src-package/typing-marker inclusion rules. A build dependency is distinct from an installed runtime dependency; keep the latter empty as required by AGENTS.md. Package version and artifact names are also asserted by test_support/inspect_artifacts.py and installed_package.py, so a version change must coordinate those owners. This file does not itself install or publish anything.
