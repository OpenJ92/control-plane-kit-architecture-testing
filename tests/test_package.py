from __future__ import annotations

import importlib
from pathlib import Path
import stat
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "control_plane_kit_architecture_testing"


def _package_module():
    try:
        return importlib.import_module(PACKAGE_NAME)
    except ModuleNotFoundError as error:
        if error.name != PACKAGE_NAME:
            raise
        return None


PACKAGE = _package_module()


class GenesisPackageTests(unittest.TestCase):
    def require_file(self, relative: str) -> Path:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"genesis scaffold is missing {relative}")
        return path

    def test_fixture_root_is_the_mounted_checkout(self) -> None:
        self.assertEqual(ROOT.name, "source")
        self.assertTrue((ROOT / "tests" / "test_package.py").is_file())

    def test_root_package_exports_exact_accepted_surface(self) -> None:
        self.assertIsNotNone(PACKAGE, "genesis package namespace is not implemented")
        self.assertEqual(type(PACKAGE.__all__), tuple)
        self.assertEqual(
            PACKAGE.__all__,
            (
                "__version__",
                "AliasBinding",
                "ArchitecturePolicy",
                "CallFact",
                "CallTarget",
                "ExactCallSurfacePolicy",
                "ExactImportSurfacePolicy",
                "ImportFact",
                "ImportSurfaceEntry",
                "PolicyEvaluationError",
                "PolicyFinding",
                "PolicyId",
                "PythonSourceFacts",
                "ResolvedCallTarget",
                "RuleId",
                "SourceAnalysisError",
                "SourceLocation",
                "UnresolvedCallTarget",
                "analyze_source",
                "evaluate_policies",
                "evaluate_policy",
            ),
        )
        self.assertEqual(PACKAGE.__version__, "0.1.0")
        self.assertEqual(
            {name for name in PACKAGE.__dict__ if not name.startswith("__")},
            (set(PACKAGE.__all__) - {"__version__"}) | {"architecture_policy", "python_source"},
        )

    def test_project_metadata_is_exact_and_runtime_dependency_free(self) -> None:
        document = tomllib.loads(
            self.require_file("pyproject.toml").read_text(encoding="utf-8")
        )

        self.assertEqual(
            document["build-system"],
            {
                "requires": ["setuptools==83.0.0"],
                "build-backend": "setuptools.build_meta",
            },
        )
        self.assertEqual(document["project"]["name"], "control-plane-kit-architecture-testing")
        self.assertEqual(document["project"]["version"], "0.1.0")
        self.assertEqual(document["project"]["requires-python"], ">=3.11")
        self.assertEqual(document["project"]["dependencies"], [])
        self.assertNotIn("optional-dependencies", document["project"])
        self.assertEqual(
            document["project"]["urls"],
            {
                "Repository": (
                    "https://github.com/OpenJ92/"
                    "control-plane-kit-architecture-testing"
                )
            },
        )
        self.assertEqual(
            document["tool"]["setuptools"]["packages"]["find"],
            {
                "where": ["src"],
                "include": ["control_plane_kit_architecture_testing*"],
            },
        )
        self.assertEqual(
            document["tool"]["setuptools"]["package-data"],
            {"control_plane_kit_architecture_testing": ["py.typed"]},
        )

    def test_repository_contract_documents_are_present(self) -> None:
        for relative in (
            "AGENTS.md",
            "GIT-FLOW.md",
            "README.md",
            "LICENSE",
            ".gitignore",
            ".dockerignore",
        ):
            with self.subTest(relative=relative):
                self.require_file(relative)

    def test_docker_gate_is_executable_and_complete(self) -> None:
        gate = self.require_file("test.sh")
        document = gate.read_text(encoding="utf-8")

        self.assertTrue(gate.stat().st_mode & stat.S_IXUSR)
        for marker in (
            "phase=source-tests",
            "phase=compile",
            "phase=build",
            "phase=artifact-inspection",
            "phase=installed-package",
            "python:3.11",
            "python:3.12",
            "python:3.13",
            "python:3.14",
            "python -m unittest discover -s tests -v",
            "python -m compileall src tests",
            "python -m pip install --no-build-isolation --no-deps /tmp/install-source",
            "python -m build --sdist --wheel",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, document)

    def test_actions_gate_is_read_only_pinned_and_runs_package_gate(self) -> None:
        workflow = self.require_file(".github/workflows/tests.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("contents: read", workflow)
        self.assertIn("timeout-minutes:", workflow)
        self.assertIn("cancel-in-progress: true", workflow)
        self.assertIn("actions/checkout@", workflow)
        self.assertNotIn("actions/checkout@v", workflow)
        self.assertIn("run: ./test.sh", workflow)

    def test_outside_source_package_smoke_is_present(self) -> None:
        smoke = self.require_file("test_support/installed_package.py")
        document = smoke.read_text(encoding="utf-8")

        self.assertIn("control_plane_kit_architecture_testing", document)
        self.assertIn("importlib.metadata", document)
        self.assertNotIn("sys.path", document)


if __name__ == "__main__":
    unittest.main()
