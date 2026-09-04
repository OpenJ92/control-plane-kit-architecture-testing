from __future__ import annotations

from pathlib import Path
import sys
import tarfile
import zipfile


dist = Path(sys.argv[1])
wheels = tuple(dist.glob("*.whl"))
source_distributions = tuple(dist.glob("*.tar.gz"))

if len(wheels) != 1:
    raise SystemExit("package build must produce exactly one wheel")
if len(source_distributions) != 1:
    raise SystemExit("package build must produce exactly one source distribution")
if wheels[0].name != "control_plane_kit_architecture_testing-0.1.0-py3-none-any.whl":
    raise SystemExit("unexpected wheel identity")
if source_distributions[0].name != "control_plane_kit_architecture_testing-0.1.0.tar.gz":
    raise SystemExit("unexpected source distribution identity")

with zipfile.ZipFile(wheels[0]) as archive:
    wheel_members = set(archive.namelist())
if "control_plane_kit_architecture_testing/__init__.py" not in wheel_members:
    raise SystemExit("wheel omits package root")
if "control_plane_kit_architecture_testing/py.typed" not in wheel_members:
    raise SystemExit("wheel omits typing marker")

with tarfile.open(source_distributions[0], mode="r:gz") as archive:
    source_members = set(archive.getnames())
prefix = "control_plane_kit_architecture_testing-0.1.0"
if f"{prefix}/src/control_plane_kit_architecture_testing/__init__.py" not in source_members:
    raise SystemExit("source distribution omits package root")
if f"{prefix}/tests/test_package.py" not in source_members:
    raise SystemExit("source distribution omits package tests")

print("control-plane-kit-architecture-testing artifacts ok")
