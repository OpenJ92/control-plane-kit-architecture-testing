from __future__ import annotations

from base64 import urlsafe_b64encode
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import tomllib
import zipfile


_SCHEMA = "cpk.architecture-testing-release.v1"
_REPOSITORY = "OpenJ92/control-plane-kit-architecture-testing"
_VERSION = "0.1.0"
_TAG = "v0.1.0"
_PYTHON_IMAGE = (
    "python:3.14-slim@sha256:"
    "ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4"
)
_WHEEL_NAME = "control_plane_kit_architecture_testing-0.1.0-py3-none-any.whl"
_SDIST_NAME = "control_plane_kit_architecture_testing-0.1.0.tar.gz"
_SDIST_PREFIX = "control_plane_kit_architecture_testing-0.1.0"
_MAX_REPORT_BYTES = 65_536
_MAX_INT64 = 9_223_372_036_854_775_807
_MIN_ZIP_EPOCH = 315_532_800
_MAX_ZIP_EPOCH = 4_354_819_199
_HEX_40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")

_BUILD_INPUT_ROWS = (
    (
        "build",
        "1.3.0",
        "build-1.3.0-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/cb/8c/"
        "2b30c12155ad8de0cf641d76a8b396a16d2c36bc6d50b621a62b7c4567c1/"
        "build-1.3.0-py3-none-any.whl",
        23_382,
        "7145f0b5061ba90a1500d60bd1b13ca0a8a4cebdd0cc16ed8adf1c0e739f43b4",
    ),
    (
        "packaging",
        "25.0",
        "packaging-25.0-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/20/12/"
        "38679034af332785aac8774540895e234f4d07f7545804097de4b666afd8/"
        "packaging-25.0-py3-none-any.whl",
        66_469,
        "29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484",
    ),
    (
        "pyproject-hooks",
        "1.2.0",
        "pyproject_hooks-1.2.0-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/bd/24/"
        "12818598c362d7f300f18e74db45963dbcb85150324092410c8b49405e42/"
        "pyproject_hooks-1.2.0-py3-none-any.whl",
        10_216,
        "9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913",
    ),
    (
        "setuptools",
        "83.0.0",
        "setuptools-83.0.0-py3-none-any.whl",
        "https://files.pythonhosted.org/packages/5d/40/"
        "e1e72872c6354b306daef1703549e8e83b4d43cfea356311bf722a043752/"
        "setuptools-83.0.0-py3-none-any.whl",
        1_008_090,
        "29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3",
    ),
)

_WHEEL_MEMBERS = (
    "control_plane_kit_architecture_testing/__init__.py",
    "control_plane_kit_architecture_testing/architecture_policy.py",
    "control_plane_kit_architecture_testing/py.typed",
    "control_plane_kit_architecture_testing/python_source.py",
    "control_plane_kit_architecture_testing-0.1.0.dist-info/METADATA",
    "control_plane_kit_architecture_testing-0.1.0.dist-info/WHEEL",
    "control_plane_kit_architecture_testing-0.1.0.dist-info/licenses/LICENSE",
    "control_plane_kit_architecture_testing-0.1.0.dist-info/RECORD",
)
_WHEEL_RECORD = _WHEEL_MEMBERS[-1]
_WHEEL_METADATA = _WHEEL_MEMBERS[4]
_WHEEL_DESCRIPTOR = _WHEEL_MEMBERS[5]

_SDIST_SOURCE_MEMBERS = (
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
_SDIST_GENERATED_MEMBERS = (
    "PKG-INFO",
    "src/control_plane_kit_architecture_testing.egg-info/PKG-INFO",
    "src/control_plane_kit_architecture_testing.egg-info/SOURCES.txt",
    "src/control_plane_kit_architecture_testing.egg-info/dependency_links.txt",
    "src/control_plane_kit_architecture_testing.egg-info/top_level.txt",
)
_SDIST_MEMBERS = _SDIST_SOURCE_MEMBERS + _SDIST_GENERATED_MEMBERS
_SDIST_DIRECTORY_MEMBERS = tuple(
    sorted(
        {
            parent.as_posix()
            for name in _SDIST_MEMBERS
            for parent in PurePosixPath(name).parents
            if parent.as_posix() != "."
        }
    )
)
_SDIST_SOURCES = "src/control_plane_kit_architecture_testing.egg-info/SOURCES.txt"

_WHEEL = (
    b"Wheel-Version: 1.0\n"
    b"Generator: setuptools (83.0.0)\n"
    b"Root-Is-Purelib: true\n"
    b"Tag: py3-none-any\n"
    b"\n"
)
_PROJECT_DOCUMENT = {
    "build-system": {
        "requires": ["setuptools==83.0.0"],
        "build-backend": "setuptools.build_meta",
    },
    "project": {
        "name": "control-plane-kit-architecture-testing",
        "version": "0.1.0",
        "description": (
            "Immutable architecture testing language for Control Plane Kit repositories"
        ),
        "readme": "README.md",
        "requires-python": ">=3.11",
        "license": "MIT",
        "license-files": ["LICENSE"],
        "authors": [{"name": "OpenJ92"}],
        "dependencies": [],
        "urls": {
            "Repository": (
                "https://github.com/OpenJ92/"
                "control-plane-kit-architecture-testing"
            )
        },
    },
    "tool": {
        "setuptools": {
            "packages": {
                "find": {
                    "where": ["src"],
                    "include": ["control_plane_kit_architecture_testing*"],
                }
            },
            "package-data": {
                "control_plane_kit_architecture_testing": ["py.typed"]
            },
        }
    },
}


class ReleaseBuildReportError(ValueError):
    pass


class _ArtifactInvalid(Exception):
    pass


def _plain_text(value: object, *, maximum: int) -> bool:
    if type(value) is not str or not 1 <= len(value) <= maximum:
        return False
    return not any(ord(character) < 32 or 0xD800 <= ord(character) <= 0xDFFF for character in value)


def _artifact_fields_valid(
    filename: object,
    size: object,
    digest: object,
) -> bool:
    return (
        _plain_text(filename, maximum=512)
        and "/" not in filename
        and "\\" not in filename
        and type(size) is int
        and 1 <= size <= _MAX_INT64
        and type(digest) is str
        and _HEX_64.fullmatch(digest) is not None
    )


@dataclass(frozen=True, slots=True)
class BuildInputArtifact:
    name: str
    version: str
    filename: str
    url: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        valid = (
            _plain_text(self.name, maximum=128)
            and _plain_text(self.version, maximum=128)
            and _artifact_fields_valid(self.filename, self.size, self.sha256)
            and _plain_text(self.url, maximum=2_048)
            and self.url.startswith("https://files.pythonhosted.org/")
            and "@" not in self.url.split("/", 3)[2]
            and self.url.endswith("/" + self.filename)
        )
        if not valid:
            raise ValueError("release build artifact is invalid")


@dataclass(frozen=True, slots=True)
class OutputArtifact:
    filename: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        if not _artifact_fields_valid(self.filename, self.size, self.sha256):
            raise ValueError("release build artifact is invalid")


def _expected_inputs() -> tuple[BuildInputArtifact, ...]:
    return tuple(BuildInputArtifact(*row) for row in _BUILD_INPUT_ROWS)


def _valid_report(report: object) -> bool:
    if type(report) is not ReleaseBuildReport:
        return False
    try:
        values = (
            report.schema,
            report.repository,
            report.commit,
            report.tree,
            report.intended_tag,
            report.version,
            report.python_image,
            report.python_version,
            report.pip_version,
        )
        source_date_epoch = report.source_date_epoch
        build_inputs = report.build_inputs
        artifacts = report.artifacts
    except AttributeError:
        return False
    if any(type(value) is not str for value in values):
        return False
    if (
        report.schema != _SCHEMA
        or report.repository != _REPOSITORY
        or _HEX_40.fullmatch(report.commit) is None
        or _HEX_40.fullmatch(report.tree) is None
        or report.intended_tag != _TAG
        or report.version != _VERSION
        or type(source_date_epoch) is not int
        or not _MIN_ZIP_EPOCH <= source_date_epoch <= _MAX_ZIP_EPOCH
        or report.python_image != _PYTHON_IMAGE
        or not _plain_text(report.python_version, maximum=64)
        or not _plain_text(report.pip_version, maximum=64)
        or type(build_inputs) is not tuple
        or type(artifacts) is not tuple
    ):
        return False
    if any(type(value) is not BuildInputArtifact for value in build_inputs):
        return False
    if any(type(value) is not OutputArtifact for value in artifacts):
        return False
    if any(not _valid_build_input(value) for value in build_inputs):
        return False
    if any(not _valid_output(value) for value in artifacts):
        return False
    if build_inputs != _expected_inputs():
        return False
    return tuple(value.filename for value in artifacts) == (
        _WHEEL_NAME,
        _SDIST_NAME,
    )


def _valid_build_input(value: BuildInputArtifact) -> bool:
    try:
        rebuilt = BuildInputArtifact(
            value.name,
            value.version,
            value.filename,
            value.url,
            value.size,
            value.sha256,
        )
    except (AttributeError, TypeError, ValueError):
        return False
    return rebuilt == value


def _valid_output(value: OutputArtifact) -> bool:
    try:
        rebuilt = OutputArtifact(value.filename, value.size, value.sha256)
    except (AttributeError, TypeError, ValueError):
        return False
    return rebuilt == value


@dataclass(frozen=True, slots=True)
class ReleaseBuildReport:
    schema: str
    repository: str
    commit: str
    tree: str
    intended_tag: str
    version: str
    source_date_epoch: int
    python_image: str
    python_version: str
    pip_version: str
    build_inputs: tuple[BuildInputArtifact, ...]
    artifacts: tuple[OutputArtifact, ...]

    def __post_init__(self) -> None:
        if not _valid_report(self):
            raise ReleaseBuildReportError("release build report is invalid")


def _artifact_document(value: BuildInputArtifact | OutputArtifact) -> dict[str, object]:
    if type(value) is BuildInputArtifact:
        return {
            "name": value.name,
            "version": value.version,
            "filename": value.filename,
            "url": value.url,
            "size": value.size,
            "sha256": value.sha256,
        }
    return {"filename": value.filename, "size": value.size, "sha256": value.sha256}


def _report_document(report: ReleaseBuildReport) -> dict[str, object]:
    return {
        "schema": report.schema,
        "repository": report.repository,
        "commit": report.commit,
        "tree": report.tree,
        "intended_tag": report.intended_tag,
        "version": report.version,
        "source_date_epoch": report.source_date_epoch,
        "python_image": report.python_image,
        "python_version": report.python_version,
        "pip_version": report.pip_version,
        "build_inputs": [_artifact_document(value) for value in report.build_inputs],
        "artifacts": [_artifact_document(value) for value in report.artifacts],
    }


def release_report_bytes(report: ReleaseBuildReport) -> bytes:
    if not _valid_report(report):
        raise ReleaseBuildReportError("release report document is invalid")
    encoded = (
        json.dumps(
            _report_document(report),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        + b"\n"
    )
    if len(encoded) > _MAX_REPORT_BYTES:
        raise ReleaseBuildReportError("release report document is invalid")
    return encoded


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _ArtifactInvalid
        result[key] = value
    return result


def _exact_keys(value: object, keys: tuple[str, ...]) -> bool:
    return type(value) is dict and tuple(sorted(value)) == tuple(sorted(keys))


def parse_release_report(encoded: bytes) -> ReleaseBuildReport:
    report: ReleaseBuildReport | None = None
    invalid = type(encoded) is not bytes or not encoded.endswith(b"\n") or encoded.endswith(b"\n\n")
    if not invalid and len(encoded) <= _MAX_REPORT_BYTES and b"\r" not in encoded:
        try:
            document = json.loads(encoded, object_pairs_hook=_unique_object)
            if not _exact_keys(
                document,
                (
                    "schema",
                    "repository",
                    "commit",
                    "tree",
                    "intended_tag",
                    "version",
                    "source_date_epoch",
                    "python_image",
                    "python_version",
                    "pip_version",
                    "build_inputs",
                    "artifacts",
                ),
            ):
                raise _ArtifactInvalid
            input_keys = ("name", "version", "filename", "url", "size", "sha256")
            output_keys = ("filename", "size", "sha256")
            if type(document["build_inputs"]) is not list or type(document["artifacts"]) is not list:
                raise _ArtifactInvalid
            if any(not _exact_keys(value, input_keys) for value in document["build_inputs"]):
                raise _ArtifactInvalid
            if any(not _exact_keys(value, output_keys) for value in document["artifacts"]):
                raise _ArtifactInvalid
            inputs = tuple(BuildInputArtifact(**value) for value in document["build_inputs"])
            outputs = tuple(OutputArtifact(**value) for value in document["artifacts"])
            report = ReleaseBuildReport(
                document["schema"],
                document["repository"],
                document["commit"],
                document["tree"],
                document["intended_tag"],
                document["version"],
                document["source_date_epoch"],
                document["python_image"],
                document["python_version"],
                document["pip_version"],
                inputs,
                outputs,
            )
            invalid = release_report_bytes(report) != encoded
        except (
            _ArtifactInvalid,
            UnicodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):
            invalid = True
    else:
        invalid = True
    if invalid or report is None:
        raise ReleaseBuildReportError("release report document is invalid")
    return report


def _require(condition: bool) -> None:
    if not condition:
        raise _ArtifactInvalid


def _zip_datetime(source_date_epoch: int) -> tuple[int, int, int, int, int, int]:
    instant = datetime.fromtimestamp(source_date_epoch, timezone.utc)
    return (
        instant.year,
        instant.month,
        instant.day,
        instant.hour,
        instant.minute,
        instant.second - instant.second % 2,
    )


def _read_zip_member(
    archive: zipfile.ZipFile,
    name: str,
    expected_datetime: tuple[int, int, int, int, int, int],
) -> bytes:
    info = archive.getinfo(name)
    mode = info.external_attr >> 16
    _require(stat.S_ISREG(mode) and stat.S_IMODE(mode) == 0o644)
    _require(info.date_time == expected_datetime)
    return archive.read(info)


def _verify_wheel(path: Path, source_date_epoch: int) -> bytes:
    expected_datetime = _zip_datetime(source_date_epoch)
    with zipfile.ZipFile(path) as archive:
        names = tuple(archive.namelist())
        _require(names == _WHEEL_MEMBERS)
        contents = {
            name: _read_zip_member(archive, name, expected_datetime)
            for name in names
        }
    _require(contents["control_plane_kit_architecture_testing/py.typed"] == b"")
    rows = tuple(csv.reader(io.StringIO(contents[_WHEEL_RECORD].decode("utf-8"))))
    _require(len(rows) == len(names))
    _require(all(type(row) is list and len(row) == 3 for row in rows))
    _require(tuple(row[0] for row in rows) == names)
    for name, digest, size in rows[:-1]:
        content = contents[name]
        encoded = urlsafe_b64encode(sha256(content).digest()).rstrip(b"=").decode("ascii")
        _require(digest == "sha256=" + encoded and size == str(len(content)))
    _require(rows[-1] == [_WHEEL_RECORD, "", ""])
    _require(contents[_WHEEL_DESCRIPTOR] == _WHEEL)
    return contents[_WHEEL_METADATA]


def _verify_sdist(path: Path, source_date_epoch: int) -> dict[str, bytes]:
    with tarfile.open(path, mode="r:gz") as archive:
        members = archive.getmembers()
        _require(
            len(members)
            == len(_SDIST_MEMBERS) + len(_SDIST_DIRECTORY_MEMBERS) + 1
        )
        root = members[0]
        _require(
            root.name == _SDIST_PREFIX
            and root.isdir()
            and root.mode == 0o755
            and root.mtime == source_date_epoch
        )
        nested = members[1:]
        _require(
            all(member.name.startswith(_SDIST_PREFIX + "/") for member in nested)
        )
        directories = tuple(member for member in nested if member.isdir())
        files = tuple(member for member in nested if member.isfile())
        _require(len(directories) + len(files) == len(nested))
        directory_names = tuple(
            member.name.removeprefix(_SDIST_PREFIX + "/")
            for member in directories
        )
        _require(
            len(set(directory_names)) == len(directory_names)
            and set(directory_names) == set(_SDIST_DIRECTORY_MEMBERS)
        )
        for member in directories:
            _require(member.mode == 0o755 and member.mtime == source_date_epoch)
        relative_names = tuple(
            member.name.removeprefix(_SDIST_PREFIX + "/") for member in files
        )
        _require(relative_names == _SDIST_MEMBERS)
        contents: dict[str, bytes] = {}
        for relative, member in zip(relative_names, files, strict=True):
            _require(member.name == _SDIST_PREFIX + "/" + relative)
            _require(member.mode == (0o755 if relative == "test.sh" else 0o644))
            _require(member.mtime == source_date_epoch)
            extracted = archive.extractfile(member)
            _require(extracted is not None)
            contents[relative] = extracted.read()
    _require(contents["src/control_plane_kit_architecture_testing.egg-info/dependency_links.txt"] == b"\n")
    _require(
        contents["src/control_plane_kit_architecture_testing.egg-info/top_level.txt"]
        == b"control_plane_kit_architecture_testing\n"
    )
    _require(
        contents[_SDIST_SOURCES]
        == ("\n".join(_SDIST_SOURCE_MEMBERS) + "\n").encode("utf-8")
    )
    return contents


def _metadata_values(message: object, name: str) -> tuple[str, ...]:
    values = message.get_all(name)
    return () if values is None else tuple(str(value) for value in values)


def _verify_project_metadata(
    wheel_metadata: bytes,
    sdist_contents: dict[str, bytes],
) -> None:
    package_metadata = sdist_contents["PKG-INFO"]
    egg_metadata = sdist_contents[
        "src/control_plane_kit_architecture_testing.egg-info/PKG-INFO"
    ]
    _require(wheel_metadata == package_metadata == egg_metadata)
    project_document = tomllib.loads(
        sdist_contents["pyproject.toml"].decode("utf-8")
    )
    _require(project_document == _PROJECT_DOCUMENT)
    message = BytesParser(policy=policy.default).parsebytes(wheel_metadata)
    _require(not message.defects)
    project = _PROJECT_DOCUMENT["project"]
    expected = {
        "Metadata-Version": ("2.4",),
        "Name": (project["name"],),
        "Version": (project["version"],),
        "Summary": (project["description"],),
        "Author": (project["authors"][0]["name"],),
        "License-Expression": (project["license"],),
        "Project-URL": (f"Repository, {project['urls']['Repository']}",),
        "Requires-Python": (project["requires-python"],),
        "Description-Content-Type": ("text/markdown",),
        "License-File": (project["license-files"][0],),
    }
    _require(
        all(_metadata_values(message, name) == values for name, values in expected.items())
    )
    _require(_metadata_values(message, "Requires-Dist") == ())
    _require(_metadata_values(message, "Provides-Extra") == ())
    payload = message.get_payload()
    _require(type(payload) is str)
    _require(payload.encode("utf-8") == sdist_contents["README.md"])


def _verify_artifacts(report: ReleaseBuildReport, artifact_root: Path) -> None:
    _require(artifact_root.is_dir() and not artifact_root.is_symlink())
    paths = tuple(sorted(artifact_root.iterdir(), key=lambda value: value.name))
    _require(tuple(path.name for path in paths) == tuple(value.filename for value in report.artifacts))
    for path, expected in zip(paths, report.artifacts, strict=True):
        _require(path.is_file() and not path.is_symlink())
        content = path.read_bytes()
        _require(len(content) == expected.size)
        _require(sha256(content).hexdigest() == expected.sha256)
    wheel_metadata = _verify_wheel(
        artifact_root / _WHEEL_NAME,
        report.source_date_epoch,
    )
    sdist_contents = _verify_sdist(
        artifact_root / _SDIST_NAME,
        report.source_date_epoch,
    )
    _verify_project_metadata(wheel_metadata, sdist_contents)


def verify_release_report(report: ReleaseBuildReport, artifact_root: Path) -> None:
    invalid = not _valid_report(report) or type(artifact_root) is not type(Path())
    if not invalid:
        try:
            _verify_artifacts(report, artifact_root)
        except (
            _ArtifactInvalid,
            csv.Error,
            IndexError,
            KeyError,
            OSError,
            OverflowError,
            tarfile.TarError,
            tomllib.TOMLDecodeError,
            UnicodeError,
            zipfile.BadZipFile,
        ):
            invalid = True
    if invalid:
        raise ReleaseBuildReportError("release artifact set is invalid")


__all__ = (
    "BuildInputArtifact",
    "OutputArtifact",
    "ReleaseBuildReport",
    "ReleaseBuildReportError",
    "parse_release_report",
    "release_report_bytes",
    "verify_release_report",
)
