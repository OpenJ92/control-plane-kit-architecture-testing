from __future__ import annotations

import io
import tarfile
import unittest

from canonical_archive_fixture import (
    MAX_COMPRESSED_BYTES,
    SDIST_MEMBER_CONTENTS,
    SDIST_PREFIX,
    SETUP_CFG,
    SETUP_CFG_NAME,
    SOURCE_DATE_EPOCH,
    canonical_sdist_bytes,
    raw_sdist_bytes,
    require_canonical,
    sdist_payloads,
)


class CanonicalSdistTests(unittest.TestCase):
    def test_raw_and_canonical_forms_normalize_to_one_exact_document(self) -> None:
        language = require_canonical(self)
        raw = raw_sdist_bytes()
        expected = canonical_sdist_bytes()

        self.assertEqual(
            language.canonicalize_sdist(raw, source_date_epoch=SOURCE_DATE_EPOCH),
            expected,
        )
        self.assertEqual(
            language.canonicalize_sdist(expected, source_date_epoch=SOURCE_DATE_EPOCH),
            expected,
        )
        self.assertLessEqual(len(expected), MAX_COMPRESSED_BYTES)
        self.assertNotEqual(raw, expected)

    def test_setup_cfg_is_the_only_raw_only_member_and_is_semantically_exact(self) -> None:
        language = require_canonical(self)
        raw_payloads = dict(sdist_payloads(raw_sdist_bytes()))
        canonical_payloads = dict(
            sdist_payloads(
                language.canonicalize_sdist(
                    raw_sdist_bytes(), source_date_epoch=SOURCE_DATE_EPOCH
                )
            )
        )
        self.assertEqual(raw_payloads.pop(SETUP_CFG_NAME), SETUP_CFG)
        self.assertEqual(raw_payloads, canonical_payloads)
        self.assertEqual(canonical_payloads, SDIST_MEMBER_CONTENTS)

        mutations = (
            SETUP_CFG.replace(b"tag_date = 0", b"tag_date = 1"),
            SETUP_CFG.replace(b"tag_build =", b"tag_build = candidate"),
            SETUP_CFG + b"unknown = candidate\n",
        )
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                members = {**SDIST_MEMBER_CONTENTS, SETUP_CFG_NAME: candidate}
                with self.assertRaises(language.CanonicalArchiveError) as raised:
                    language.canonicalize_sdist(
                        raw_sdist_bytes(members),
                        source_date_epoch=SOURCE_DATE_EPOCH,
                    )
                self.assertEqual(str(raised.exception), "release archive is invalid")
                self.assertNotIn("candidate", str(raised.exception))

    def test_payload_changes_are_preserved_not_rewritten(self) -> None:
        language = require_canonical(self)
        accepted = dict(SDIST_MEMBER_CONTENTS)
        changed = dict(SDIST_MEMBER_CONTENTS)
        changed["AGENTS.md"] += b"semantic-change\n"
        first = language.canonicalize_sdist(
            raw_sdist_bytes({**accepted, SETUP_CFG_NAME: SETUP_CFG}),
            source_date_epoch=SOURCE_DATE_EPOCH,
        )
        second = language.canonicalize_sdist(
            raw_sdist_bytes({**changed, SETUP_CFG_NAME: SETUP_CFG}),
            source_date_epoch=SOURCE_DATE_EPOCH,
        )
        self.assertNotEqual(first, second)
        self.assertEqual(dict(sdist_payloads(second))["AGENTS.md"], changed["AGENTS.md"])

    def test_canonical_gzip_and_ustar_metadata_are_exact(self) -> None:
        language = require_canonical(self)
        encoded = language.canonicalize_sdist(
            raw_sdist_bytes(), source_date_epoch=SOURCE_DATE_EPOCH
        )
        self.assertEqual(encoded[:10], b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff")
        with tarfile.open(fileobj=io.BytesIO(encoded), mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual(members[0].name, SDIST_PREFIX)
            self.assertTrue(all(member.uid == member.gid == 0 for member in members))
            self.assertTrue(all(member.uname == member.gname == "" for member in members))
            self.assertTrue(all(member.mtime == SOURCE_DATE_EPOCH for member in members))
            self.assertTrue(all(member.type in (tarfile.DIRTYPE, tarfile.REGTYPE) for member in members))
            self.assertTrue(all(member.pax_headers == {} for member in members))
            file_names = tuple(
                member.name.split("/", 1)[1] for member in members if member.isfile()
            )
            self.assertEqual(file_names, tuple(SDIST_MEMBER_CONTENTS))


if __name__ == "__main__":
    unittest.main()
