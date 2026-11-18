Source: [src/control_plane_kit_architecture_testing/py.typed](../../../../src/control_plane_kit_architecture_testing/py.typed).
Maintain this document alongside its source file. When the source or relevant
imported contracts change, verify and update this companion in the same change.

This empty marker advertises inline typing in the installed package. Its existence and package-data inclusion matter even though it contains no executable contract. pyproject.toml owns inclusion; test_support/inspect_artifacts.py checks its wheel presence. Preserve it through packaging changes; do not infer runtime type enforcement from a typing marker.
