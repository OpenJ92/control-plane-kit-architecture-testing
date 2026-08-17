"""Convert Python source text into immutable lexical architecture facts."""

from __future__ import annotations

import ast
from dataclasses import dataclass


_MAX_COORDINATE_LENGTH = 512
_MAX_QUALIFIED_NAME_LENGTH = 4096
_MAX_SOURCE_BYTES = 1_048_576
_MAX_INT32 = 2_147_483_647
_FACT_ERROR = "python source fact is invalid"
_REQUEST_ERROR = "python source request is invalid"


def _raise_fact_type_error() -> None:
    raise TypeError(_FACT_ERROR)


def _raise_fact_value_error() -> None:
    raise ValueError(_FACT_ERROR)


def _utf8_bytes(value: str) -> bytes | None:
    try:
        return value.encode("utf-8")
    except UnicodeEncodeError:
        return None


def _valid_text(value: object, maximum: int) -> bool:
    return (
        type(value) is str
        and 0 < len(value) <= maximum
        and "\x00" not in value
        and not any(ord(character) < 32 for character in value)
        and _utf8_bytes(value) is not None
    )


def _require_text(value: object, maximum: int) -> None:
    if type(value) is not str:
        _raise_fact_type_error()
    if not _valid_text(value, maximum):
        _raise_fact_value_error()


def _valid_location(value: object) -> bool:
    return (
        type(value) is SourceLocation
        and _valid_text(value.path, _MAX_COORDINATE_LENGTH)
        and type(value.line) is int
        and 1 <= value.line <= _MAX_INT32
        and type(value.column) is int
        and 0 <= value.column <= _MAX_INT32
    )


def _require_location(value: object) -> None:
    if type(value) is not SourceLocation:
        _raise_fact_type_error()
    if not _valid_location(value):
        _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class SourceLocation:
    """One bounded source coordinate using Python AST location semantics."""

    path: str
    line: int
    column: int

    def __post_init__(self) -> None:
        if type(self.path) is not str or type(self.line) is not int or type(self.column) is not int:
            _raise_fact_type_error()
        if not _valid_location(self):
            _raise_fact_value_error()


def _valid_import_fact(value: object) -> bool:
    if type(value) is not ImportFact:
        return False
    if not _valid_text(value.module, _MAX_COORDINATE_LENGTH):
        return False
    if value.imported_name is not None and not _valid_text(
        value.imported_name, _MAX_COORDINATE_LENGTH
    ):
        return False
    if value.bound_name is not None and not _valid_text(
        value.bound_name, _MAX_COORDINATE_LENGTH
    ):
        return False
    if value.imported_name is None:
        if value.bound_name is None:
            return False
    elif value.imported_name == "*":
        if value.bound_name is not None:
            return False
    elif value.bound_name is None:
        return False
    return _valid_location(value.location)


def _require_import_fact(value: object) -> None:
    if type(value) is not ImportFact:
        _raise_fact_type_error()
    if not _valid_import_fact(value):
        _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class ImportFact:
    """One plain or from-import occurrence and its lexical binding."""

    module: str
    imported_name: str | None
    bound_name: str | None
    location: SourceLocation

    def __post_init__(self) -> None:
        if (
            type(self.module) is not str
            or (self.imported_name is not None and type(self.imported_name) is not str)
            or (self.bound_name is not None and type(self.bound_name) is not str)
            or type(self.location) is not SourceLocation
        ):
            _raise_fact_type_error()
        if not _valid_import_fact(self):
            _raise_fact_value_error()

    @property
    def qualified_name(self) -> str:
        if self.imported_name is None:
            return self.module
        separator = "" if self.module.endswith(".") else "."
        return f"{self.module}{separator}{self.imported_name}"


def _valid_alias_binding(value: object) -> bool:
    return (
        type(value) is AliasBinding
        and _valid_text(value.local_name, _MAX_COORDINATE_LENGTH)
        and _valid_text(value.qualified_name, _MAX_QUALIFIED_NAME_LENGTH)
    )


def _require_alias_binding(value: object) -> None:
    if type(value) is not AliasBinding:
        _raise_fact_type_error()
    if not _valid_alias_binding(value):
        _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class AliasBinding:
    """One import-derived local name and its qualified lexical name."""

    local_name: str
    qualified_name: str

    def __post_init__(self) -> None:
        if type(self.local_name) is not str or type(self.qualified_name) is not str:
            _raise_fact_type_error()
        if not _valid_alias_binding(self):
            _raise_fact_value_error()


def _valid_resolved_target(value: object) -> bool:
    return type(value) is ResolvedCallTarget and _valid_text(
        value.qualified_name, _MAX_QUALIFIED_NAME_LENGTH
    )


def _require_resolved_target(value: object) -> None:
    if type(value) is not ResolvedCallTarget:
        _raise_fact_type_error()
    if not _valid_resolved_target(value):
        _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class ResolvedCallTarget:
    """A call target with an exact lexical qualification."""

    qualified_name: str

    def __post_init__(self) -> None:
        if type(self.qualified_name) is not str:
            _raise_fact_type_error()
        if not _valid_text(self.qualified_name, _MAX_QUALIFIED_NAME_LENGTH):
            _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class UnresolvedCallTarget:
    """A call target whose expression has no safe lexical qualification."""


CallTarget = ResolvedCallTarget | UnresolvedCallTarget


def _valid_call_fact(value: object) -> bool:
    if type(value) is not CallFact:
        return False
    if type(value.target) is ResolvedCallTarget:
        if not _valid_resolved_target(value.target):
            return False
    elif type(value.target) is not UnresolvedCallTarget:
        return False
    return _valid_location(value.location)


def _require_call_fact(value: object) -> None:
    if type(value) is not CallFact:
        _raise_fact_type_error()
    if not _valid_call_fact(value):
        _raise_fact_value_error()


@dataclass(frozen=True, slots=True)
class CallFact:
    """One syntactic call occurrence and its closed lexical target."""

    target: CallTarget
    location: SourceLocation

    def __post_init__(self) -> None:
        if (
            type(self.target) not in (ResolvedCallTarget, UnresolvedCallTarget)
            or type(self.location) is not SourceLocation
        ):
            _raise_fact_type_error()
        if (
            type(self.target) is ResolvedCallTarget
            and not _valid_resolved_target(self.target)
        ) or not _valid_location(self.location):
            _raise_fact_value_error()


def _binding_for_import(value: ImportFact) -> AliasBinding | None:
    if value.bound_name is None:
        return None
    if (
        value.imported_name is None
        and "." in value.module
        and value.bound_name == value.module.split(".", 1)[0]
    ):
        qualified_name = value.bound_name
    else:
        qualified_name = value.qualified_name
    return AliasBinding(value.bound_name, qualified_name)


def _derived_aliases(imports: tuple[ImportFact, ...]) -> tuple[AliasBinding, ...]:
    values: list[AliasBinding] = []
    for value in imports:
        binding = _binding_for_import(value)
        if binding is not None:
            values.append(binding)
    return tuple(values)


def _valid_source_facts(value: object) -> bool:
    if type(value) is not PythonSourceFacts:
        return False
    if not _valid_text(value.path, _MAX_COORDINATE_LENGTH):
        return False
    if not _valid_text(value.module, _MAX_COORDINATE_LENGTH):
        return False
    if type(value.imports) is not tuple or type(value.aliases) is not tuple or type(value.calls) is not tuple:
        return False
    for import_fact in value.imports:
        if not _valid_import_fact(import_fact) or import_fact.location.path != value.path:
            return False
    for alias in value.aliases:
        if not _valid_alias_binding(alias):
            return False
    for call in value.calls:
        if not _valid_call_fact(call) or call.location.path != value.path:
            return False
    return value.aliases == _derived_aliases(value.imports)


@dataclass(frozen=True, slots=True)
class PythonSourceFacts:
    """The immutable lexical source-fact quotient of one Python module."""

    path: str
    module: str
    imports: tuple[ImportFact, ...]
    aliases: tuple[AliasBinding, ...]
    calls: tuple[CallFact, ...]

    def __post_init__(self) -> None:
        if (
            type(self.path) is not str
            or type(self.module) is not str
            or type(self.imports) is not tuple
            or type(self.aliases) is not tuple
            or type(self.calls) is not tuple
            or any(type(value) is not ImportFact for value in self.imports)
            or any(type(value) is not AliasBinding for value in self.aliases)
            or any(type(value) is not CallFact for value in self.calls)
        ):
            _raise_fact_type_error()
        if not _valid_source_facts(self):
            _raise_fact_value_error()


class SourceAnalysisError(ValueError):
    """A bounded source-analysis failure without source or literal evidence."""

    __slots__ = ("path", "line", "column")

    def __init__(self, message: str, *, path: str, line: int, column: int) -> None:
        self.path = path
        self.line = line
        self.column = column
        super().__init__(message)


def _raise_request_type_error() -> None:
    raise TypeError(_REQUEST_ERROR)


def _raise_request_value_error() -> None:
    raise ValueError(_REQUEST_ERROR)


def _source_limit_error(path: str) -> SourceAnalysisError:
    return SourceAnalysisError(
        "python source exceeds analysis limit",
        path=path,
        line=0,
        column=0,
    )


def _fact_limit_error(path: str, node: ast.AST) -> SourceAnalysisError:
    return SourceAnalysisError(
        "python source facts exceed analysis limit",
        path=path,
        line=getattr(node, "lineno", 0),
        column=getattr(node, "col_offset", 0),
    )


def _source_location(path: str, node: ast.AST) -> SourceLocation:
    line = getattr(node, "lineno", 0)
    column = getattr(node, "col_offset", 0)
    if (
        type(line) is not int
        or not 1 <= line <= _MAX_INT32
        or type(column) is not int
        or not 0 <= column <= _MAX_INT32
    ):
        raise _fact_limit_error(path, node)
    return SourceLocation(path, line, column)


def _preorder_nodes(tree: ast.AST) -> tuple[ast.AST, ...]:
    values: list[ast.AST] = []
    pending = [tree]
    while pending:
        node = pending.pop()
        values.append(node)
        children = list(ast.iter_child_nodes(node))
        pending.extend(reversed(children))
    return tuple(values)


def _source_ordered_nodes(tree: ast.AST, exact_type: type) -> tuple[ast.AST, ...]:
    indexed = tuple(
        (node, index)
        for index, node in enumerate(_preorder_nodes(tree))
        if isinstance(node, exact_type)
    )
    return tuple(
        node
        for node, _ in sorted(
            indexed,
            key=lambda item: (
                getattr(item[0], "lineno", 0),
                getattr(item[0], "col_offset", 0),
                item[1],
            ),
        )
    )


def _import_facts(tree: ast.AST, path: str) -> tuple[ImportFact, ...]:
    values: list[ImportFact] = []
    import_nodes = _source_ordered_nodes(tree, (ast.Import, ast.ImportFrom))
    for node in import_nodes:
        if isinstance(node, ast.Import):
            for imported in node.names:
                module = imported.name
                bound_name = imported.asname or imported.name.split(".", 1)[0]
                if not _valid_text(module, _MAX_COORDINATE_LENGTH) or not _valid_text(
                    bound_name, _MAX_COORDINATE_LENGTH
                ):
                    raise _fact_limit_error(path, imported)
                values.append(
                    ImportFact(
                        module,
                        None,
                        bound_name,
                        _source_location(path, imported),
                    )
                )
        else:
            module = f"{'.' * node.level}{node.module or ''}"
            if not _valid_text(module, _MAX_COORDINATE_LENGTH):
                raise _fact_limit_error(path, node)
            for imported in node.names:
                imported_name = imported.name
                bound_name = None if imported_name == "*" else imported.asname or imported_name
                if not _valid_text(imported_name, _MAX_COORDINATE_LENGTH) or (
                    bound_name is not None
                    and not _valid_text(bound_name, _MAX_COORDINATE_LENGTH)
                ):
                    raise _fact_limit_error(path, imported)
                values.append(
                    ImportFact(
                        module,
                        imported_name,
                        bound_name,
                        _source_location(path, imported),
                    )
                )
    return tuple(values)


def _alias_resolution(
    aliases: tuple[AliasBinding, ...],
) -> tuple[dict[str, str], set[str]]:
    candidates: dict[str, set[str]] = {}
    for alias in aliases:
        candidates.setdefault(alias.local_name, set()).add(alias.qualified_name)
    resolved = {
        local_name: next(iter(qualified_names))
        for local_name, qualified_names in candidates.items()
        if len(qualified_names) == 1
    }
    conflicts = {
        local_name
        for local_name, qualified_names in candidates.items()
        if len(qualified_names) > 1
    }
    return resolved, conflicts


def _qualified_call_name(
    node: ast.AST,
    aliases: dict[str, str],
    conflicts: set[str],
    wildcard_present: bool,
) -> str | None:
    attributes: list[str] = []
    owner = node
    while isinstance(owner, ast.Attribute):
        attributes.append(owner.attr)
        owner = owner.value
    if not isinstance(owner, ast.Name):
        return None
    root = owner.id
    if root in conflicts:
        return None
    if root in aliases:
        qualified_name = aliases[root]
    elif wildcard_present:
        return None
    else:
        qualified_name = root
    if attributes:
        qualified_name = ".".join((qualified_name, *reversed(attributes)))
    return qualified_name


def _call_facts(
    tree: ast.AST,
    path: str,
    imports: tuple[ImportFact, ...],
    aliases: tuple[AliasBinding, ...],
) -> tuple[CallFact, ...]:
    resolved_aliases, conflicts = _alias_resolution(aliases)
    wildcard_present = any(value.imported_name == "*" for value in imports)
    values: list[CallFact] = []
    for node in _source_ordered_nodes(tree, ast.Call):
        name = _qualified_call_name(
            node.func,
            resolved_aliases,
            conflicts,
            wildcard_present,
        )
        if name is None:
            target: CallTarget = UnresolvedCallTarget()
        else:
            if not _valid_text(name, _MAX_QUALIFIED_NAME_LENGTH):
                raise _fact_limit_error(path, node)
            target = ResolvedCallTarget(name)
        values.append(CallFact(target, _source_location(path, node)))
    return tuple(values)


def analyze_source(source: str, *, path: str, module: str) -> PythonSourceFacts:
    """Analyze source with the executing Python's stdlib AST grammar."""

    if type(source) is not str or type(path) is not str or type(module) is not str:
        _raise_request_type_error()
    if not _valid_text(path, _MAX_COORDINATE_LENGTH) or not _valid_text(
        module, _MAX_COORDINATE_LENGTH
    ):
        _raise_request_value_error()
    source_bytes = _utf8_bytes(source)
    if source_bytes is None or "\x00" in source:
        _raise_request_value_error()
    if len(source_bytes) > _MAX_SOURCE_BYTES:
        raise _source_limit_error(path)

    syntax_error: tuple[int, int] | None = None
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as error:
        syntax_error = (error.lineno or 0, error.offset or 0)
    if syntax_error is not None:
        line, column = syntax_error
        raise SourceAnalysisError(
            "python source is invalid",
            path=path,
            line=line,
            column=column,
        )

    imports = _import_facts(tree, path)
    aliases = _derived_aliases(imports)
    calls = _call_facts(tree, path, imports, aliases)
    return PythonSourceFacts(path, module, imports, aliases, calls)


__all__ = (
    "AliasBinding",
    "CallFact",
    "CallTarget",
    "ImportFact",
    "PythonSourceFacts",
    "ResolvedCallTarget",
    "SourceAnalysisError",
    "SourceLocation",
    "UnresolvedCallTarget",
    "analyze_source",
)
