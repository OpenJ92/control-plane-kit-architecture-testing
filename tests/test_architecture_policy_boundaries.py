from __future__ import annotations

import ast
from pathlib import Path
import unittest

from policy_fixture import require_policy_language


ROOT = Path(__file__).resolve().parents[1]


class ArchitecturePolicyBoundaryTests(unittest.TestCase):
    def test_policy_module_has_the_exact_stdlib_and_fact_language_dependency_surface(self) -> None:
        require_policy_language(self)
        implementation = (
            ROOT
            / "src/control_plane_kit_architecture_testing/architecture_policy.py"
        )
        document = implementation.read_text(encoding="utf-8")
        tree = ast.parse(document, filename=implementation.as_posix())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend((value.name, None, value.asname) for value in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.extend(
                    (node.module or "", value.name, value.asname) for value in node.names
                )
        self.assertEqual(
            tuple(imports),
            (
                ("__future__", "annotations", None),
                ("dataclasses", "dataclass", None),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "CallTarget",
                    None,
                ),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "ImportFact",
                    None,
                ),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "PythonSourceFacts",
                    None,
                ),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "ResolvedCallTarget",
                    None,
                ),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "SourceLocation",
                    None,
                ),
                (
                    "control_plane_kit_architecture_testing.python_source",
                    "UnresolvedCallTarget",
                    None,
                ),
            ),
        )

    def test_policy_module_has_no_effect_successor_or_consumer_capability(self) -> None:
        policy = require_policy_language(self)
        implementation = (
            ROOT
            / "src/control_plane_kit_architecture_testing/architecture_policy.py"
        )
        document = implementation.read_text(encoding="utf-8")
        tree = ast.parse(document, filename=implementation.as_posix())
        forbidden_names = {
            "open",
            "exec",
            "eval",
            "compile",
            "input",
            "print",
            "breakpoint",
            "__import__",
        }
        forbidden_roots = {
            "asyncio",
            "datetime",
            "importlib",
            "io",
            "logging",
            "os",
            "pathlib",
            "random",
            "secrets",
            "shutil",
            "socket",
            "subprocess",
            "tempfile",
            "time",
            "uuid",
        }
        self.assertFalse(
            {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name) and node.id in forbidden_names
            }
        )
        self.assertFalse(
            {
                node.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Name) and node.id in forbidden_roots
            }
        )
        for prohibited in (
            "ArchitecturePolicyProtocol",
            "PolicyRegistry",
            "discover_policies",
            "evaluate_file",
            "rewrite_source",
            "autofix",
        ):
            self.assertFalse(hasattr(policy, prohibited))
        for candidate in (
            "control_plane_kit_core",
            "control_plane_kit_operations",
            "docker",
            "cloudflare",
            "provider",
            "postgres",
        ):
            self.assertNotIn(candidate, document)


if __name__ == "__main__":
    unittest.main()
