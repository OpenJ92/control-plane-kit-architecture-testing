"""Test-only architecture language for Control Plane Kit repositories."""

from control_plane_kit_architecture_testing.python_source import (
    AliasBinding,
    CallFact,
    CallTarget,
    ImportFact,
    PythonSourceFacts,
    ResolvedCallTarget,
    SourceAnalysisError,
    SourceLocation,
    UnresolvedCallTarget,
    analyze_source,
)

__version__ = "0.1.0"

__all__ = (
    "__version__",
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
