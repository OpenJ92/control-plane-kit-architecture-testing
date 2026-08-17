from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest

from release_build_fixture import BUILD_INPUT_ROWS, lock_document


ROOT = Path(__file__).resolve().parents[1]


class ReleaseBuildRepositoryContractTests(unittest.TestCase):
    def test_build_input_fixture_is_exact_canonical_and_complete(self) -> None:
        encoded = lock_document()
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertFalse(encoded.endswith(b"\n\n"))
        document = json.loads(encoded)
        self.assertEqual(
            tuple(row["name"] for row in document["artifacts"]),
            ("build", "packaging", "pyproject-hooks", "setuptools"),
        )
        self.assertEqual(
            tuple(row["version"] for row in document["artifacts"]),
            ("1.3.0", "25.0", "1.2.0", "83.0.0"),
        )
        for row in document["artifacts"]:
            with self.subTest(name=row["name"]):
                self.assertRegex(row["sha256"], r"\A[0-9a-f]{64}\Z")
                self.assertGreater(row["size"], 0)
                self.assertTrue(row["url"].startswith("https://files.pythonhosted.org/"))
                self.assertTrue(row["url"].endswith(row["filename"]))

    def test_exact_hash_locked_build_input_document_is_present(self) -> None:
        path = ROOT / "test_support" / "build-inputs.json"
        self.assertTrue(path.is_file(), "release build input lock is not implemented")
        encoded = path.read_bytes()
        self.assertEqual(encoded, lock_document())
        document = json.loads(encoded)
        self.assertEqual(len(document["artifacts"]), 4)
        self.assertEqual(
            tuple(
                (
                    row["name"],
                    row["version"],
                    row["filename"],
                    row["url"],
                    row["size"],
                    row["sha256"],
                )
                for row in document["artifacts"]
            ),
            BUILD_INPUT_ROWS,
        )

    def test_package_requires_the_fixed_build_backend(self) -> None:
        metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["build-system"]["requires"], ["setuptools==83.0.0"])

    def test_gate_requires_the_lock_and_offline_hash_enforcement(self) -> None:
        gate = (ROOT / "test.sh").read_text(encoding="utf-8")
        for marker in (
            'BUILD_BACKEND="setuptools==83.0.0"',
            "test_support/build-inputs.json",
            "--no-index",
            "--find-links",
            "--require-hashes",
            "--only-binary=:all:",
            "--no-deps",
            "phase=reproducible-build",
            "release_report.py",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, gate)

    def test_readme_describes_current_language_and_release_candidate_boundary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for marker in (
            "Python source facts",
            "Architecture policies",
            "Reproducible release candidates",
            "not published",
            "no runtime dependencies",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, readme)
        self.assertIsNotNone(re.search(r"Python 3\.11 through\s+Python 3\.14", readme))
        self.assertNotIn("Genesis Surface", readme)
        self.assertNotIn("only one importable package namespace", readme)

    def test_stage_one_support_is_stdlib_only_and_has_no_effect_capability(self) -> None:
        release_path = ROOT / "test_support" / "release_report.py"
        self.assertTrue(release_path.is_file(), "release report language is not implemented")
        tree = ast.parse(release_path.read_text(encoding="utf-8"), filename=release_path.as_posix())
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_roots.add(node.module.split(".", 1)[0])
        self.assertLessEqual(imported_roots, set(sys.stdlib_module_names) | {"__future__"})
        self.assertTrue(imported_roots.isdisjoint({"http", "requests", "socket", "subprocess", "urllib"}))
        source = release_path.read_text(encoding="utf-8")
        for forbidden in (
            "requests",
            "urllib",
            "socket",
            "subprocess",
            "docker",
            "boto",
            "credential",
            "upload",
            "git tag",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
