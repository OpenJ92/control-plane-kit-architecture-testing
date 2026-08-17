from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from canonical_archive_fixture import (
    MAX_COMPRESSED_BYTES,
    SETUP_CFG,
    SETUP_CFG_NAME,
    SOURCE_DATE_EPOCH,
    admitted_sdist_variants,
    admitted_wheel_variants,
    canonical_sdist_bytes,
    canonical_wheel_bytes,
    invalid_sdist_variants,
    invalid_wheel_variants,
    raw_sdist_bytes,
    raw_wheel_bytes,
    require_canonical,
    sdist_payloads,
    stage_one_accepted_noncanonical_sdist_bytes,
    stage_one_accepted_noncanonical_wheel_bytes,
    wheel_payloads,
)
from release_build_fixture import (
    SDIST_MEMBER_CONTENTS,
    SDIST_NAME,
    WHEEL_MEMBER_CONTENTS,
    WHEEL_NAME,
    release_report,
    require_release,
)


class CanonicalArchiveVerifierIntegrationTests(unittest.TestCase):
    def _write(self, root: Path, wheel: bytes, sdist: bytes) -> None:
        (root / WHEEL_NAME).write_bytes(wheel)
        (root / SDIST_NAME).write_bytes(sdist)

    def assert_verifier_rejects(self, release, wheel: bytes, sdist: bytes) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, wheel, sdist)
            report = release_report(release, root)
            with self.assertRaises(release.ReleaseBuildReportError) as raised:
                release.verify_release_report(report, root)
            self.assertEqual(str(raised.exception), "release artifact set is invalid")

    def test_noncanonical_witnesses_preserve_the_predecessor_semantic_closure(self) -> None:
        wheel = stage_one_accepted_noncanonical_wheel_bytes()
        sdist = stage_one_accepted_noncanonical_sdist_bytes()
        self.assertEqual(dict(wheel_payloads(wheel)), WHEEL_MEMBER_CONTENTS)
        self.assertEqual(dict(sdist_payloads(sdist)), SDIST_MEMBER_CONTENTS)
        self.assertNotEqual(wheel, canonical_wheel_bytes())
        self.assertNotEqual(sdist, canonical_sdist_bytes())

    def test_variant_fixture_matrices_are_bounded_and_source_independent(self) -> None:
        sdist_variants = admitted_sdist_variants()
        wheel_variants = admitted_wheel_variants()
        self.assertEqual(len({name for name, _ in sdist_variants}), len(sdist_variants))
        self.assertEqual(len({name for name, _ in wheel_variants}), len(wheel_variants))
        for name, encoded in sdist_variants:
            with self.subTest(kind="sdist admitted", name=name):
                self.assertIs(type(encoded), bytes)
                self.assertLessEqual(len(encoded), MAX_COMPRESSED_BYTES)
                payloads = dict(sdist_payloads(encoded))
                self.assertIn(payloads.pop(SETUP_CFG_NAME), (SETUP_CFG,) + (
                    b"[egg_info]\ntag_date=0\ntag_build=\n",
                    b"# generated\n[egg_info]\n tag_build = \n tag_date = 0\n",
                    b"[egg_info]\n; generated\ntag_date : 0\ntag_build :\n",
                ))
                self.assertEqual(payloads, SDIST_MEMBER_CONTENTS)
        for name, encoded in wheel_variants:
            with self.subTest(kind="wheel admitted", name=name):
                self.assertIs(type(encoded), bytes)
                self.assertLessEqual(len(encoded), MAX_COMPRESSED_BYTES)
                self.assertEqual(dict(wheel_payloads(encoded)), WHEEL_MEMBER_CONTENTS)
        for kind, variants in (
            ("sdist malformed", invalid_sdist_variants()),
            ("wheel malformed", invalid_wheel_variants()),
        ):
            self.assertEqual(len({name for name, _ in variants}), len(variants))
            for name, encoded in variants:
                with self.subTest(kind=kind, name=name):
                    self.assertIs(type(encoded), bytes)
                    self.assertGreater(len(encoded), 0)
                    self.assertLessEqual(len(encoded), MAX_COMPRESSED_BYTES)

    def test_stage_one_verifier_accepts_only_canonical_artifacts(self) -> None:
        canonical = require_canonical(self)
        release = require_release(self)
        raw_wheel = raw_wheel_bytes()
        raw_sdist = raw_sdist_bytes()
        wheel = canonical.canonicalize_wheel(
            raw_wheel, source_date_epoch=SOURCE_DATE_EPOCH
        )
        sdist = canonical.canonicalize_sdist(
            raw_sdist, source_date_epoch=SOURCE_DATE_EPOCH
        )
        self.assertEqual(wheel, canonical_wheel_bytes())
        self.assertEqual(sdist, canonical_sdist_bytes())

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, wheel, sdist)
            report = release_report(release, root)
            self.assertIsNone(release.verify_release_report(report, root))

        self.assert_verifier_rejects(release, raw_wheel, sdist)
        self.assert_verifier_rejects(release, wheel, raw_sdist)

    def test_verifier_rejects_predecessor_accepted_noncanonical_bytes(self) -> None:
        canonical = require_canonical(self)
        release = require_release(self)
        noncanonical_wheel = stage_one_accepted_noncanonical_wheel_bytes()
        noncanonical_sdist = stage_one_accepted_noncanonical_sdist_bytes()
        wheel = canonical_wheel_bytes()
        sdist = canonical_sdist_bytes()
        self.assertNotEqual(noncanonical_wheel, wheel)
        self.assertNotEqual(noncanonical_sdist, sdist)
        self.assertEqual(
            canonical.canonicalize_wheel(
                noncanonical_wheel, source_date_epoch=SOURCE_DATE_EPOCH
            ),
            wheel,
        )
        self.assert_verifier_rejects(release, noncanonical_wheel, sdist)
        self.assert_verifier_rejects(release, wheel, noncanonical_sdist)

    def test_canonicalization_does_not_mutate_input_or_emit_a_report(self) -> None:
        canonical = require_canonical(self)
        for function, raw in (
            (canonical.canonicalize_wheel, raw_wheel_bytes()),
            (canonical.canonicalize_sdist, raw_sdist_bytes()),
        ):
            before = bytes(raw)
            result = function(raw, source_date_epoch=SOURCE_DATE_EPOCH)
            self.assertEqual(raw, before)
            self.assertIs(type(result), bytes)
            self.assertNotIn(b"release-report.json", result)
            self.assertEqual(sha256(result).digest(), sha256(bytes(result)).digest())


if __name__ == "__main__":
    unittest.main()
