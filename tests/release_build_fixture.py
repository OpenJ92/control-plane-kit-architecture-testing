from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import io
import json
from pathlib import Path
import tarfile
from types import ModuleType
from typing import Any, Callable
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "test_support.release_report"
PACKAGE_NAME = "control_plane_kit_architecture_testing"
VERSION = "0.1.0"
WHEEL_NAME = f"{PACKAGE_NAME}-{VERSION}-py3-none-any.whl"
SDIST_NAME = f"{PACKAGE_NAME}-{VERSION}.tar.gz"
SDIST_PREFIX = f"{PACKAGE_NAME}-{VERSION}"
SOURCE_DATE_EPOCH = 1_800_000_001


def source_metadata() -> bytes:
    return (
        b"Metadata-Version: 2.4\n"
        b"Name: control-plane-kit-architecture-testing\n"
        b"Version: 0.1.0\n"
        b"Summary: Immutable architecture testing language for Control Plane Kit repositories\n"
        b"Author: OpenJ92\n"
        b"License-Expression: MIT\n"
        b"Project-URL: Repository, https://github.com/OpenJ92/control-plane-kit-architecture-testing\n"
        b"Requires-Python: >=3.11\n"
        b"Description-Content-Type: text/markdown\n"
        b"License-File: LICENSE\n"
        b"\n"
        + (ROOT / "README.md").read_bytes()
    )


def zip_datetime(source_date_epoch: int) -> tuple[int, int, int, int, int, int]:
    instant = datetime.fromtimestamp(source_date_epoch, timezone.utc)
    return (
        instant.year,
        instant.month,
        instant.day,
        instant.hour,
        instant.minute,
        instant.second - instant.second % 2,
    )

BUILD_INPUT_ROWS = (
    (
        "build",
        "1.3.0",
        "build-1.3.0-py3-none-any.whl",
        (
            "https://files.pythonhosted.org/packages/cb/8c/"
            "2b30c12155ad8de0cf641d76a8b396a16d2c36bc6d50b621a62b7c4567c1/"
            "build-1.3.0-py3-none-any.whl"
        ),
        23_382,
        "7145f0b5061ba90a1500d60bd1b13ca0a8a4cebdd0cc16ed8adf1c0e739f43b4",
    ),
    (
        "packaging",
        "25.0",
        "packaging-25.0-py3-none-any.whl",
        (
            "https://files.pythonhosted.org/packages/20/12/"
            "38679034af332785aac8774540895e234f4d07f7545804097de4b666afd8/"
            "packaging-25.0-py3-none-any.whl"
        ),
        66_469,
        "29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484",
    ),
    (
        "pyproject-hooks",
        "1.2.0",
        "pyproject_hooks-1.2.0-py3-none-any.whl",
        (
            "https://files.pythonhosted.org/packages/bd/24/"
            "12818598c362d7f300f18e74db45963dbcb85150324092410c8b49405e42/"
            "pyproject_hooks-1.2.0-py3-none-any.whl"
        ),
        10_216,
        "9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913",
    ),
    (
        "setuptools",
        "83.0.0",
        "setuptools-83.0.0-py3-none-any.whl",
        (
            "https://files.pythonhosted.org/packages/5d/40/"
            "e1e72872c6354b306daef1703549e8e83b4d43cfea356311bf722a043752/"
            "setuptools-83.0.0-py3-none-any.whl"
        ),
        1_008_090,
        "29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3",
    ),
)

_WHEEL_MEMBERS_WITHOUT_RECORD = {
    f"{PACKAGE_NAME}/__init__.py": b'__version__ = "0.1.0"\n',
    f"{PACKAGE_NAME}/architecture_policy.py": b"# policy language\n",
    f"{PACKAGE_NAME}/py.typed": b"",
    f"{PACKAGE_NAME}/python_source.py": b"# source facts\n",
    f"{PACKAGE_NAME}-{VERSION}.dist-info/METADATA": source_metadata(),
    f"{PACKAGE_NAME}-{VERSION}.dist-info/WHEEL": (
        b"Wheel-Version: 1.0\n"
        b"Generator: setuptools (83.0.0)\n"
        b"Root-Is-Purelib: true\n"
        b"Tag: py3-none-any\n"
        b"\n"
    ),
    f"{PACKAGE_NAME}-{VERSION}.dist-info/licenses/LICENSE": b"MIT License\n",
}


def _wheel_record(members: dict[str, bytes]) -> bytes:
    rows = []
    for name, content in members.items():
        digest = urlsafe_b64encode(sha256(content).digest()).rstrip(b"=").decode("ascii")
        rows.append(f"{name},sha256={digest},{len(content)}\n")
    rows.append(f"{PACKAGE_NAME}-{VERSION}.dist-info/RECORD,,\n")
    return "".join(rows).encode("utf-8")


WHEEL_RECORD_NAME = f"{PACKAGE_NAME}-{VERSION}.dist-info/RECORD"


def coherent_wheel_members(members: dict[str, bytes]) -> dict[str, bytes]:
    without_record = {
        name: content for name, content in members.items() if name != WHEEL_RECORD_NAME
    }
    return {**without_record, WHEEL_RECORD_NAME: _wheel_record(without_record)}


WHEEL_MEMBER_CONTENTS = coherent_wheel_members(_WHEEL_MEMBERS_WITHOUT_RECORD)

SDIST_SOURCE_MEMBERS = (
    "AGENTS.md",
    "GIT-FLOW.md",
    "LICENSE",
    "MANIFEST.in",
    "README.md",
    "pyproject.toml",
    "test.sh",
    "src/control_plane_kit_architecture_testing/__init__.py",
    "src/control_plane_kit_architecture_testing/architecture_policy.py",
    "src/control_plane_kit_architecture_testing/py.typed",
    "src/control_plane_kit_architecture_testing/python_source.py",
    "test_support/build-inputs.json",
    "test_support/inspect_artifacts.py",
    "test_support/installed_package.py",
    "test_support/release_report.py",
    "tests/policy_fixture.py",
    "tests/release_build_fixture.py",
    "tests/source_fact_fixture.py",
    "tests/test_architecture_policy_boundaries.py",
    "tests/test_architecture_policy_evaluation.py",
    "tests/test_architecture_policy_values.py",
    "tests/test_package.py",
    "tests/test_python_source_analysis.py",
    "tests/test_python_source_boundaries.py",
    "tests/test_python_source_values.py",
    "tests/test_release_artifacts.py",
    "tests/test_release_build_contract.py",
    "tests/test_release_report_codec.py",
    "tests/test_release_report_values.py",
)

SDIST_GENERATED_MEMBERS = (
    "PKG-INFO",
    "src/control_plane_kit_architecture_testing.egg-info/PKG-INFO",
    "src/control_plane_kit_architecture_testing.egg-info/SOURCES.txt",
    "src/control_plane_kit_architecture_testing.egg-info/dependency_links.txt",
    "src/control_plane_kit_architecture_testing.egg-info/top_level.txt",
)
SDIST_DIRECTORY_MEMBERS = tuple(
    sorted(
        {
            parent.as_posix()
            for name in SDIST_SOURCE_MEMBERS + SDIST_GENERATED_MEMBERS
            for parent in Path(name).parents
            if parent.as_posix() != "."
        }
    )
)
SDIST_SOURCES_NAME = "src/control_plane_kit_architecture_testing.egg-info/SOURCES.txt"


def coherent_sdist_members(members: dict[str, bytes]) -> dict[str, bytes]:
    selected = dict(members)
    selected[SDIST_SOURCES_NAME] = (
        "\n".join(
            name for name in selected if name not in SDIST_GENERATED_MEMBERS
        ).encode("utf-8")
        + b"\n"
    )
    return selected

SDIST_MEMBER_CONTENTS = {
    **{name: f"fixture:{name}\n".encode("utf-8") for name in SDIST_SOURCE_MEMBERS},
    **{name: f"generated:{name}\n".encode("utf-8") for name in SDIST_GENERATED_MEMBERS},
}
SDIST_MEMBER_CONTENTS.update(
    {
        "LICENSE": (ROOT / "LICENSE").read_bytes(),
        "README.md": (ROOT / "README.md").read_bytes(),
        "pyproject.toml": (ROOT / "pyproject.toml").read_bytes(),
        "src/control_plane_kit_architecture_testing/__init__.py": (
            b'__version__ = "0.1.0"\n'
        ),
        "PKG-INFO": source_metadata(),
        "src/control_plane_kit_architecture_testing.egg-info/PKG-INFO": source_metadata(),
        SDIST_SOURCES_NAME: b"",
        "src/control_plane_kit_architecture_testing.egg-info/dependency_links.txt": b"\n",
        "src/control_plane_kit_architecture_testing.egg-info/top_level.txt": (
            b"control_plane_kit_architecture_testing\n"
        ),
    }
)
SDIST_MEMBER_CONTENTS = coherent_sdist_members(SDIST_MEMBER_CONTENTS)


def closure_mutations() -> tuple[
    tuple[str, dict[str, bytes], dict[str, bytes]], ...
]:
    missing_wheel = dict(WHEEL_MEMBER_CONTENTS)
    missing_wheel.pop(f"{PACKAGE_NAME}/py.typed")

    extra_wheel = dict(WHEEL_MEMBER_CONTENTS)
    extra_wheel["tests/leak.py"] = b""

    dependency_wheel = dict(WHEEL_MEMBER_CONTENTS)
    dependency_wheel[f"{PACKAGE_NAME}-{VERSION}.dist-info/METADATA"] += (
        b"Requires-Dist: candidate-secret\n"
    )

    report_wheel = dict(WHEEL_MEMBER_CONTENTS)
    report_wheel["release-report.json"] = b"{}\n"

    report_sdist = dict(SDIST_MEMBER_CONTENTS)
    report_sdist["release-report.json"] = b"{}\n"

    missing_sdist = dict(SDIST_MEMBER_CONTENTS)
    missing_sdist.pop("tests/policy_fixture.py")

    extra_sdist = dict(SDIST_MEMBER_CONTENTS)
    extra_sdist[".git/config"] = b"candidate-secret"

    return (
        ("wheel missing", missing_wheel, SDIST_MEMBER_CONTENTS),
        ("wheel extra", extra_wheel, SDIST_MEMBER_CONTENTS),
        ("runtime dependency", dependency_wheel, SDIST_MEMBER_CONTENTS),
        ("embedded report", report_wheel, SDIST_MEMBER_CONTENTS),
        ("sdist embedded report", WHEEL_MEMBER_CONTENTS, report_sdist),
        ("sdist missing fixture", WHEEL_MEMBER_CONTENTS, missing_sdist),
        ("sdist git state", WHEEL_MEMBER_CONTENTS, extra_sdist),
    )


def load_release_language() -> ModuleType | None:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as error:
        if error.name != MODULE_NAME:
            raise
        return None


RELEASE = load_release_language()


def require_release(case: unittest.TestCase) -> Any:
    case.assertIsNotNone(RELEASE, "release report language is not implemented")
    return RELEASE


def captured_error(
    case: unittest.TestCase,
    expected: type[BaseException] | tuple[type[BaseException], ...],
    callback: Callable[[], object],
) -> BaseException:
    with case.assertRaises(expected) as raised:
        callback()
    error = raised.exception
    case.assertIsNone(error.__cause__)
    case.assertIsNone(error.__context__)
    return error


def forge(exact_type: type, **fields: object) -> object:
    value = object.__new__(exact_type)
    for name, field_value in fields.items():
        object.__setattr__(value, name, field_value)
    return value


class HostileStr(str):
    def encode(self, *args: object, **kwargs: object) -> bytes:
        raise RuntimeError("hostile string encode dispatched")

    def __len__(self) -> int:
        raise RuntimeError("hostile string length dispatched")


class HostileInt(int):
    def __index__(self) -> int:
        raise RuntimeError("hostile integer index dispatched")


class HostileTuple(tuple):
    def __iter__(self):
        raise RuntimeError("hostile tuple iteration dispatched")


def build_inputs(language: Any) -> tuple[object, ...]:
    return tuple(language.BuildInputArtifact(*row) for row in BUILD_INPUT_ROWS)


def output_artifact(language: Any, path: Path) -> object:
    content = path.read_bytes()
    return language.OutputArtifact(path.name, len(content), sha256(content).hexdigest())


def release_report(
    language: Any,
    artifact_root: Path | None = None,
    *,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> object:
    if artifact_root is None:
        artifacts = (
            language.OutputArtifact(WHEEL_NAME, 101, "1" * 64),
            language.OutputArtifact(SDIST_NAME, 202, "2" * 64),
        )
    else:
        artifacts = (
            output_artifact(language, artifact_root / SDIST_NAME),
            output_artifact(language, artifact_root / WHEEL_NAME),
        )
        artifacts = tuple(sorted(artifacts, key=lambda item: item.filename))
    return language.ReleaseBuildReport(
        "cpk.architecture-testing-release.v1",
        "OpenJ92/control-plane-kit-architecture-testing",
        "a" * 40,
        "b" * 40,
        "v0.1.0",
        VERSION,
        source_date_epoch,
        (
            "python:3.14-slim@sha256:"
            "ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
        ),
        "3.14.0",
        "25.2",
        build_inputs(language),
        artifacts,
    )


def write_wheel(
    root: Path,
    *,
    members: dict[str, bytes] | None = None,
    mode: int = 0o644,
    member_modes: dict[str, int] | None = None,
    record_override: bytes | None = None,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> Path:
    path = root / WHEEL_NAME
    selected = coherent_wheel_members(
        WHEEL_MEMBER_CONTENTS if members is None else members
    )
    selected_modes = {} if member_modes is None else member_modes
    if record_override is not None:
        selected[WHEEL_RECORD_NAME] = record_override
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in selected.items():
            info = zipfile.ZipInfo(name, date_time=zip_datetime(source_date_epoch))
            info.create_system = 3
            info.external_attr = (
                selected_modes.get(name, stat_mode(mode)) & 0xFFFF
            ) << 16
            archive.writestr(info, content)
    return path


def write_sdist(
    root: Path,
    *,
    members: dict[str, bytes] | None = None,
    mode: int | None = None,
    member_types: dict[str, bytes] | None = None,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> Path:
    path = root / SDIST_NAME
    selected = coherent_sdist_members(
        SDIST_MEMBER_CONTENTS if members is None else members
    )
    selected_types = {} if member_types is None else member_types
    with path.open("wb") as destination:
        with tarfile.open(fileobj=destination, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
            directory = tarfile.TarInfo(SDIST_PREFIX)
            directory.type = tarfile.DIRTYPE
            directory.mode = 0o755
            directory.mtime = source_date_epoch
            archive.addfile(directory)
            for name in SDIST_DIRECTORY_MEMBERS:
                directory = tarfile.TarInfo(f"{SDIST_PREFIX}/{name}")
                directory.type = tarfile.DIRTYPE
                directory.mode = 0o755
                directory.mtime = source_date_epoch
                archive.addfile(directory)
            for name, content in selected.items():
                info = tarfile.TarInfo(f"{SDIST_PREFIX}/{name}")
                info.mode = (
                    mode
                    if mode is not None
                    else (0o755 if name == "test.sh" else 0o644)
                )
                info.mtime = source_date_epoch
                info.type = selected_types.get(name, tarfile.REGTYPE)
                if info.type == tarfile.REGTYPE:
                    info.size = len(content)
                    archive.addfile(info, io.BytesIO(content))
                else:
                    info.size = 0
                    info.linkname = content.decode("utf-8")
                    archive.addfile(info)
    return path


def write_artifacts(root: Path) -> tuple[Path, Path]:
    return write_wheel(root), write_sdist(root)


def stat_mode(mode: int) -> int:
    return 0o100000 | mode


def lock_document() -> bytes:
    rows = [
        {
            "filename": filename,
            "name": name,
            "sha256": digest,
            "size": size,
            "url": url,
            "version": version,
        }
        for name, version, filename, url, size, digest in BUILD_INPUT_ROWS
    ]
    return (
        json.dumps(
            {"artifacts": rows, "schema": "cpk.architecture-testing-build-inputs.v1"},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        + b"\n"
    )
