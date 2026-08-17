"""Evaluate immutable exact import and lexical call surface policies."""

from __future__ import annotations

from dataclasses import dataclass

from control_plane_kit_architecture_testing.python_source import (
    CallTarget,
    ImportFact,
    PythonSourceFacts,
    ResolvedCallTarget,
    SourceLocation,
    UnresolvedCallTarget,
)


_MAX_IDENTIFIER_LENGTH = 200
_MAX_TEXT_LENGTH = 512
_MAX_QUALIFIED_NAME_LENGTH = 4096
_MAX_POLICY_SURFACE = 4096
_MAX_FACTS = 4096
_MAX_POLICIES = 1024
_MAX_OCCURRENCE_WORK = 65_536
_MAX_INT32 = 2_147_483_647

_IDENTIFIER_ERROR = "architecture policy identifier is invalid"
_VALUE_ERROR = "architecture policy value is invalid"
_REQUEST_ERROR = "architecture policy evaluation request is invalid"


def _raise_identifier_type_error() -> None:
    raise TypeError(_IDENTIFIER_ERROR)


def _raise_identifier_value_error() -> None:
    raise ValueError(_IDENTIFIER_ERROR)


def _raise_value_type_error() -> None:
    raise TypeError(_VALUE_ERROR)


def _raise_value_error() -> None:
    raise ValueError(_VALUE_ERROR)


def _raise_evaluation_error(message: str = _REQUEST_ERROR) -> None:
    raise PolicyEvaluationError(message)


def _utf8_bytes(value: str) -> bytes | None:
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError:
        return None


def _valid_text(value: object, maximum: int) -> bool:
    return (
        type(value) is str
        and 0 < len(value) <= maximum
        and not any(ord(character) < 32 for character in value)
        and _utf8_bytes(value) is not None
    )


def _valid_identifier(value: object) -> bool:
    if type(value) is not str or not 1 <= len(value) <= _MAX_IDENTIFIER_LENGTH:
        return False
    if not "a" <= value[0] <= "z":
        return False
    separator = False
    for character in value[1:]:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            separator = False
        elif character in ".-_" and not separator:
            separator = True
        else:
            return False
    return not separator


@dataclass(frozen=True, slots=True)
class PolicyId:
    """A bounded stable identity for one architecture policy."""

    value: str

    def __post_init__(self) -> None:
        if type(self) is not PolicyId or type(self.value) is not str:
            _raise_identifier_type_error()
        if not _valid_identifier(self.value):
            _raise_identifier_value_error()


@dataclass(frozen=True, slots=True)
class RuleId:
    """A bounded stable identity for one rule within a policy."""

    value: str

    def __post_init__(self) -> None:
        if type(self) is not RuleId or type(self.value) is not str:
            _raise_identifier_type_error()
        if not _valid_identifier(self.value):
            _raise_identifier_value_error()


def _valid_policy_id(value: object) -> bool:
    return type(value) is PolicyId and _valid_identifier(value.value)


def _valid_rule_id(value: object) -> bool:
    return type(value) is RuleId and _valid_identifier(value.value)


@dataclass(frozen=True, slots=True)
class ImportSurfaceEntry:
    """The location-free syntax identity of one import occurrence."""

    module: str
    imported_name: str | None
    alias_name: str | None

    def __post_init__(self) -> None:
        if (
            type(self.module) is not str
            or (self.imported_name is not None and type(self.imported_name) is not str)
            or (self.alias_name is not None and type(self.alias_name) is not str)
        ):
            _raise_value_type_error()
        if not _valid_import_surface_fields(self):
            _raise_value_error()


def _valid_import_surface_fields(value: ImportSurfaceEntry) -> bool:
    return (
        _valid_text(value.module, _MAX_TEXT_LENGTH)
        and (
            value.imported_name is None
            or _valid_text(value.imported_name, _MAX_TEXT_LENGTH)
        )
        and (
            value.alias_name is None
            or _valid_text(value.alias_name, _MAX_TEXT_LENGTH)
        )
        and not (value.imported_name == "*" and value.alias_name is not None)
    )


def _valid_import_surface_entry(value: object) -> bool:
    return type(value) is ImportSurfaceEntry and _valid_import_surface_fields(value)


def _optional_text_key(value: str | None) -> tuple[int, str]:
    if value is None:
        return (0, "")
    return (1, value)


def _import_surface_key(
    value: ImportSurfaceEntry,
) -> tuple[str, tuple[int, str], tuple[int, str]]:
    return (
        value.module,
        _optional_text_key(value.imported_name),
        _optional_text_key(value.alias_name),
    )


def _valid_call_target(value: object) -> bool:
    if type(value) is UnresolvedCallTarget:
        return True
    return type(value) is ResolvedCallTarget and _valid_text(
        value.qualified_name,
        _MAX_QUALIFIED_NAME_LENGTH,
    )


def _call_surface_key(value: CallTarget) -> tuple[int, str]:
    if type(value) is UnresolvedCallTarget:
        return (0, "")
    return (1, value.qualified_name)


def _is_canonical(values: tuple, key) -> bool:
    if len(values) < 2:
        return True
    previous = key(values[0])
    for value in values[1:]:
        current = key(value)
        if current < previous:
            return False
        previous = current
    return True


def _valid_policy_coordinates(path: object, module: object, message: object) -> bool:
    return (
        _valid_text(path, _MAX_TEXT_LENGTH)
        and _valid_text(module, _MAX_TEXT_LENGTH)
        and _valid_text(message, _MAX_TEXT_LENGTH)
    )


@dataclass(frozen=True, slots=True)
class ExactImportSurfacePolicy:
    """Require one module's import-occurrence multiset to match exactly."""

    policy_id: PolicyId
    rule_id: RuleId
    path: str
    module: str
    expected_imports: tuple[ImportSurfaceEntry, ...]
    message: str

    def __post_init__(self) -> None:
        if (
            type(self) is not ExactImportSurfacePolicy
            or type(self.policy_id) is not PolicyId
            or type(self.rule_id) is not RuleId
            or type(self.path) is not str
            or type(self.module) is not str
            or type(self.expected_imports) is not tuple
            or type(self.message) is not str
        ):
            _raise_value_type_error()
        if not _valid_import_policy(self):
            _raise_value_error()


def _valid_import_policy(value: object) -> bool:
    return (
        type(value) is ExactImportSurfacePolicy
        and _valid_policy_id(value.policy_id)
        and _valid_rule_id(value.rule_id)
        and _valid_policy_coordinates(value.path, value.module, value.message)
        and type(value.expected_imports) is tuple
        and len(value.expected_imports) <= _MAX_POLICY_SURFACE
        and all(
            _valid_import_surface_entry(entry)
            for entry in value.expected_imports
        )
        and _is_canonical(value.expected_imports, _import_surface_key)
    )


@dataclass(frozen=True, slots=True)
class ExactCallSurfacePolicy:
    """Require one module's lexical call-target multiset to match exactly."""

    policy_id: PolicyId
    rule_id: RuleId
    path: str
    module: str
    expected_calls: tuple[CallTarget, ...]
    message: str

    def __post_init__(self) -> None:
        if (
            type(self) is not ExactCallSurfacePolicy
            or type(self.policy_id) is not PolicyId
            or type(self.rule_id) is not RuleId
            or type(self.path) is not str
            or type(self.module) is not str
            or type(self.expected_calls) is not tuple
            or type(self.message) is not str
        ):
            _raise_value_type_error()
        if not _valid_call_policy(self):
            _raise_value_error()


def _valid_call_policy(value: object) -> bool:
    return (
        type(value) is ExactCallSurfacePolicy
        and _valid_policy_id(value.policy_id)
        and _valid_rule_id(value.rule_id)
        and _valid_policy_coordinates(value.path, value.module, value.message)
        and type(value.expected_calls) is tuple
        and len(value.expected_calls) <= _MAX_POLICY_SURFACE
        and all(_valid_call_target(target) for target in value.expected_calls)
        and _is_canonical(value.expected_calls, _call_surface_key)
    )


ArchitecturePolicy = ExactImportSurfacePolicy | ExactCallSurfacePolicy


def _valid_location(value: object) -> bool:
    return (
        type(value) is SourceLocation
        and _valid_text(value.path, _MAX_TEXT_LENGTH)
        and type(value.line) is int
        and 1 <= value.line <= _MAX_INT32
        and type(value.column) is int
        and 0 <= value.column <= _MAX_INT32
    )


@dataclass(frozen=True, slots=True)
class PolicyFinding:
    """One bounded policy-authored mismatch at a module anchor."""

    policy_id: PolicyId
    rule_id: RuleId
    location: SourceLocation
    message: str

    def __post_init__(self) -> None:
        if (
            type(self) is not PolicyFinding
            or type(self.policy_id) is not PolicyId
            or type(self.rule_id) is not RuleId
            or type(self.location) is not SourceLocation
            or type(self.message) is not str
        ):
            _raise_value_type_error()
        if not _valid_finding(self):
            _raise_value_error()


def _valid_finding(value: object) -> bool:
    return (
        type(value) is PolicyFinding
        and _valid_policy_id(value.policy_id)
        and _valid_rule_id(value.rule_id)
        and _valid_location(value.location)
        and _valid_text(value.message, _MAX_TEXT_LENGTH)
    )


class PolicyEvaluationError(ValueError):
    """A bounded categorical architecture-policy evaluation failure."""


def _valid_source_facts(value: object) -> bool:
    if type(value) is not PythonSourceFacts:
        return False
    invalid = False
    try:
        PythonSourceFacts(
            value.path,
            value.module,
            value.imports,
            value.aliases,
            value.calls,
        )
    except (TypeError, ValueError) as error:
        if type(error) in (TypeError, ValueError) and str(error) == "python source fact is invalid":
            invalid = True
        else:
            raise
    return not invalid


def _valid_policy(value: object) -> bool:
    if type(value) is ExactImportSurfacePolicy:
        return _valid_import_policy(value)
    if type(value) is ExactCallSurfacePolicy:
        return _valid_call_policy(value)
    return False


def _policy_id(value: ArchitecturePolicy) -> PolicyId:
    return value.policy_id


def _rule_id(value: ArchitecturePolicy) -> RuleId:
    return value.rule_id


def _finding(value: ArchitecturePolicy) -> PolicyFinding:
    return PolicyFinding(
        _policy_id(value),
        _rule_id(value),
        SourceLocation(value.path, 1, 0),
        value.message,
    )


def _project_imports(facts: PythonSourceFacts) -> tuple[ImportSurfaceEntry, ...]:
    values = []
    for value in facts.imports:
        if type(value) is not ImportFact:
            _raise_evaluation_error()
        values.append(
            ImportSurfaceEntry(
                value.module,
                value.imported_name,
                value.alias_name,
            )
        )
    return tuple(sorted(values, key=_import_surface_key))


def _project_calls(facts: PythonSourceFacts) -> tuple[CallTarget, ...]:
    return tuple(sorted((value.target for value in facts.calls), key=_call_surface_key))


def evaluate_policy(
    facts: PythonSourceFacts,
    policy: ArchitecturePolicy,
) -> tuple[PolicyFinding, ...]:
    """Evaluate one exact fact/policy target pair."""

    if not _valid_source_facts(facts) or not _valid_policy(policy):
        _raise_evaluation_error()
    if (facts.path, facts.module) != (policy.path, policy.module):
        _raise_evaluation_error("architecture policy target does not match facts")
    if type(policy) is ExactImportSurfacePolicy:
        matches = _project_imports(facts) == policy.expected_imports
    else:
        matches = _project_calls(facts) == policy.expected_calls
    if matches:
        return ()
    return (_finding(policy),)


def _batch_outer_valid(
    facts: object,
    policies: object,
) -> bool:
    if (
        type(facts) is not tuple
        or type(policies) is not tuple
        or len(facts) > _MAX_FACTS
        or len(policies) > _MAX_POLICIES
    ):
        return False
    for value in facts:
        if (
            type(value) is not PythonSourceFacts
            or type(value.path) is not str
            or type(value.module) is not str
            or type(value.imports) is not tuple
            or type(value.aliases) is not tuple
            or type(value.calls) is not tuple
        ):
            return False
    for value in policies:
        if type(value) is ExactImportSurfacePolicy:
            expected = value.expected_imports
        elif type(value) is ExactCallSurfacePolicy:
            expected = value.expected_calls
        else:
            return False
        if (
            type(value.policy_id) is not PolicyId
            or type(value.policy_id.value) is not str
            or type(value.path) is not str
            or type(value.module) is not str
            or type(expected) is not tuple
        ):
            return False
    return True


def _fact_index(
    facts: tuple[PythonSourceFacts, ...],
) -> dict[tuple[str, str], PythonSourceFacts]:
    values: dict[tuple[str, str], PythonSourceFacts] = {}
    for value in facts:
        coordinate = (value.path, value.module)
        if coordinate in values:
            _raise_evaluation_error(
                "architecture facts contain duplicate target coordinates"
            )
        values[coordinate] = value
    return values


def _require_unique_policy_ids(policies: tuple[ArchitecturePolicy, ...]) -> None:
    values = set()
    for value in policies:
        identity = value.policy_id.value
        if identity in values:
            _raise_evaluation_error(
                "architecture policies contain duplicate identifiers"
            )
        values.add(identity)


def _expected_occurrences(value: ArchitecturePolicy) -> int:
    if type(value) is ExactImportSurfacePolicy:
        return len(value.expected_imports)
    return len(value.expected_calls)


def _projected_occurrences(
    value: ArchitecturePolicy,
    facts: PythonSourceFacts | None,
) -> int:
    if facts is None:
        return 0
    if type(value) is ExactImportSurfacePolicy:
        return len(facts.imports)
    return len(facts.calls)


def _require_bounded_occurrence_work(
    facts: tuple[PythonSourceFacts, ...],
    policies: tuple[ArchitecturePolicy, ...],
    indexed: dict[tuple[str, str], PythonSourceFacts],
) -> None:
    fact_occurrences = sum(
        len(value.imports) + len(value.aliases) + len(value.calls)
        for value in facts
    )
    expected_occurrences = sum(_expected_occurrences(value) for value in policies)
    projected_occurrences = sum(
        _projected_occurrences(value, indexed.get((value.path, value.module)))
        for value in policies
    )
    if (
        fact_occurrences + expected_occurrences + projected_occurrences
        > _MAX_OCCURRENCE_WORK
    ):
        _raise_evaluation_error("architecture policy occurrence work exceeds 65536")


def _finding_key(
    value: PolicyFinding,
) -> tuple[str, int, int, str, str, str]:
    return (
        value.location.path,
        value.location.line,
        value.location.column,
        value.policy_id.value,
        value.rule_id.value,
        value.message,
    )


def evaluate_policies(
    facts: tuple[PythonSourceFacts, ...],
    policies: tuple[ArchitecturePolicy, ...],
) -> tuple[PolicyFinding, ...]:
    """Evaluate a bounded deterministic batch of exact policies."""

    if not _batch_outer_valid(facts, policies):
        _raise_evaluation_error()
    indexed = _fact_index(facts)
    _require_unique_policy_ids(policies)
    _require_bounded_occurrence_work(facts, policies, indexed)
    if not all(_valid_source_facts(value) for value in facts) or not all(
        _valid_policy(value) for value in policies
    ):
        _raise_evaluation_error()

    findings = []
    for policy in sorted(policies, key=lambda value: value.policy_id.value):
        target = indexed.get((policy.path, policy.module))
        if target is None:
            findings.append(_finding(policy))
        else:
            findings.extend(evaluate_policy(target, policy))
    return tuple(sorted(findings, key=_finding_key))
