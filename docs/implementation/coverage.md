# Initial architecture-testing companion coverage

Source scope: develop `d31dbf5c6e6127e5be10253e81e2fbf1e84cc0ed`; [issue #15](https://github.com/OpenJ92/control-plane-kit-architecture-testing/issues/15). This initial tracked-file inventory does not include the new documentation itself. It records rollout coverage, not permanent freshness or a behavior audit. Review depth and source coordinates belong in the PR. Unknown semantics/discrepancies remain independent from coverage.

24 tracked files: 20 reviewed, 0 pending, 4 excluded. Vale independently reviewed all companions: source owners and consequential harness claims directly, with selected assertion review for routine test navigation. This is not a full large-test audit. No executable validation claimed.

| Source | Status | Disposition |
| --- | --- | --- |
| `.dockerignore` | reviewed | [Companion](.dockerignore.md) |
| `.github/workflows/tests.yml` | reviewed | [Companion](.github/workflows/tests.yml.md) |
| `.gitignore` | reviewed | [Companion](.gitignore.md) |
| `AGENTS.md` | excluded | Governing instructions updated directly; no recursive documentation mirror. |
| `GIT-FLOW.md` | excluded | Existing governance maintained directly. |
| `LICENSE` | excluded | Legal text remains its own authoritative artifact. |
| `README.md` | excluded | Existing prose; genesis/current API discrepancy tracked in issue #15 and guide. |
| `pyproject.toml` | reviewed | [Companion](pyproject.toml.md) |
| `src/control_plane_kit_architecture_testing/__init__.py` | reviewed | [Companion](src/control_plane_kit_architecture_testing/__init__.py.md) |
| `src/control_plane_kit_architecture_testing/architecture_policy.py` | reviewed | [Companion](src/control_plane_kit_architecture_testing/architecture_policy.py.md) |
| `src/control_plane_kit_architecture_testing/py.typed` | reviewed | [Companion](src/control_plane_kit_architecture_testing/py.typed.md) |
| `src/control_plane_kit_architecture_testing/python_source.py` | reviewed | [Companion](src/control_plane_kit_architecture_testing/python_source.py.md) |
| `test.sh` | reviewed | [Companion](test.sh.md) |
| `test_support/inspect_artifacts.py` | reviewed | [Companion](test_support/inspect_artifacts.py.md) |
| `test_support/installed_package.py` | reviewed | [Companion](test_support/installed_package.py.md) |
| `tests/policy_fixture.py` | reviewed | [Companion](tests/policy_fixture.py.md) |
| `tests/source_fact_fixture.py` | reviewed | [Companion](tests/source_fact_fixture.py.md) |
| `tests/test_architecture_policy_boundaries.py` | reviewed | [Companion](tests/test_architecture_policy_boundaries.py.md) |
| `tests/test_architecture_policy_evaluation.py` | reviewed | [Companion](tests/test_architecture_policy_evaluation.py.md) |
| `tests/test_architecture_policy_values.py` | reviewed | [Companion](tests/test_architecture_policy_values.py.md) |
| `tests/test_package.py` | reviewed | [Companion](tests/test_package.py.md) |
| `tests/test_python_source_analysis.py` | reviewed | [Companion](tests/test_python_source_analysis.py.md) |
| `tests/test_python_source_boundaries.py` | reviewed | [Companion](tests/test_python_source_boundaries.py.md) |
| `tests/test_python_source_values.py` | reviewed | [Companion](tests/test_python_source_values.py.md) |
