from __future__ import annotations

import ast
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "test_support" / "canonical_archives.py"
ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "base64",
    "configparser",
    "csv",
    "datetime",
    "hashlib",
    "io",
    "stat",
    "struct",
    "tarfile",
    "zipfile",
    "zlib",
}
FORBIDDEN_CALL_NAMES = {
    "breakpoint",
    "compile",
    "eval",
    "exec",
    "exit",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "print",
    "quit",
    "setattr",
    "vars",
}
FORBIDDEN_TOKENS = (
    "callback",
    "credential",
    "docker",
    "environment",
    "filesystem",
    "git ",
    "logging",
    "network",
    "pathlib",
    "plugin",
    "random",
    "requests",
    "secret",
    "socket",
    "subprocess",
    "tempfile",
    "uuid",
)


def _root_name(node: ast.expr) -> str | None:
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


class CanonicalArchiveOwnershipTests(unittest.TestCase):
    def test_source_has_closed_stdlib_import_and_lexical_call_capability(self) -> None:
        self.assertTrue(SOURCE.is_file(), "canonical archive language is not implemented")
        document = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(document, filename=SOURCE.as_posix())
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                self.assertEqual(node.level, 0)
                self.assertIsNotNone(node.module)
                imported_roots.add(node.module.split(".", 1)[0])
                self.assertNotIn("*", tuple(alias.name for alias in node.names))

        self.assertEqual(imported_roots, ALLOWED_IMPORT_ROOTS)
        self.assertLessEqual(imported_roots, set(sys.stdlib_module_names) | {"__future__"})
        self.assertNotIn("control_plane_kit_architecture_testing", imported_roots)
        self.assertNotIn("test_support", imported_roots)

        bound_names = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
        }
        bound_names.update(node.arg for node in ast.walk(tree) if isinstance(node, ast.arg))
        bound_names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        )
        bound_names.update(
            alias.asname or alias.name.split(".", 1)[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        bound_names.update(
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        )
        safe_builtins = {
            "all",
            "any",
            "bool",
            "bytes",
            "dict",
            "enumerate",
            "int",
            "isinstance",
            "len",
            "list",
            "range",
            "set",
            "sorted",
            "str",
            "sum",
            "tuple",
            "type",
            "zip",
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            self.assertIsInstance(node.func, (ast.Name, ast.Attribute))
            root = _root_name(node.func)
            self.assertIsNotNone(root)
            if isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, FORBIDDEN_CALL_NAMES)
                self.assertIn(node.func.id, bound_names | safe_builtins)
            else:
                self.assertNotIn(node.func.attr, FORBIDDEN_CALL_NAMES)
            self.assertNotEqual(root, "__builtins__")

        lowered = document.lower()
        for token in FORBIDDEN_TOKENS:
            with self.subTest(token=token):
                self.assertNotIn(token, lowered)

        public_functions = tuple(
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not node.name.startswith("_")
        )
        self.assertEqual(public_functions, ("canonicalize_sdist", "canonicalize_wheel"))


if __name__ == "__main__":
    unittest.main()
