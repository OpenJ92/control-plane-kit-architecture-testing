from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

from release_build_fixture import (
    SDIST_MEMBER_CONTENTS,
    WHEEL_MEMBER_CONTENTS,
    captured_error,
    release_report,
    require_release,
    write_artifacts,
    write_sdist,
    write_wheel,
)


class ReleaseArtifactVerifierTests(unittest.TestCase):
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

    def test_synthetic_wheel_and_sdist_form_the_complete_accepted_closure(self) -> None:
        release = require_release(self)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_artifacts(root)
            report = self.verify_fixture(release, root)
            self.assertEqual(tuple(value.filename for value in report.artifacts), tuple(sorted(path.name for path in root.iterdir())))

    def test_verifier_rejects_missing_extra_embedded_report_and_runtime_dependency(self) -> None:
        release = require_release(self)
        mutations = []

        missing_wheel = dict(WHEEL_MEMBER_CONTENTS)
        missing_wheel.pop("control_plane_kit_architecture_testing/py.typed")
        mutations.append(("wheel missing", missing_wheel, SDIST_MEMBER_CONTENTS))

        extra_wheel = dict(WHEEL_MEMBER_CONTENTS)
        extra_wheel["tests/leak.py"] = b""
        mutations.append(("wheel extra", extra_wheel, SDIST_MEMBER_CONTENTS))

        dependency_wheel = dict(WHEEL_MEMBER_CONTENTS)
        dependency_wheel[
            "control_plane_kit_architecture_testing-0.1.0.dist-info/METADATA"
        ] += b"Requires-Dist: candidate-secret\n"
        mutations.append(("runtime dependency", dependency_wheel, SDIST_MEMBER_CONTENTS))

        report_wheel = dict(WHEEL_MEMBER_CONTENTS)
        report_wheel["release-report.json"] = b"{}\n"
        mutations.append(("embedded report", report_wheel, SDIST_MEMBER_CONTENTS))

        report_sdist = dict(SDIST_MEMBER_CONTENTS)
        report_sdist["release-report.json"] = b"{}\n"
        mutations.append(("sdist embedded report", WHEEL_MEMBER_CONTENTS, report_sdist))

        missing_sdist = dict(SDIST_MEMBER_CONTENTS)
        missing_sdist.pop("tests/policy_fixture.py")
        mutations.append(("sdist missing fixture", WHEEL_MEMBER_CONTENTS, missing_sdist))

        extra_sdist = dict(SDIST_MEMBER_CONTENTS)
        extra_sdist[".git/config"] = b"candidate-secret"
        mutations.append(("sdist git state", WHEEL_MEMBER_CONTENTS, extra_sdist))

        for name, wheel_members, sdist_members in mutations:
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
                self.assertEqual(set(root.iterdir()), {root / value.filename for value in report.artifacts})
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()},
                    snapshot,
                )

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
