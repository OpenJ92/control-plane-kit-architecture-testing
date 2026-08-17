from __future__ import annotations

import ast
import unittest

from source_fact_fixture import require_language


class PythonSourceAnalysisTests(unittest.TestCase):
    def test_plain_dotted_aliased_relative_and_wildcard_imports_are_exact(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "import os\n"
            "import package.module\n"
            "import another.module as selected\n"
            "from .helpers import run as execute\n"
            "from . import local\n"
            "from package import *\n",
            path="package/sample.py",
            module="package.sample",
        )

        self.assertEqual(
            tuple(
                (value.module, value.imported_name, value.bound_name, value.qualified_name)
                for value in facts.imports
            ),
            (
                ("os", None, "os", "os"),
                ("package.module", None, "package", "package.module"),
                ("another.module", None, "selected", "another.module"),
                (".helpers", "run", "execute", ".helpers.run"),
                (".", "local", "local", ".local"),
                ("package", "*", None, "package.*"),
            ),
        )
        self.assertEqual(
            tuple((value.local_name, value.qualified_name) for value in facts.aliases),
            (
                ("os", "os"),
                ("package", "package"),
                ("selected", "another.module"),
                ("execute", ".helpers.run"),
                ("local", ".local"),
            ),
        )

    def test_dotted_import_binding_matches_python_lexical_semantics(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "import package.module\n"
            "import another.module as selected\n"
            "package.module.run()\n"
            "selected.run()\n",
            path="sample.py",
            module="sample",
        )

        self.assertEqual(
            tuple(type(value.target) for value in facts.calls),
            (language.ResolvedCallTarget, language.ResolvedCallTarget),
        )
        self.assertEqual(
            tuple(value.target.qualified_name for value in facts.calls),
            ("package.module.run", "another.module.run"),
        )

    def test_wildcard_and_conflicting_aliases_are_conservatively_unresolved(self) -> None:
        language = require_language(self)
        wildcard = language.analyze_source(
            "from package import *\n"
            "from known import exact\n"
            "direct()\n"
            "exact()\n",
            path="wildcard.py",
            module="wildcard",
        )
        conflict = language.analyze_source(
            "import first as selected\n"
            "import second as selected\n"
            "selected()\n",
            path="conflict.py",
            module="conflict",
        )
        repeated = language.analyze_source(
            "import first as selected\n"
            "import first as selected\n"
            "selected()\n",
            path="repeated.py",
            module="repeated",
        )

        self.assertIs(type(wildcard.calls[0].target), language.UnresolvedCallTarget)
        self.assertEqual(wildcard.calls[1].target.qualified_name, "known.exact")
        self.assertEqual(
            tuple(
                (value.local_name, value.qualified_name)
                for value in conflict.aliases
            ),
            (("selected", "first"), ("selected", "second")),
        )
        self.assertIs(type(conflict.calls[0].target), language.UnresolvedCallTarget)
        self.assertEqual(repeated.calls[0].target.qualified_name, "first")
        self.assertEqual(len(repeated.aliases), 2)

    def test_every_call_is_preserved_in_the_closed_target_sum(self) -> None:
        language = require_language(self)
        source = (
            "plain()\n"
            "owner.method()\n"
            "factory()()\n"
            "registry['name']()\n"
            "(lambda: None)()\n"
        )
        facts = language.analyze_source(source, path="calls.py", module="calls")
        parsed_call_count = sum(isinstance(node, ast.Call) for node in ast.walk(ast.parse(source)))

        self.assertEqual(len(facts.calls), parsed_call_count)
        self.assertEqual(
            tuple(
                value.target.qualified_name
                if type(value.target) is language.ResolvedCallTarget
                else None
                for value in facts.calls
            ),
            ("plain", "owner.method", None, "factory", None, None),
        )
        self.assertTrue(
            all(
                type(value.target)
                in (language.ResolvedCallTarget, language.UnresolvedCallTarget)
                for value in facts.calls
            )
        )

    def test_duplicate_calls_and_deterministic_source_order_are_preserved(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "outer(inner())\n"
            "repeat()\n"
            "repeat()\n",
            path="order.py",
            module="order",
        )
        self.assertEqual(
            tuple(value.target.qualified_name for value in facts.calls),
            ("outer", "inner", "repeat", "repeat"),
        )
        self.assertEqual(
            tuple((value.location.line, value.location.column) for value in facts.calls),
            ((1, 0), (1, 6), (2, 0), (3, 0)),
        )
        self.assertEqual(facts.calls[2].target, facts.calls[3].target)
        self.assertNotEqual(facts.calls[2].location, facts.calls[3].location)

    def test_comments_strings_docstrings_and_literals_produce_no_facts(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            '"""import requests; subprocess.run()"""\n'
            "# import httpx\n"
            "VALUE = \"os.environ.get('SECRET')\"\n",
            path="prose.py",
            module="prose",
        )
        self.assertEqual(facts.imports, ())
        self.assertEqual(facts.aliases, ())
        self.assertEqual(facts.calls, ())
        self.assertNotIn("SECRET", repr(facts))

    def test_non_ascii_call_column_is_the_ast_utf8_byte_offset(self) -> None:
        language = require_language(self)
        source = "é = 1; call()\n"
        character_index = source.index("call")
        expected_byte_offset = len(source[:character_index].encode("utf-8"))
        self.assertEqual(character_index, 7)
        self.assertEqual(expected_byte_offset, 8)

        facts = language.analyze_source(source, path="unicode.py", module="unicode")

        self.assertEqual(facts.calls[0].location.column, expected_byte_offset)
        self.assertNotEqual(facts.calls[0].location.column, character_index)

    def test_common_syntax_is_stable_under_the_executing_ast_grammar(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "def select(value):\n"
            "    match value:\n"
            "        case {'run': target}:\n"
            "            return target()\n"
            "        case _:\n"
            "            return fallback()\n",
            path="common.py",
            module="common",
        )
        self.assertEqual(
            tuple(value.target.qualified_name for value in facts.calls),
            ("target", "fallback"),
        )

    def test_analyzer_returns_exact_nominal_values_only(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "import package.module\npackage.module.run()\n",
            path="sample.py",
            module="sample",
        )
        self.assertIs(type(facts), language.PythonSourceFacts)
        self.assertTrue(all(type(value) is language.ImportFact for value in facts.imports))
        self.assertTrue(all(type(value) is language.AliasBinding for value in facts.aliases))
        self.assertTrue(all(type(value) is language.CallFact for value in facts.calls))
        self.assertTrue(all(type(value.location) is language.SourceLocation for value in facts.calls))


if __name__ == "__main__":
    unittest.main()
