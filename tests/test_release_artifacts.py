from __future__ import annotations

from base64 import urlsafe_b64encode
import csv
from dataclasses import replace
from hashlib import sha256
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from release_build_fixture import (
    SDIST_GENERATED_MEMBERS,
    SDIST_MEMBER_CONTENTS,
    SDIST_SOURCES_NAME,
    WHEEL_MEMBER_CONTENTS,
    WHEEL_RECORD_NAME,
    captured_error,
    closure_mutations,
    release_report,
    require_release,
    write_artifacts,
    write_sdist,
    write_wheel,
)


class ReleaseArtifactVerifierTests(unittest.TestCase):
    def write_nonregular_wheel(self, root: Path) -> Path:
        wheel_members = dict(WHEEL_MEMBER_CONTENTS)
        wheel_members["control_plane_kit_architecture_testing/py.typed"] = (
            b"/tmp/external"
        )
        return write_wheel(
            root,
            members=wheel_members,
            member_modes={
                "control_plane_kit_architecture_testing/py.typed": 0o120777
            },
        )

    def write_nonregular_sdist(self, root: Path) -> Path:
        sdist_members = dict(SDIST_MEMBER_CONTENTS)
        sdist_members["README.md"] = b"../outside"
        return write_sdist(
            root,
            members=sdist_members,
            member_types={"README.md": tarfile.SYMTYPE},
        )

    def assert_wheel_record_is_consistent(self, path: Path) -> None:
        with zipfile.ZipFile(path) as archive:
            names = tuple(archive.namelist())
            rows = tuple(
                csv.reader(
                    io.StringIO(archive.read(WHEEL_RECORD_NAME).decode("utf-8"))
                )
            )
            self.assertEqual(tuple(row[0] for row in rows), names)
            for name, digest, size in rows[:-1]:
                content = archive.read(name)
                expected_digest = urlsafe_b64encode(sha256(content).digest()).rstrip(b"=")
                self.assertEqual(digest, f"sha256={expected_digest.decode('ascii')}")
                self.assertEqual(size, str(len(content)))
            self.assertEqual(rows[-1], [WHEEL_RECORD_NAME, "", ""])

    def assert_sdist_sources_are_consistent(self, path: Path) -> None:
        with tarfile.open(path, mode="r:gz") as archive:
            members = tuple(member for member in archive.getmembers() if not member.isdir())
            by_relative = {
                member.name.split("/", 1)[1]: member for member in members
            }
            manifest = archive.extractfile(by_relative[SDIST_SOURCES_NAME])
            self.assertIsNotNone(manifest)
            listed = tuple(manifest.read().decode("utf-8").splitlines())
            self.assertEqual(
                listed,
                tuple(
                    name for name in by_relative if name not in SDIST_GENERATED_MEMBERS
                ),
            )

    def verify_fixture(self, release, root: Path) -> object:
        report = release_report(release, root)
        self.assertIsNone(release.verify_release_report(report, root))
        return report

    def test_synthetic_archive_fixtures_are_complete_regular_and_self_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel, sdist = write_artifacts(root)

            with zipfile.ZipFile(wheel) as archive:
                self.assertEqual(tuple(archive.namelist()), tuple(WHEEL_MEMBER_CONTENTS))
                for name, expected in WHEEL_MEMBER_CONTENTS.items():
                    with self.subTest(archive="wheel", name=name):
                        info = archive.getinfo(name)
                        self.assertEqual(archive.read(name), expected)
                        self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                        self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))

            with tarfile.open(sdist, mode="r:gz") as archive:
                members = archive.getmembers()
                self.assertTrue(members[0].isdir())
                files = tuple(member for member in members if member.isfile())
                self.assertEqual(
                    tuple(member.name for member in files),
                    tuple(
                        f"control_plane_kit_architecture_testing-0.1.0/{name}"
                        for name in SDIST_MEMBER_CONTENTS
                    ),
                )
                for member in files:
                    relative = member.name.split("/", 1)[1]
                    with self.subTest(archive="sdist", name=relative):
                        extracted = archive.extractfile(member)
                        self.assertIsNotNone(extracted)
                        self.assertEqual(extracted.read(), SDIST_MEMBER_CONTENTS[relative])
                        self.assertEqual(
                            member.mode,
                            0o755 if relative == "test.sh" else 0o644,
                        )
                        self.assertEqual(member.mtime, 1_800_000_000)

            self.assertNotIn("release-report.json", WHEEL_MEMBER_CONTENTS)
            self.assertNotIn("release-report.json", SDIST_MEMBER_CONTENTS)

    def test_negative_closure_fixtures_have_coherent_internal_manifests(self) -> None:
        for name, wheel_members, sdist_members in closure_mutations():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                wheel = write_wheel(root, members=wheel_members)
                sdist = write_sdist(root, members=sdist_members)
                self.assert_wheel_record_is_consistent(wheel)
                self.assert_sdist_sources_are_consistent(sdist)

    def test_symlink_fixtures_are_causal_and_internally_self_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "artifacts"
            root.mkdir()
            wheel, _sdist = write_artifacts(root)
            outside = parent / "outside.whl"
            wheel.rename(outside)
            wheel.symlink_to(outside)
            self.assertTrue(wheel.is_symlink())
            self.assertEqual(outside.read_bytes(), wheel.read_bytes())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = self.write_nonregular_wheel(root)
            self.assert_wheel_record_is_consistent(wheel)
            with zipfile.ZipFile(wheel) as archive:
                info = archive.getinfo(
                    "control_plane_kit_architecture_testing/py.typed"
                )
                self.assertEqual((info.external_attr >> 16) & 0o170000, 0o120000)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdist = self.write_nonregular_sdist(root)
            self.assert_sdist_sources_are_consistent(sdist)
            with tarfile.open(sdist, mode="r:gz") as archive:
                member = archive.getmember(
                    "control_plane_kit_architecture_testing-0.1.0/README.md"
                )
                self.assertTrue(member.issym())

    def test_synthetic_wheel_and_sdist_form_the_complete_accepted_closure(self) -> None:
        release = require_release(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            report = self.verify_fixture(release, root)
            self.assertEqual(tuple(value.filename for value in report.artifacts), tuple(sorted(path.name for path in root.iterdir())))

    def test_verifier_rejects_missing_extra_embedded_report_and_runtime_dependency(self) -> None:
        release = require_release(self)
        for name, wheel_members, sdist_members in closure_mutations():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_wheel(root, members=wheel_members)
                write_sdist(root, members=sdist_members)
                report = release_report(release, root)
                snapshot = {path.name: path.read_bytes() for path in root.iterdir()}
                error = captured_error(
                    self,
                    release.ReleaseBuildReportError,
                    lambda report=report, root=root: release.verify_release_report(report, root),
                )
                self.assertEqual(str(error), "release artifact set is invalid")
                self.assertNotIn("candidate", str(error))
                self.assertEqual(
                    set(root.iterdir()),
                    {root / value.filename for value in report.artifacts},
                )
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()},
                    snapshot,
                )

    def test_verifier_rejects_root_and_archive_member_symlinks(self) -> None:
        release = require_release(self)

        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "artifacts"
            root.mkdir()
            wheel, _sdist = write_artifacts(root)
            report = release_report(release, root)
            outside = parent / "outside.whl"
            wheel.rename(outside)
            wheel.symlink_to(outside)
            error = captured_error(
                self,
                release.ReleaseBuildReportError,
                lambda: release.verify_release_report(report, root),
            )
            self.assertEqual(str(error), "release artifact set is invalid")
            self.assertTrue(wheel.is_symlink())
            self.assertEqual(outside.read_bytes(), wheel.read_bytes())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wheel = self.write_nonregular_wheel(root)
            write_sdist(root)
            self.assert_wheel_record_is_consistent(wheel)
            with zipfile.ZipFile(wheel) as archive:
                info = archive.getinfo(
                    "control_plane_kit_architecture_testing/py.typed"
                )
                self.assertEqual((info.external_attr >> 16) & 0o170000, 0o120000)
            report = release_report(release, root)
            error = captured_error(
                self,
                release.ReleaseBuildReportError,
                lambda: release.verify_release_report(report, root),
            )
            self.assertEqual(str(error), "release artifact set is invalid")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_wheel(root)
            sdist = self.write_nonregular_sdist(root)
            self.assert_sdist_sources_are_consistent(sdist)
            with tarfile.open(sdist, mode="r:gz") as archive:
                member = archive.getmember(
                    "control_plane_kit_architecture_testing-0.1.0/README.md"
                )
                self.assertTrue(member.issym())
            report = release_report(release, root)
            error = captured_error(
                self,
                release.ReleaseBuildReportError,
                lambda: release.verify_release_report(report, root),
            )
            self.assertEqual(str(error), "release artifact set is invalid")

    def test_verifier_rejects_identity_hash_size_and_unsafe_member_modes(self) -> None:
        release = require_release(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            report = release_report(release, root)
            wheel = next(path for path in root.iterdir() if path.suffix == ".whl")
            original = wheel.read_bytes()

            wheel.write_bytes(original + b"drift")
            error = captured_error(
                self,
                release.ReleaseBuildReportError,
                lambda: release.verify_release_report(report, root),
            )
            self.assertEqual(str(error), "release artifact set is invalid")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            report = release_report(release, root)
            first, second = report.artifacts
            for drifted in (
                replace(first, size=first.size + 1),
                replace(first, sha256="f" * 64),
            ):
                with self.subTest(drift=drifted):
                    changed = replace(report, artifacts=(drifted, second))
                    error = captured_error(
                        self,
                        release.ReleaseBuildReportError,
                        lambda changed=changed: release.verify_release_report(changed, root),
                    )
                    self.assertEqual(str(error), "release artifact set is invalid")

            (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
            error = captured_error(
                self,
                release.ReleaseBuildReportError,
                lambda: release.verify_release_report(report, root),
            )
            self.assertEqual(str(error), "release artifact set is invalid")

        for mode in (0o600, 0o755):
            with self.subTest(mode=oct(mode)), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                write_wheel(root, mode=mode)
                write_sdist(root)
                report = release_report(release, root)
                error = captured_error(
                    self,
                    release.ReleaseBuildReportError,
                    lambda report=report, root=root: release.verify_release_report(report, root),
                )
                self.assertEqual(str(error), "release artifact set is invalid")

    def test_verifier_requires_exact_report_and_artifact_root_inputs(self) -> None:
        release = require_release(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            report = release_report(release, root)

            class HostilePath(type(root)):
                pass

            for candidate in (root.as_posix(), HostilePath(root)):
                with self.subTest(candidate=type(candidate)):
                    error = captured_error(
                        self,
                        (TypeError, release.ReleaseBuildReportError),
                        lambda candidate=candidate: release.verify_release_report(
                            report, candidate
                        ),
                    )
                    self.assertEqual(str(error), "release artifact set is invalid")


if __name__ == "__main__":
    unittest.main()
