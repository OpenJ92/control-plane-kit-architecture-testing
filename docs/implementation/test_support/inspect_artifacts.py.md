Source: [test_support/inspect_artifacts.py](../../../test_support/inspect_artifacts.py).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This executable build helper reads the supplied dist directory and requires exactly one wheel and one source archive with the expected identities. It checks selected package-root, typing-marker and test members. It reads archive metadata without extracting it. Those membership checks are not exhaustive source parity, signature verification, dependency safety or proof that the package executes correctly. test.sh owns when this helper runs; keep version/name expectations coordinated with pyproject.toml and the separate installed-package helper. Failures stop the owning gate; no arbitrary artifacts should be treated as trusted merely because these selected paths exist.
