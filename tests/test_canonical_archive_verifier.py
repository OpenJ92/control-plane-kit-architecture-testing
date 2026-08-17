from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from canonical_archive_fixture import (
    SOURCE_DATE_EPOCH,
    canonical_sdist_bytes,
    canonical_wheel_bytes,
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

    def test_noncanonical_witnesses_preserve_the_predecessor_semantic_closure(self) -> None:
        wheel = stage_one_accepted_noncanonical_wheel_bytes()
        sdist = stage_one_accepted_noncanonical_sdist_bytes()
        self.assertEqual(dict(wheel_payloads(wheel)), WHEEL_MEMBER_CONTENTS)
        self.assertEqual(dict(sdist_payloads(sdist)), SDIST_MEMBER_CONTENTS)
        self.assertNotEqual(wheel, canonical_wheel_bytes())
        self.assertNotEqual(sdist, canonical_sdist_bytes())

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

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, raw_wheel, raw_sdist)
            report = release_report(release, root)
            with self.assertRaises(release.ReleaseBuildReportError) as raised:
                release.verify_release_report(report, root)
            self.assertEqual(str(raised.exception), "release artifact set is invalid")

    def test_verifier_rejects_predecessor_accepted_noncanonical_bytes(self) -> None:
        canonical = require_canonical(self)
        release = require_release(self)
        wheel = stage_one_accepted_noncanonical_wheel_bytes()
        sdist = stage_one_accepted_noncanonical_sdist_bytes()
        self.assertNotEqual(wheel, canonical_wheel_bytes())
        self.assertNotEqual(sdist, canonical_sdist_bytes())
        self.assertEqual(
            canonical.canonicalize_wheel(wheel, source_date_epoch=SOURCE_DATE_EPOCH),
            canonical_wheel_bytes(),
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write(root, wheel, sdist)
            report = release_report(release, root)
            with self.assertRaises(release.ReleaseBuildReportError) as raised:
                release.verify_release_report(report, root)
            self.assertEqual(str(raised.exception), "release artifact set is invalid")

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
