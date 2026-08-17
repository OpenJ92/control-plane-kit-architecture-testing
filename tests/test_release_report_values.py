from __future__ import annotations

from dataclasses import fields, FrozenInstanceError, is_dataclass, replace
import unittest

from release_build_fixture import (
    BUILD_INPUT_ROWS,
    HostileInt,
    HostileStr,
    HostileTuple,
    build_inputs,
    captured_error,
    forge,
    release_report,
    require_release,
)


class ReleaseReportValueTests(unittest.TestCase):
    def test_public_values_are_exact_frozen_slotted_repository_values(self) -> None:
        release = require_release(self)
        expected_fields = {
            "BuildInputArtifact": (
                "name",
                "version",
                "filename",
                "url",
                "size",
                "sha256",
            ),
            "OutputArtifact": ("filename", "size", "sha256"),
            "ReleaseBuildReport": (
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
        }
        for name, field_names in expected_fields.items():
            with self.subTest(name=name):
                exact_type = getattr(release, name)
                self.assertTrue(is_dataclass(exact_type))
                self.assertTrue(exact_type.__dataclass_params__.frozen)
                self.assertEqual(tuple(field.name for field in fields(exact_type)), field_names)
                self.assertIn("__slots__", exact_type.__dict__)

        self.assertTrue(issubclass(release.ReleaseBuildReportError, ValueError))

        report = release_report(release)
        with self.assertRaises(FrozenInstanceError):
            report.commit = "c" * 40
        self.assertIs(type(report.build_inputs), tuple)
        self.assertIs(type(report.artifacts), tuple)
        self.assertNotIn("credential", repr(report).lower())

    def test_exact_four_wheel_input_closure_and_backend_security_correction(self) -> None:
        release = require_release(self)
        inputs = build_inputs(release)
        self.assertEqual(
            tuple(
                (
                    value.name,
                    value.version,
                    value.filename,
                    value.url,
                    value.size,
                    value.sha256,
                )
                for value in inputs
            ),
            BUILD_INPUT_ROWS,
        )
        self.assertEqual(tuple(value.name for value in inputs), tuple(sorted(value.name for value in inputs)))
        self.assertEqual(inputs[-1].version, "83.0.0")

    def test_artifact_values_are_deep_exact_nominal_bounded_and_redacted(self) -> None:
        release = require_release(self)
        valid_input = build_inputs(release)[0]
        valid_output = release.OutputArtifact("artifact.whl", 1, "a" * 64)

        for candidate in (
            (HostileStr(valid_input.name), valid_input.version, valid_input.filename, valid_input.url, valid_input.size, valid_input.sha256),
            (valid_input.name, valid_input.version, valid_input.filename, valid_input.url, HostileInt(valid_input.size), valid_input.sha256),
            (valid_input.name, valid_input.version, valid_input.filename, valid_input.url, 0, valid_input.sha256),
            (valid_input.name, valid_input.version, valid_input.filename, valid_input.url, 9_223_372_036_854_775_808, valid_input.sha256),
            (valid_input.name, valid_input.version, valid_input.filename, valid_input.url, valid_input.size, "A" * 64),
            (valid_input.name, valid_input.version, "bad\x00.whl", valid_input.url, valid_input.size, valid_input.sha256),
            (valid_input.name, valid_input.version, valid_input.filename, "https://user:secret@example.invalid/value.whl", valid_input.size, valid_input.sha256),
        ):
            with self.subTest(candidate=tuple(type(value) for value in candidate)):
                error = captured_error(
                    self,
                    (TypeError, ValueError),
                    lambda candidate=candidate: release.BuildInputArtifact(*candidate),
                )
                self.assertEqual(str(error), "release build artifact is invalid")

        class HostileOutput(release.OutputArtifact):
            pass

        for candidate in (
            HostileOutput(valid_output.filename, valid_output.size, valid_output.sha256),
            forge(release.OutputArtifact, filename=HostileStr("artifact.whl"), size=1, sha256="a" * 64),
        ):
            error = captured_error(
                self,
                (TypeError, ValueError),
                lambda candidate=candidate: release.ReleaseBuildReport(
                    "cpk.architecture-testing-release.v1",
                    "OpenJ92/control-plane-kit-architecture-testing",
                    "a" * 40,
                    "b" * 40,
                    "v0.1.0",
                    "0.1.0",
                    1,
                    "python:3.14-slim@sha256:" + "c" * 64,
                    "3.14.0",
                    "25.2",
                    build_inputs(release),
                    (candidate,),
                ),
            )
            self.assertEqual(str(error), "release build report is invalid")

    def test_report_coordinates_sums_and_order_are_closed(self) -> None:
        release = require_release(self)
        report = release_report(release)
        self.assertEqual(report.schema, "cpk.architecture-testing-release.v1")
        self.assertEqual(report.repository, "OpenJ92/control-plane-kit-architecture-testing")
        self.assertEqual(report.intended_tag, "v0.1.0")
        self.assertEqual(report.version, "0.1.0")
        self.assertEqual(report.source_date_epoch, 1_800_000_001)

        alternate_input = release.BuildInputArtifact(
            "build",
            "1.3.1",
            "build-1.3.1-py3-none-any.whl",
            "https://files.pythonhosted.org/packages/alternate/build-1.3.1-py3-none-any.whl",
            23_383,
            "c" * 64,
        )
        drifted_inputs = (alternate_input, *report.build_inputs[1:])
        foreign_output = release.OutputArtifact("foreign-0.1.0.tar.gz", 1, "d" * 64)

        invalid = (
            {"schema": "other"},
            {"repository": "Other/repository"},
            {"commit": "a" * 39},
            {"tree": "B" * 40},
            {"intended_tag": "0.1.0"},
            {"version": "0.1.1"},
            {"source_date_epoch": True},
            {"source_date_epoch": 0},
            {"source_date_epoch": 9_223_372_036_854_775_808},
            {"python_image": "python:3.14-slim"},
            {"build_inputs": HostileTuple(report.build_inputs)},
            {"build_inputs": tuple(reversed(report.build_inputs))},
            {"build_inputs": report.build_inputs + (report.build_inputs[0],)},
            {"build_inputs": drifted_inputs},
            {"artifacts": tuple(reversed(report.artifacts))},
            {"artifacts": report.artifacts + (report.artifacts[0],)},
            {"artifacts": report.artifacts[:1]},
            {"artifacts": (report.artifacts[0], foreign_output)},
        )
        for changes in invalid:
            with self.subTest(changes=tuple(changes)):
                values = {field.name: getattr(report, field.name) for field in fields(report)}
                values.update(changes)
                error = captured_error(
                    self,
                    release.ReleaseBuildReportError,
                    lambda values=values: release.ReleaseBuildReport(**values),
                )
                self.assertEqual(str(error), "release build report is invalid")

    def test_source_date_epoch_is_exactly_zip_representable_in_utc(self) -> None:
        release = require_release(self)
        report = release_report(release)
        minimum = 315_532_800
        maximum = 4_354_819_199

        for candidate in (minimum, maximum):
            with self.subTest(accepted=candidate):
                accepted = replace(report, source_date_epoch=candidate)
                self.assertIs(type(accepted), release.ReleaseBuildReport)
                self.assertEqual(accepted.source_date_epoch, candidate)

        for candidate in (minimum - 1, maximum + 1, 253_402_300_800):
            with self.subTest(rejected=candidate):
                error = captured_error(
                    self,
                    release.ReleaseBuildReportError,
                    lambda candidate=candidate: replace(
                        report,
                        source_date_epoch=candidate,
                    ),
                )
                self.assertEqual(str(error), "release build report is invalid")
                self.assertNotIn(str(candidate), str(error))


if __name__ == "__main__":
    unittest.main()
