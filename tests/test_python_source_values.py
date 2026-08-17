from __future__ import annotations

from dataclasses import fields, FrozenInstanceError, is_dataclass
import importlib
import unittest

from source_fact_fixture import (
    HostileInt,
    HostileStr,
    HostileTuple,
    captured_error,
    forge,
    require_language,
)


ROOT_PACKAGE = importlib.import_module("control_plane_kit_architecture_testing")


class PythonSourceValueTests(unittest.TestCase):
    def test_public_values_have_exact_frozen_slotted_shapes_and_root_identity(self) -> None:
        language = require_language(self)
        expected_fields = {
            "SourceLocation": ("path", "line", "column"),
            "ImportFact": ("module", "imported_name", "bound_name", "location"),
            "AliasBinding": ("local_name", "qualified_name"),
            "ResolvedCallTarget": ("qualified_name",),
            "UnresolvedCallTarget": (),
            "CallFact": ("target", "location"),
            "PythonSourceFacts": ("path", "module", "imports", "aliases", "calls"),
        }

        for name, field_names in expected_fields.items():
            with self.subTest(name=name):
                exact_type = getattr(language, name)
                self.assertTrue(is_dataclass(exact_type))
                self.assertEqual(tuple(value.name for value in fields(exact_type)), field_names)
                self.assertIn("__slots__", exact_type.__dict__)
                self.assertIs(getattr(ROOT_PACKAGE, name), exact_type)

        self.assertEqual(
            language.CallTarget,
            language.ResolvedCallTarget | language.UnresolvedCallTarget,
        )
        self.assertIs(ROOT_PACKAGE.CallTarget, language.CallTarget)
        self.assertIs(ROOT_PACKAGE.SourceAnalysisError, language.SourceAnalysisError)
        self.assertIs(ROOT_PACKAGE.analyze_source, language.analyze_source)

    def test_source_location_is_exact_nominal_and_portably_bounded(self) -> None:
        language = require_language(self)
        maximum = language.SourceLocation("p" * 512, 2_147_483_647, 2_147_483_647)
        self.assertEqual(maximum.path, "p" * 512)

        candidates = (
            ("", 1, 0),
            ("p" * 513, 1, 0),
            ("bad\x00path", 1, 0),
            ("bad\ud800path", 1, 0),
            (HostileStr("sample.py"), 1, 0),
            ("sample.py", HostileInt(1), 0),
            ("sample.py", 0, 0),
            ("sample.py", 2_147_483_648, 0),
            ("sample.py", 1, -1),
            ("sample.py", 1, 2_147_483_648),
        )
        errors = []
        for path, line, column in candidates:
            with self.subTest(path=type(path), line=line, column=column):
                errors.append(
                    captured_error(
                        self,
                        (TypeError, ValueError),
                        lambda: language.SourceLocation(path, line, column),
                    )
                )
        for error in errors:
            self.assertLessEqual(len(str(error)), 160)
            for candidate in ("bad", "513", "2147483648"):
                self.assertNotIn(candidate, str(error))

    def test_import_fact_forms_and_alias_bindings_are_closed(self) -> None:
        language = require_language(self)
        location = language.SourceLocation("sample.py", 1, 0)
        values = (
            language.ImportFact("package.module", None, "package", location),
            language.ImportFact("package.module", None, "selected", location),
            language.ImportFact(".helpers", "run", "execute", location),
            language.ImportFact("package", "*", None, location),
        )
        self.assertEqual(
            tuple(value.qualified_name for value in values),
            ("package.module", "package.module", ".helpers.run", "package.*"),
        )
        self.assertEqual(
            language.AliasBinding("execute", ".helpers.run"),
            language.AliasBinding("execute", ".helpers.run"),
        )

        invalid = (
            ("package", None, None),
            ("package", "*", "star"),
            ("package", "run", None),
            ("", "run", "run"),
            (HostileStr("package"), None, "package"),
            ("package", HostileStr("run"), "run"),
            ("package", "run", HostileStr("run")),
            ("package", "run", "run", forge(language.SourceLocation, path="x.py", line=True, column=0)),
        )
        for candidate in invalid:
            with self.subTest(candidate=candidate[:3]):
                if len(candidate) == 3:
                    arguments = (*candidate, location)
                else:
                    arguments = candidate
                captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda arguments=arguments: language.ImportFact(*arguments),
                )

    def test_call_target_sum_and_qualified_names_are_exact(self) -> None:
        language = require_language(self)
        resolved = language.ResolvedCallTarget("package.module.run")
        unresolved = language.UnresolvedCallTarget()
        location = language.SourceLocation("sample.py", 1, 0)

        self.assertIs(type(resolved), language.ResolvedCallTarget)
        self.assertIs(type(unresolved), language.UnresolvedCallTarget)
        self.assertIs(type(language.CallFact(resolved, location)), language.CallFact)
        self.assertEqual(language.ResolvedCallTarget("q" * 4096).qualified_name, "q" * 4096)

        for candidate in ("", "q" * 4097, "bad\x00name", "bad\ud800name", HostileStr("run")):
            with self.subTest(candidate=type(candidate)):
                captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda candidate=candidate: language.ResolvedCallTarget(candidate),
                )

        class HostileResolved(language.ResolvedCallTarget):
            pass

        for target in (HostileResolved("run"), object()):
            with self.subTest(target=type(target)):
                captured_error(
                    self,
                    TypeError,
                    lambda target=target: language.CallFact(target, location),
                )

    def test_python_source_facts_require_exact_tuples_and_derived_aliases(self) -> None:
        language = require_language(self)
        location = language.SourceLocation("sample.py", 1, 0)
        import_fact = language.ImportFact("package.module", None, "package", location)
        alias = language.AliasBinding("package", "package")
        call = language.CallFact(
            language.ResolvedCallTarget("package.module.run"),
            language.SourceLocation("sample.py", 2, 0),
        )
        facts = language.PythonSourceFacts(
            "sample.py",
            "sample",
            (import_fact,),
            (alias,),
            (call,),
        )
        self.assertEqual(facts.imports, (import_fact,))

        invalid = (
            ([import_fact], (alias,), (call,)),
            ((import_fact,), HostileTuple((alias,)), (call,)),
            ((import_fact,), (alias,), (value for value in (call,))),
            ((import_fact,), (), (call,)),
            ((import_fact,), (language.AliasBinding("package", "other"),), (call,)),
            (
                (language.ImportFact("package", None, "package", language.SourceLocation("other.py", 1, 0)),),
                (alias,),
                (call,),
            ),
        )
        for imports, aliases, calls in invalid:
            with self.subTest(imports=type(imports), aliases=type(aliases), calls=type(calls)):
                captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda imports=imports, aliases=aliases, calls=calls: language.PythonSourceFacts(
                        "sample.py", "sample", imports, aliases, calls
                    ),
                )

    def test_nested_constructor_bypasses_and_hostile_subclasses_are_revalidated(self) -> None:
        language = require_language(self)
        location = language.SourceLocation("sample.py", 1, 0)
        target = language.ResolvedCallTarget("run")
        exact_call = language.CallFact(target, location)

        forged_location = forge(
            language.SourceLocation,
            path=HostileStr("sample.py"),
            line=1,
            column=0,
        )
        forged_target = forge(language.ResolvedCallTarget, qualified_name=HostileStr("run"))
        forged_call = forge(language.CallFact, target=forged_target, location=location)
        forged_import = forge(
            language.ImportFact,
            module="package",
            imported_name=None,
            bound_name="package",
            location=forged_location,
        )
        candidates = (
            ((forged_import,), (), ()),
            ((), (), (forged_call,)),
            ((), (), (forge(language.CallFact, target=target, location=forged_location),)),
        )
        for imports, aliases, calls in candidates:
            with self.subTest(imports=imports, calls=calls):
                captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda imports=imports, aliases=aliases, calls=calls: language.PythonSourceFacts(
                        "sample.py", "sample", imports, aliases, calls
                    ),
                )

        class HostileCall(language.CallFact):
            pass

        captured_error(
            self,
            TypeError,
            lambda: language.PythonSourceFacts(
                "sample.py", "sample", (), (), (HostileCall(target, location),)
            ),
        )
        self.assertIs(type(exact_call), language.CallFact)

    def test_values_are_immutable_and_repr_never_contains_source_or_literals(self) -> None:
        language = require_language(self)
        facts = language.analyze_source(
            "SECRET = 'literal-candidate'\nrun()\n",
            path="sample.py",
            module="sample",
        )
        with self.assertRaises(FrozenInstanceError):
            facts.path = "other.py"
        self.assertNotIn("literal-candidate", repr(facts))
        self.assertNotIn("SECRET", repr(facts))
        self.assertFalse(hasattr(facts, "source"))
        self.assertFalse(hasattr(facts, "tree"))


if __name__ == "__main__":
    unittest.main()
