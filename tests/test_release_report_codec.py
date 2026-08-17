from __future__ import annotations

import json
import unittest

from release_build_fixture import (
    captured_error,
    release_report,
    require_release,
)


EXPECTED_REPORT_BYTES = (
    b'{"artifacts":['
    b'{"filename":"control_plane_kit_architecture_testing-0.1.0-py3-none-any.whl",'
    b'"sha256":"1111111111111111111111111111111111111111111111111111111111111111",'
    b'"size":101},'
    b'{"filename":"control_plane_kit_architecture_testing-0.1.0.tar.gz",'
    b'"sha256":"2222222222222222222222222222222222222222222222222222222222222222",'
    b'"size":202}],'
    b'"build_inputs":['
    b'{"filename":"build-1.3.0-py3-none-any.whl","name":"build",'
    b'"sha256":"7145f0b5061ba90a1500d60bd1b13ca0a8a4cebdd0cc16ed8adf1c0e739f43b4",'
    b'"size":23382,"url":"https://files.pythonhosted.org/packages/cb/8c/'
    b'2b30c12155ad8de0cf641d76a8b396a16d2c36bc6d50b621a62b7c4567c1/'
    b'build-1.3.0-py3-none-any.whl","version":"1.3.0"},'
    b'{"filename":"packaging-25.0-py3-none-any.whl","name":"packaging",'
    b'"sha256":"29572ef2b1f17581046b3a2227d5c611fb25ec70ca1ba8554b24b0e69331a484",'
    b'"size":66469,"url":"https://files.pythonhosted.org/packages/20/12/'
    b'38679034af332785aac8774540895e234f4d07f7545804097de4b666afd8/'
    b'packaging-25.0-py3-none-any.whl","version":"25.0"},'
    b'{"filename":"pyproject_hooks-1.2.0-py3-none-any.whl","name":"pyproject-hooks",'
    b'"sha256":"9e5c6bfa8dcc30091c74b0cf803c81fdd29d94f01992a7707bc97babb1141913",'
    b'"size":10216,"url":"https://files.pythonhosted.org/packages/bd/24/'
    b'12818598c362d7f300f18e74db45963dbcb85150324092410c8b49405e42/'
    b'pyproject_hooks-1.2.0-py3-none-any.whl","version":"1.2.0"},'
    b'{"filename":"setuptools-83.0.0-py3-none-any.whl","name":"setuptools",'
    b'"sha256":"29b23c360f22f414dc7336bb39178cc7bcbf6021ed2733cde173f09dba19abb3",'
    b'"size":1008090,"url":"https://files.pythonhosted.org/packages/5d/40/'
    b'e1e72872c6354b306daef1703549e8e83b4d43cfea356311bf722a043752/'
    b'setuptools-83.0.0-py3-none-any.whl","version":"83.0.0"}],'
    b'"commit":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",'
    b'"intended_tag":"v0.1.0","pip_version":"25.2",'
    b'"python_image":"python:3.14-slim@sha256:'
    b'ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4",'
    b'"python_version":"3.14.0",'
    b'"repository":"OpenJ92/control-plane-kit-architecture-testing",'
    b'"schema":"cpk.architecture-testing-release.v1",'
    b'"source_date_epoch":1800000001,'
    b'"tree":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","version":"0.1.0"}\n'
)


class ReleaseReportCodecTests(unittest.TestCase):
    def test_canonical_golden_fixture_is_strict_valid_json(self) -> None:
        self.assertTrue(EXPECTED_REPORT_BYTES.endswith(b"\n"))
        document = json.loads(EXPECTED_REPORT_BYTES)
        self.assertEqual(document["schema"], "cpk.architecture-testing-release.v1")
        self.assertEqual(document["version"], "0.1.0")
        self.assertEqual(len(document["build_inputs"]), 4)
        self.assertEqual(len(document["artifacts"]), 2)
        self.assertEqual(
            json.dumps(
                document,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("ascii")
            + b"\n",
            EXPECTED_REPORT_BYTES,
        )

    def test_canonical_document_has_exact_sorted_compact_ascii_shape_and_lf(self) -> None:
        release = require_release(self)
        report = release_report(release)
        encoded = release.release_report_bytes(report)

        self.assertIs(type(encoded), bytes)
        self.assertEqual(encoded, EXPECTED_REPORT_BYTES)
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertFalse(encoded.endswith(b"\n\n"))
        self.assertNotIn(b" ", encoded)
        self.assertNotIn(b"\r", encoded)
        self.assertEqual(release.parse_release_report(encoded), report)
        self.assertEqual(release.release_report_bytes(release.parse_release_report(encoded)), encoded)
        self.assertLessEqual(len(encoded), 65_536)

        self.assertLess(encoded.index(b'"artifacts"'), encoded.index(b'"build_inputs"'))
        self.assertLess(encoded.index(b'"build_inputs"'), encoded.index(b'"commit"'))
        first_input = encoded.index(b'"filename":"build-1.3.0-py3-none-any.whl"')
        self.assertLess(first_input, encoded.index(b'"name":"build"', first_input))

    def test_parser_rejects_noncanonical_duplicate_unknown_and_malformed_json(self) -> None:
        release = require_release(self)
        encoded = release.release_report_bytes(release_report(release))
        candidates = (
            bytearray(encoded),
            encoded[:-1],
            encoded + b"\n",
            encoded.replace(b'"schema":', b'"schema":"duplicate","schema":', 1),
            encoded.replace(b'{"artifacts":', b'{"unknown":0,"artifacts":', 1),
            encoded.replace(b'"source_date_epoch":1800000001', b'"source_date_epoch":true', 1),
            encoded.replace(b'"version":"0.1.0"', b'"version":"0.1.0",', 1),
            b"[]\n",
            b'{"candidate":"secret-value"}\n',
            b"\xff\n",
        )
        for candidate in candidates:
            with self.subTest(candidate=bytes(candidate[:24])):
                error = captured_error(
                    self,
                    release.ReleaseBuildReportError,
                    lambda candidate=candidate: release.parse_release_report(candidate),
                )
                self.assertEqual(str(error), "release report document is invalid")
                self.assertNotIn("secret", str(error))
                self.assertNotIn("candidate", str(error))

    def test_codec_revalidates_forged_report_before_encoding(self) -> None:
        release = require_release(self)
        report = release_report(release)
        forged = object.__new__(release.ReleaseBuildReport)
        for name in (
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
        ):
            object.__setattr__(forged, name, getattr(report, name))
        object.__setattr__(forged, "commit", "bad")
        error = captured_error(
            self,
            release.ReleaseBuildReportError,
            lambda: release.release_report_bytes(forged),
        )
        self.assertEqual(str(error), "release report document is invalid")


if __name__ == "__main__":
    unittest.main()
