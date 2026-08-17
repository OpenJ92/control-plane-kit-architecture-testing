from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Callable
import unittest

from source_fact_fixture import captured_error, forge, require_language


MODULE_NAME = "control_plane_kit_architecture_testing.architecture_policy"


def load_policy_language() -> ModuleType | None:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as error:
        if error.name != MODULE_NAME:
            raise
        return None


POLICY_LANGUAGE = load_policy_language()


def require_policy_language(case: unittest.TestCase) -> Any:
    case.assertIsNotNone(
        POLICY_LANGUAGE,
        "immutable architecture policies are not implemented",
    )
    return POLICY_LANGUAGE


class HostileStr(str):
    def encode(self, *args: object, **kwargs: object) -> bytes:
        raise RuntimeError("hostile string encode dispatched")

    def __len__(self) -> int:
        raise RuntimeError("hostile string length dispatched")


class HostileTuple(tuple):
    def __iter__(self):
        raise RuntimeError("hostile tuple iteration dispatched")


def empty_facts(
    case: unittest.TestCase,
    *,
    path: str = "package/sample.py",
    module: str = "package.sample",
):
    language = require_language(case)
    return language.PythonSourceFacts(path, module, (), (), ())


def import_facts(case: unittest.TestCase):
    language = require_language(case)
    return language.analyze_source(
        "import alpha\n"
        "import alpha as selected\n"
        "from beta import run\n"
        "from beta import run\n",
        path="package/sample.py",
        module="package.sample",
    )


def call_facts(case: unittest.TestCase):
    language = require_language(case)
    return language.analyze_source(
        "import service as selected\n"
        "selected.run()\n"
        "registry['dynamic']()\n"
        "selected.run()\n",
        path="package/sample.py",
        module="package.sample",
    )


def policy_ids(case: unittest.TestCase):
    policy = require_policy_language(case)
    return policy.PolicyId("package-surface"), policy.RuleId("exact-surface")


def import_entries(case: unittest.TestCase, facts) -> tuple:
    policy = require_policy_language(case)
    return tuple(
        sorted(
            (
                policy.ImportSurfaceEntry(
                    value.module,
                    value.imported_name,
                    value.alias_name,
                )
                for value in facts.imports
            ),
            key=lambda value: (
                value.module,
                (0, "")
                if value.imported_name is None
                else (1, value.imported_name),
                (0, "") if value.alias_name is None else (1, value.alias_name),
            ),
        )
    )


def call_targets(case: unittest.TestCase, facts) -> tuple:
    language = require_language(case)
    return tuple(
        sorted(
            (value.target for value in facts.calls),
            key=lambda value: (0, "")
            if type(value) is language.UnresolvedCallTarget
            else (1, value.qualified_name),
        )
    )


def import_policy(case: unittest.TestCase, facts, *, message: str = "import surface differs"):
    policy = require_policy_language(case)
    policy_id, rule_id = policy_ids(case)
    return policy.ExactImportSurfacePolicy(
        policy_id,
        rule_id,
        facts.path,
        facts.module,
        import_entries(case, facts),
        message,
    )


def call_policy(case: unittest.TestCase, facts, *, message: str = "call surface differs"):
    policy = require_policy_language(case)
    policy_id, rule_id = policy_ids(case)
    return policy.ExactCallSurfacePolicy(
        policy_id,
        rule_id,
        facts.path,
        facts.module,
        call_targets(case, facts),
        message,
    )


__all__ = (
    "HostileStr",
    "HostileTuple",
    "call_facts",
    "call_policy",
    "call_targets",
    "captured_error",
    "empty_facts",
    "forge",
    "import_entries",
    "import_facts",
    "import_policy",
    "policy_ids",
    "require_language",
    "require_policy_language",
)
