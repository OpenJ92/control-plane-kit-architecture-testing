from __future__ import annotations

import io
import stat
import unittest
import zipfile

from canonical_archive_fixture import (
    MAX_COMPRESSED_BYTES,
    SOURCE_DATE_EPOCH,
    WHEEL_MEMBER_CONTENTS,
    WHEEL_RECORD_NAME,
    canonical_wheel_bytes,
    raw_wheel_bytes,
    require_canonical,
    wheel_payloads,
    wheel_record_is_consistent,
)
from release_build_fixture import coherent_wheel_members


class CanonicalWheelTests(unittest.TestCase):
    def test_raw_and_canonical_wheels_normalize_to_one_exact_document(self) -> None:
        language = require_canonical(self)
        raw = raw_wheel_bytes()
        expected = canonical_wheel_bytes()
        actual = language.canonicalize_wheel(raw, source_date_epoch=SOURCE_DATE_EPOCH)
        self.assertEqual(actual, expected)
        self.assertEqual(
            language.canonicalize_wheel(actual, source_date_epoch=SOURCE_DATE_EPOCH),
            expected,
        )
        self.assertLessEqual(len(actual), MAX_COMPRESSED_BYTES)
        self.assertNotEqual(raw, actual)

    def test_member_order_modes_times_and_headers_are_exact(self) -> None:
        language = require_canonical(self)
        encoded = language.canonicalize_wheel(
            raw_wheel_bytes(), source_date_epoch=SOURCE_DATE_EPOCH
        )
        with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
            infos = archive.infolist()
            self.assertEqual(tuple(info.filename for info in infos), tuple(WHEEL_MEMBER_CONTENTS))
            self.assertTrue(all(info.compress_type == zipfile.ZIP_STORED for info in infos))
            self.assertTrue(all(info.create_system == 3 for info in infos))
            self.assertTrue(
                all(
                    stat.S_ISREG(info.external_attr >> 16)
                    and stat.S_IMODE(info.external_attr >> 16) == 0o644
                    for info in infos
                )
            )
            self.assertEqual(archive.comment, b"")
            self.assertFalse(any(info.flag_bits & 0x09 for info in infos))
        self.assertNotIn(b"PK\x07\x08", encoded)
        self.assertNotIn(b"PK\x06\x06", encoded)
        self.assertNotIn(b"PK\x06\x07", encoded)

    def test_wheel_payloads_and_record_are_preserved_exactly(self) -> None:
        language = require_canonical(self)
        raw = raw_wheel_bytes()
        encoded = language.canonicalize_wheel(raw, source_date_epoch=SOURCE_DATE_EPOCH)
        self.assertEqual(dict(wheel_payloads(encoded)), WHEEL_MEMBER_CONTENTS)
        self.assertEqual(
            dict(wheel_payloads(encoded))[WHEEL_RECORD_NAME],
            WHEEL_MEMBER_CONTENTS[WHEEL_RECORD_NAME],
        )
        self.assertTrue(wheel_record_is_consistent(encoded))

    def test_payload_changes_are_preserved_not_rewritten(self) -> None:
        language = require_canonical(self)
        changed = dict(WHEEL_MEMBER_CONTENTS)
        changed["control_plane_kit_architecture_testing/python_source.py"] += b"change\n"
        changed = coherent_wheel_members(changed)
        accepted = language.canonicalize_wheel(
            raw_wheel_bytes(), source_date_epoch=SOURCE_DATE_EPOCH
        )
        candidate = language.canonicalize_wheel(
            raw_wheel_bytes(changed), source_date_epoch=SOURCE_DATE_EPOCH
        )
        self.assertNotEqual(accepted, candidate)
        self.assertEqual(
            dict(wheel_payloads(candidate))[
                "control_plane_kit_architecture_testing/python_source.py"
            ],
            changed["control_plane_kit_architecture_testing/python_source.py"],
        )
        self.assertEqual(
            dict(wheel_payloads(candidate))[WHEEL_RECORD_NAME],
            changed[WHEEL_RECORD_NAME],
        )


if __name__ == "__main__":
    unittest.main()
