from __future__ import annotations

import ast
from pathlib import Path
from unittest import mock
import unittest

from source_fact_fixture import HostileStr, captured_error, require_language


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LIMIT = 1_048_576


class PythonSourceBoundaryTests(unittest.TestCase):
    def test_analysis_request_requires_exact_bounded_strings_before_parsing(self) -> None:
        language = require_language(self)
        invalid = (
            (HostileStr("run()"), "sample.py", "sample"),
            ("run()", HostileStr("sample.py"), "sample"),
            ("run()", "sample.py", HostileStr("sample")),
            ("run()", "", "sample"),
            ("run()", "p" * 513, "sample"),
            ("run()", "sample.py", "m" * 513),
            ("run()\x00", "sample.py", "sample"),
            ("run()\ud800", "sample.py", "sample"),
        )
        errors = []
        for source, path, module in invalid:
            with self.subTest(source=type(source), path=type(path), module=type(module)):
                errors.append(
                    captured_error(
                        self,
                        (TypeError, ValueError),
                        lambda source=source, path=path, module=module: language.analyze_source(
                            source, path=path, module=module
                        ),
                    )
                )
        for error in errors:
            for candidate in ("run", "sample", "513", "surrogate"):
                self.assertNotIn(candidate, str(error).lower())

    def test_source_size_is_exact_utf8_length_at_maximum_and_plus_one(self) -> None:
        language = require_language(self)
        maximum_ascii = "#" + ("x" * (SOURCE_LIMIT - 2)) + "\n"
        plus_one_ascii = maximum_ascii[:-1] + "x\n"
        maximum_multibyte = "#" + ("é" * 524_287) + "\n"
        plus_one_multibyte = "#x" + ("é" * 524_287) + "\n"
        self.assertEqual(len(maximum_ascii.encode("utf-8")), SOURCE_LIMIT)
        self.assertEqual(len(plus_one_ascii.encode("utf-8")), SOURCE_LIMIT + 1)
        self.assertEqual(len(maximum_multibyte), 524_289)
        self.assertEqual(len(maximum_multibyte.encode("utf-8")), SOURCE_LIMIT)
        self.assertEqual(len(plus_one_multibyte.encode("utf-8")), SOURCE_LIMIT + 1)
        self.assertEqual(
            language.analyze_source(maximum_ascii, path="max.py", module="max").calls,
            (),
        )
        self.assertEqual(
            language.analyze_source(
                maximum_multibyte,
                path="max_unicode.py",
                module="max_unicode",
            ).calls,
            (),
        )

        for source, path, module in (
            (plus_one_ascii, "plus.py", "plus"),
            (plus_one_multibyte, "plus_unicode.py", "plus_unicode"),
        ):
            with self.subTest(path=path):
                error = captured_error(
                    self,
                    language.SourceAnalysisError,
                    lambda source=source, path=path, module=module: language.analyze_source(
                        source, path=path, module=module
                    ),
                )
                self.assertNotIn("xxx", str(error))
                self.assertNotIn("ééé", str(error))
                self.assertLessEqual(len(str(error)), 600)

    def test_malformed_source_error_is_bounded_redacted_and_context_free(self) -> None:
        language = require_language(self)
        secret = "TOKEN = 'do-not-echo'\ndef broken(:\n"
        error = captured_error(
            self,
            language.SourceAnalysisError,
            lambda: language.analyze_source(secret, path="broken.py", module="broken"),
        )
        self.assertIs(type(error), language.SourceAnalysisError)
        self.assertEqual(error.path, "broken.py")
        self.assertEqual(error.line, 2)
        self.assertGreater(error.column, 0)
        self.assertNotIn("do-not-echo", str(error))
        self.assertNotIn("broken(:", str(error))
        self.assertLessEqual(len(str(error)), 600)

    def test_syntax_error_offset_is_not_normalized_to_source_location(self) -> None:
        language = require_language(self)
        source = "é = 1; broken(\n"
        try:
            ast.parse(source, filename="syntax.py")
        except SyntaxError as parser_error:
            expected_line = parser_error.lineno or 0
            expected_column = parser_error.offset or 0
        else:
            self.fail("syntax witness unexpectedly parsed")

        error = captured_error(
            self,
            language.SourceAnalysisError,
            lambda: language.analyze_source(source, path="syntax.py", module="syntax"),
        )
        self.assertEqual((error.line, error.column), (expected_line, expected_column))
        self.assertNotEqual(error.column, len(source.splitlines()[0].encode("utf-8")))

    def test_unexpected_parser_failures_escape_by_exact_identity(self) -> None:
        language = require_language(self)
        for canary in (TypeError("type-canary"), RuntimeError("runtime-canary")):
            with self.subTest(error=type(canary)):
                with mock.patch.object(language.ast, "parse", side_effect=canary):
                    with self.assertRaises(type(canary)) as raised:
                        language.analyze_source("run()\n", path="sample.py", module="sample")
                self.assertIs(raised.exception, canary)

    def test_derived_qualified_name_limit_is_categorical_and_nonleaking(self) -> None:
        language = require_language(self)
        maximum = "aa" + (".b" * 2047)
        plus_one = "aaa" + (".b" * 2047)
        self.assertEqual(len(maximum), 4096)
        self.assertEqual(len(plus_one), 4097)
        accepted = language.analyze_source(
            f"{maximum}()\n", path="max_name.py", module="max_name"
        )
        self.assertEqual(accepted.calls[0].target.qualified_name, maximum)
        error = captured_error(
            self,
            language.SourceAnalysisError,
            lambda: language.analyze_source(
                f"{plus_one}()\n", path="plus_name.py", module="plus_name"
            ),
        )
        self.assertNotIn(plus_one[:32], str(error))

    def test_no_effect_surface_is_proved_by_independent_test_side_ast(self) -> None:
        require_language(self)
        implementation = ROOT / "src/control_plane_kit_architecture_testing/python_source.py"
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
                ("ast", None, None),
                ("dataclasses", "dataclass", None),
            ),
        )

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

    def test_public_surface_contains_no_later_issue_or_filesystem_capability(self) -> None:
        language = require_language(self)
        prohibited = (
            "analyze_file",
            "evaluate_policy",
            "evaluate_policies",
            "ArchitecturePolicy",
            "PolicyFinding",
            "ReferenceFact",
            "DecoratorFact",
            "FunctionFact",
            "ExceptHandlerFact",
        )
        for name in prohibited:
            with self.subTest(name=name):
                self.assertFalse(hasattr(language, name))


if __name__ == "__main__":
    unittest.main()
