from __future__ import annotations

from unittest import mock
import unittest

from policy_fixture import (
    call_facts,
    call_policy,
    captured_error,
    empty_facts,
    forge,
    import_entries,
    import_facts,
    import_policy,
    policy_ids,
    require_language,
    require_policy_language,
)


class ArchitecturePolicyEvaluationTests(unittest.TestCase):
    def test_import_surface_equality_and_duplicate_preserving_mismatch_are_exact(self) -> None:
        policy = require_policy_language(self)
        facts = import_facts(self)
        exact = import_policy(self, facts)
        self.assertEqual(policy.evaluate_policy(facts, exact), ())

        expected = exact.expected_imports[:-1]
        mismatch = policy.ExactImportSurfacePolicy(
            exact.policy_id,
            exact.rule_id,
            exact.path,
            exact.module,
            expected,
            exact.message,
        )
        findings = policy.evaluate_policy(facts, mismatch)
        self.assertEqual(len(findings), 1)
        self.assertIs(type(findings[0]), policy.PolicyFinding)
        self.assertEqual(findings[0].message, exact.message)
        self.assertEqual((findings[0].location.line, findings[0].location.column), (1, 0))

    def test_call_surface_equality_and_resolved_unresolved_mismatch_are_exact(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        facts = call_facts(self)
        exact = call_policy(self, facts)
        self.assertEqual(policy.evaluate_policy(facts, exact), ())

        replacement = tuple(
            language.ResolvedCallTarget("registry.dynamic")
            if type(value) is language.UnresolvedCallTarget
            else value
            for value in exact.expected_calls
        )
        replacement = tuple(
            sorted(
                replacement,
                key=lambda value: (0, "")
                if type(value) is language.UnresolvedCallTarget
                else (1, value.qualified_name),
            )
        )
        mismatch = policy.ExactCallSurfacePolicy(
            exact.policy_id,
            exact.rule_id,
            exact.path,
            exact.module,
            replacement,
            exact.message,
        )
        self.assertEqual(len(policy.evaluate_policy(facts, mismatch)), 1)

    def test_single_policy_requires_the_exact_named_target(self) -> None:
        policy = require_policy_language(self)
        facts = empty_facts(self)
        named = import_policy(self, facts)
        foreign = empty_facts(self, path="package/foreign.py", module="package.foreign")
        error = captured_error(
            self,
            policy.PolicyEvaluationError,
            lambda: policy.evaluate_policy(foreign, named),
        )
        self.assertIs(type(error), policy.PolicyEvaluationError)
        self.assertEqual(str(error), "architecture policy target does not match facts")

    def test_batch_empty_and_absent_targets_are_total_without_silent_success(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        facts = empty_facts(self)
        named = import_policy(self, facts, message="required module is absent")
        self.assertEqual(policy.evaluate_policies((), ()), ())
        self.assertEqual(policy.evaluate_policies((facts,), ()), ())

        findings = policy.evaluate_policies((), (named,))
        self.assertEqual(
            findings,
            (
                policy.PolicyFinding(
                    named.policy_id,
                    named.rule_id,
                    language.SourceLocation(named.path, 1, 0),
                    named.message,
                ),
            ),
        )

    def test_duplicate_fact_coordinates_and_policy_ids_reject_before_findings(self) -> None:
        policy = require_policy_language(self)
        facts = empty_facts(self)
        duplicate = empty_facts(self)
        first = import_policy(self, facts)
        second = policy.ExactCallSurfacePolicy(
            first.policy_id,
            policy.RuleId("call-surface"),
            facts.path,
            facts.module,
            (),
            "call surface differs",
        )
        canary = RuntimeError("finding constructor dispatched")
        with mock.patch.object(policy.PolicyFinding, "__post_init__", side_effect=canary):
            fact_error = captured_error(
                self,
                policy.PolicyEvaluationError,
                lambda: policy.evaluate_policies((facts, duplicate), (first,)),
            )
            policy_error = captured_error(
                self,
                policy.PolicyEvaluationError,
                lambda: policy.evaluate_policies((facts,), (first, second)),
            )
        self.assertEqual(
            str(fact_error),
            "architecture facts contain duplicate target coordinates",
        )
        self.assertEqual(str(policy_error), "architecture policies contain duplicate identifiers")

    def test_batch_order_is_deterministic_and_distinct_findings_are_preserved(self) -> None:
        policy = require_policy_language(self)
        alpha = empty_facts(self, path="z.py", module="z")
        beta = empty_facts(self, path="a.py", module="a")
        first = policy.ExactImportSurfacePolicy(
            policy.PolicyId("z-policy"),
            policy.RuleId("same-rule"),
            alpha.path,
            alpha.module,
            (policy.ImportSurfaceEntry("missing", None, None),),
            "same-message",
        )
        second = policy.ExactImportSurfacePolicy(
            policy.PolicyId("a-policy"),
            policy.RuleId("same-rule"),
            beta.path,
            beta.module,
            (policy.ImportSurfaceEntry("missing", None, None),),
            "same-message",
        )
        findings = policy.evaluate_policies((alpha, beta), (first, second))
        self.assertEqual(len(findings), 2)
        self.assertEqual(tuple(value.location.path for value in findings), ("a.py", "z.py"))
        self.assertNotEqual(findings[0].policy_id, findings[1].policy_id)
        self.assertEqual((alpha.imports, beta.imports), ((), ()))

    def test_actual_surface_over_policy_cap_is_evaluated_when_work_is_bounded(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        location = language.SourceLocation("large.py", 1, 0)
        occurrence = language.CallFact(language.ResolvedCallTarget("run"), location)
        facts = language.PythonSourceFacts(
            "large.py",
            "large",
            (),
            (),
            tuple(occurrence for _ in range(4097)),
        )
        value = policy.ExactCallSurfacePolicy(
            policy.PolicyId("large-surface"),
            policy.RuleId("exact-calls"),
            facts.path,
            facts.module,
            (occurrence.target,),
            "large call surface differs",
        )
        findings = policy.evaluate_policies((facts,), (value,))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].message, value.message)

    def test_aggregate_occurrence_work_exact_max_and_plus_one_precede_deep_dispatch(self) -> None:
        language = require_language(self)
        policy = require_policy_language(self)
        location = language.SourceLocation("large.py", 1, 0)
        occurrence = language.CallFact(language.ResolvedCallTarget("run"), location)
        calls = tuple(occurrence for _ in range(30_719))
        facts = language.PythonSourceFacts("large.py", "large", (), (), calls)
        import_location = language.SourceLocation("imports.py", 1, 0)
        import_fact = language.ImportFact("dependency", None, None, import_location)
        imported = language.PythonSourceFacts(
            "imports.py",
            "imports",
            (import_fact,),
            (language.AliasBinding("dependency", "dependency"),),
            (),
        )
        expected = tuple(occurrence.target for _ in range(4096))
        value = policy.ExactCallSurfacePolicy(
            policy.PolicyId("maximum-work"),
            policy.RuleId("exact-calls"),
            facts.path,
            facts.module,
            expected,
            "large call surface differs",
        )
        occurrence_work = (
            len(facts.calls)
            + len(imported.imports)
            + len(imported.aliases)
            + len(expected)
            + len(facts.calls)
        )
        self.assertEqual(occurrence_work, 65_536)
        self.assertEqual(len(policy.evaluate_policies((facts, imported), (value,))), 1)

        foreign_location = language.SourceLocation("foreign.py", 1, 0)
        invalid_call = forge(language.CallFact, target=object(), location=foreign_location)
        foreign = forge(
            language.PythonSourceFacts,
            path="foreign.py",
            module="foreign",
            imports=(),
            aliases=(),
            calls=(invalid_call,),
        )
        finding_canary = RuntimeError("partial finding constructed")
        with mock.patch.object(
            policy.PolicyFinding,
            "__post_init__",
            side_effect=finding_canary,
        ):
            error = captured_error(
                self,
                policy.PolicyEvaluationError,
                lambda: policy.evaluate_policies((facts, imported, foreign), (value,)),
            )
        self.assertEqual(str(error), "architecture policy occurrence work exceeds 65536")

    def test_batch_outer_and_nested_admission_is_exact_before_interpretation(self) -> None:
        policy = require_policy_language(self)
        facts = empty_facts(self)
        value = import_policy(self, facts)
        for fact_values, policy_values in (
            ([facts], (value,)),
            ((facts,), [value]),
            ((facts,) * 4097, ()),
            ((facts,), (value,) * 1025),
            ((forge(type(facts), path=facts.path, module=facts.module, imports=(), aliases=(), calls=(object(),)),), (value,)),
            (
                (facts,),
                (
                    forge(
                        type(value),
                        policy_id=forge(policy.PolicyId, value="BAD"),
                        rule_id=value.rule_id,
                        path=value.path,
                        module=value.module,
                        expected_imports=value.expected_imports,
                        message=value.message,
                    ),
                ),
            ),
        ):
            with self.subTest(facts=type(fact_values), policies=type(policy_values)):
                error = captured_error(
                    self,
                    (TypeError, policy.PolicyEvaluationError),
                    lambda fact_values=fact_values, policy_values=policy_values: policy.evaluate_policies(
                        fact_values, policy_values
                    ),
                )
                self.assertIn(
                    str(error),
                    (
                        "architecture policy evaluation request is invalid",
                        "architecture policy occurrence work exceeds 65536",
                    ),
                )

    def test_errors_are_candidate_free_and_unexpected_internal_failures_remain_raw(self) -> None:
        policy = require_policy_language(self)
        facts = empty_facts(self)
        value = import_policy(self, facts)
        malformed = forge(
            type(facts),
            path=facts.path,
            module=facts.module,
            imports=(object(),),
            aliases=(),
            calls=(),
        )
        error = captured_error(
            self,
            policy.PolicyEvaluationError,
            lambda: policy.evaluate_policy(malformed, value),
        )
        self.assertEqual(str(error), "architecture policy evaluation request is invalid")
        self.assertNotIn("object", str(error))

        canary = RuntimeError("internal comparison canary")
        with mock.patch.object(policy, "_import_surface_key", side_effect=canary):
            with self.assertRaises(RuntimeError) as raised:
                policy.evaluate_policy(import_facts(self), import_policy(self, import_facts(self)))
        self.assertIs(raised.exception, canary)


if __name__ == "__main__":
    unittest.main()
