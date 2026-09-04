"""Test-only architecture language for Control Plane Kit repositories."""

from control_plane_kit_architecture_testing.architecture_policy import (
    ArchitecturePolicy,
    ExactCallSurfacePolicy,
    ExactImportSurfacePolicy,
    ImportSurfaceEntry,
    PolicyEvaluationError,
    PolicyFinding,
    PolicyId,
    RuleId,
    evaluate_policies,
    evaluate_policy,
)
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
    "ArchitecturePolicy",
    "CallFact",
    "CallTarget",
    "ExactCallSurfacePolicy",
    "ExactImportSurfacePolicy",
    "ImportFact",
    "ImportSurfaceEntry",
    "PolicyEvaluationError",
    "PolicyFinding",
    "PolicyId",
    "PythonSourceFacts",
    "ResolvedCallTarget",
    "RuleId",
    "SourceAnalysisError",
    "SourceLocation",
    "UnresolvedCallTarget",
    "analyze_source",
    "evaluate_policies",
    "evaluate_policy",
)
