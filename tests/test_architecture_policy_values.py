from __future__ import annotations

from dataclasses import fields, FrozenInstanceError, is_dataclass
import importlib
import unittest

from policy_fixture import (
    HostileStr,
    HostileTuple,
    call_facts,
    captured_error,
    empty_facts,
    forge,
    import_facts,
    policy_ids,
    require_language,
    require_policy_language,
)


ROOT_PACKAGE = importlib.import_module("control_plane_kit_architecture_testing")


class ArchitecturePolicyValueTests(unittest.TestCase):
    def test_public_values_have_exact_frozen_slotted_shapes_and_root_identity(self) -> None:
        policy = require_policy_language(self)
        expected_fields = {
            "PolicyId": ("value",),
            "RuleId": ("value",),
            "ImportSurfaceEntry": ("module", "imported_name", "alias_name"),
            "ExactImportSurfacePolicy": (
                "policy_id",
                "rule_id",
                "path",
                "module",
                "expected_imports",
                "message",
            ),
            "ExactCallSurfacePolicy": (
                "policy_id",
                "rule_id",
                "path",
                "module",
                "expected_calls",
                "message",
            ),
            "PolicyFinding": ("policy_id", "rule_id", "location", "message"),
        }
        for name, field_names in expected_fields.items():
            with self.subTest(name=name):
                exact_type = getattr(policy, name)
                self.assertTrue(is_dataclass(exact_type))
                self.assertTrue(exact_type.__dataclass_params__.frozen)
                self.assertEqual(tuple(value.name for value in fields(exact_type)), field_names)
                self.assertIn("__slots__", exact_type.__dict__)
                self.assertIs(getattr(ROOT_PACKAGE, name), exact_type)

        self.assertEqual(
            policy.ArchitecturePolicy,
            policy.ExactImportSurfacePolicy | policy.ExactCallSurfacePolicy,
        )
        for name in (
            "ArchitecturePolicy",
            "PolicyEvaluationError",
            "evaluate_policy",
            "evaluate_policies",
        ):
            self.assertIs(getattr(ROOT_PACKAGE, name), getattr(policy, name))

    def test_policy_and_rule_identifiers_are_exact_nominal_machine_values(self) -> None:
        policy = require_policy_language(self)
        for exact_type in (policy.PolicyId, policy.RuleId):
            with self.subTest(exact_type=exact_type.__name__):
                self.assertEqual(exact_type("a").value, "a")
                self.assertEqual(exact_type("a" * 200).value, "a" * 200)
                for candidate in (
                    "",
                    "a" * 201,
                    "Upper",
                    "9first",
                    "two--parts",
                    "trailing-",
                    "bad space",
                    "bad\x00id",
                    "bad\ud800id",
                    HostileStr("valid-id"),
                ):
                    with self.subTest(candidate=type(candidate)):
                        error = captured_error(
                            self,
                            (TypeError, ValueError),
                            lambda candidate=candidate: exact_type(candidate),
                        )
                        self.assertEqual(str(error), "architecture policy identifier is invalid")
                        self.assertNotIn("valid", str(error))

    def test_import_surface_and_policy_are_canonical_deep_nominal_values(self) -> None:
        policy = require_policy_language(self)
        facts = import_facts(self)
        policy_id, rule_id = policy_ids(self)
        location_free = policy.ImportSurfaceEntry("alpha", None, None)
        aliased = policy.ImportSurfaceEntry("alpha", None, "selected")
        imported = policy.ImportSurfaceEntry("beta", "run", None)
        expected = (location_free, aliased, imported, imported)
        value = policy.ExactImportSurfacePolicy(
            policy_id,
            rule_id,
            facts.path,
            facts.module,
            expected,
            "import surface differs",
        )
        self.assertEqual(value.expected_imports, expected)

        for module, imported_name, alias_name in (
            ("", None, None),
            ("m" * 513, None, None),
            ("bad\x00module", None, None),
            ("bad\ud800module", None, None),
            (HostileStr("alpha"), None, None),
            ("alpha", "i" * 513, None),
            ("alpha", "bad\x00member", None),
            ("alpha", "bad\ud800member", None),
            ("alpha", HostileStr("member"), None),
            ("alpha", None, "a" * 513),
            ("alpha", None, "bad\x00alias"),
            ("alpha", None, "bad\ud800alias"),
            ("alpha", None, HostileStr("alias")),
        ):
            with self.subTest(
                module=type(module),
                imported_name=type(imported_name),
                alias_name=type(alias_name),
            ):
                error = captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda module=module, imported_name=imported_name, alias_name=alias_name: policy.ImportSurfaceEntry(
                        module, imported_name, alias_name
                    ),
                )
                self.assertEqual(str(error), "architecture policy value is invalid")

        class HostileEntry(policy.ImportSurfaceEntry):
            pass

        invalid_entries = (
            policy.ImportSurfaceEntry("alpha", "member", None),
            forge(policy.ImportSurfaceEntry, module="alpha", imported_name=HostileStr("member"), alias_name=None),
            HostileEntry("alpha", None, None),
        )
        for entries in (
            (invalid_entries[0], location_free),
            (invalid_entries[1],),
            (invalid_entries[2],),
            HostileTuple(expected),
            tuple(location_free for _ in range(4097)),
        ):
            with self.subTest(entries=type(entries)):
                error = captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda entries=entries: policy.ExactImportSurfacePolicy(
                        policy_id,
                        rule_id,
                        facts.path,
                        facts.module,
                        entries,
                        "import surface differs",
                    ),
                )
                self.assertEqual(str(error), "architecture policy value is invalid")

    def test_call_policy_requires_the_exact_tagged_canonical_target_sum(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        facts = call_facts(self)
        policy_id, rule_id = policy_ids(self)
        unresolved = language.UnresolvedCallTarget()
        resolved = language.ResolvedCallTarget("service.run")
        expected = (unresolved, resolved, resolved)
        value = policy.ExactCallSurfacePolicy(
            policy_id,
            rule_id,
            facts.path,
            facts.module,
            expected,
            "call surface differs",
        )
        self.assertEqual(value.expected_calls, expected)

        class HostileTarget(language.ResolvedCallTarget):
            pass

        for targets in (
            (resolved, unresolved),
            (HostileTarget("service.run"),),
            (forge(language.ResolvedCallTarget, qualified_name=HostileStr("service.run")),),
            [resolved],
            tuple(resolved for _ in range(4097)),
        ):
            with self.subTest(targets=type(targets)):
                error = captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda targets=targets: policy.ExactCallSurfacePolicy(
                        policy_id,
                        rule_id,
                        facts.path,
                        facts.module,
                        targets,
                        "call surface differs",
                    ),
                )
                self.assertEqual(str(error), "architecture policy value is invalid")

    def test_finding_and_policy_boundaries_are_bounded_redacted_and_immutable(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        policy_id, rule_id = policy_ids(self)
        finding = policy.PolicyFinding(
            policy_id,
            rule_id,
            language.SourceLocation("p" * 512, 1, 0),
            "m" * 512,
        )
        with self.assertRaises(FrozenInstanceError):
            finding.message = "other"
        self.assertNotIn("source", finding.__dict__ if hasattr(finding, "__dict__") else ())

        facts = empty_facts(self)
        for path, module, message in (
            ("", facts.module, "message"),
            ("p" * 513, facts.module, "message"),
            (facts.path, "", "message"),
            (facts.path, "m" * 513, "message"),
            (facts.path, facts.module, ""),
            (facts.path, facts.module, "x" * 513),
            ("bad\x00path", facts.module, "message"),
            ("bad\ud800path", facts.module, "message"),
            (facts.path, "bad\x00module", "message"),
            (facts.path, "bad\ud800module", "message"),
            (facts.path, facts.module, "bad\x00message"),
            (HostileStr(facts.path), facts.module, "message"),
            (facts.path, HostileStr(facts.module), "message"),
            (facts.path, facts.module, HostileStr("message")),
            (facts.path, facts.module, "secret\ud800candidate"),
        ):
            with self.subTest(path=type(path), module=type(module), message=type(message)):
                error = captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda path=path, module=module, message=message: policy.ExactImportSurfacePolicy(
                        policy_id, rule_id, path, module, (), message
                    ),
                )
                self.assertEqual(str(error), "architecture policy value is invalid")
                self.assertNotIn("secret", str(error))

        forged_id = forge(policy.PolicyId, value=HostileStr("package-surface"))
        forged_location = forge(
            language.SourceLocation,
            path=HostileStr("package/sample.py"),
            line=1,
            column=0,
        )
        for candidate in (
            (forged_id, rule_id, language.SourceLocation(facts.path, 1, 0), "message"),
            (policy_id, rule_id, forged_location, "message"),
        ):
            error = captured_error(
                self,
                (TypeError, ValueError),
                lambda candidate=candidate: policy.PolicyFinding(*candidate),
            )
            self.assertEqual(str(error), "architecture policy value is invalid")

        error = captured_error(
            self,
            (TypeError, ValueError),
            lambda: policy.ExactImportSurfacePolicy(
                forged_id,
                rule_id,
                facts.path,
                facts.module,
                (),
                "message",
            ),
        )
        self.assertEqual(str(error), "architecture policy value is invalid")


if __name__ == "__main__":
    unittest.main()
