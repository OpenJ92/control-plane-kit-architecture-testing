from __future__ import annotations

import importlib.metadata
from pathlib import Path

import control_plane_kit_architecture_testing as package


PACKAGE_ROOT = Path(package.__file__).resolve().parent

if package.__version__ != "0.1.0":
    raise SystemExit("unexpected installed package version")
if package.__all__ != ("__version__",):
    raise SystemExit("unexpected installed package root exports")
if importlib.metadata.version("control-plane-kit-architecture-testing") != "0.1.0":
    raise SystemExit("unexpected installed distribution version")
if importlib.metadata.requires("control-plane-kit-architecture-testing") not in (None, []):
    raise SystemExit("installed distribution must have no runtime dependencies")
if "/tmp/package" in PACKAGE_ROOT.as_posix():
    raise SystemExit("outside-source smoke imported the checkout")

print("control-plane-kit-architecture-testing installed import ok")
