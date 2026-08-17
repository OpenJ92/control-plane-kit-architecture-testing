from __future__ import annotations

import unittest
from unittest import mock

from canonical_archive_fixture import (
    HostileBytes,
    HostileInt,
    MAX_COMPRESSED_BYTES,
    MAX_EXPANDED_BYTES,
    MAX_MEMBER_BYTES,
    MAX_MEMBER_NAME_BYTES,
    MAX_MEMBERS,
    SOURCE_DATE_EPOCH,
    captured_error,
    require_canonical,
)


class CanonicalArchiveBoundaryTests(unittest.TestCase):
    def test_public_surface_and_exact_nominal_inputs(self) -> None:
        language = require_canonical(self)
        self.assertEqual(
            language.__all__,
            ("CanonicalArchiveError", "canonicalize_sdist", "canonicalize_wheel"),
        )
        self.assertTrue(issubclass(language.CanonicalArchiveError, ValueError))

        candidates = (
            (HostileBytes(b"candidate"), SOURCE_DATE_EPOCH),
            (b"candidate", HostileInt(SOURCE_DATE_EPOCH)),
            (bytearray(b"candidate"), SOURCE_DATE_EPOCH),
            (b"candidate", True),
        )
        for function_name in ("canonicalize_sdist", "canonicalize_wheel"):
            function = getattr(language, function_name)
            for raw, epoch in candidates:
                with self.subTest(function=function_name, raw=type(raw), epoch=type(epoch)):
                    error = captured_error(
                        self,
                        TypeError,
                        lambda: function(raw, source_date_epoch=epoch),
                    )
                    self.assertEqual(str(error), "release archive input is invalid")
                    self.assertNotIn("candidate", str(error))

    def test_complete_compressed_bound_precedes_owned_decode_boundary(self) -> None:
        language = require_canonical(self)
        for function_name, decoder_name in (
            ("canonicalize_wheel", "_decode_wheel"),
            ("canonicalize_sdist", "_decode_sdist"),
        ):
            function = getattr(language, function_name)
            dispatches: list[str] = []

            def decoder_canary(*args: object, **kwargs: object) -> object:
                dispatches.append("decode")
                raise RuntimeError("owned decoder canary")

            with self.subTest(function=function_name), mock.patch.object(
                language, decoder_name, decoder_canary
            ):
                with self.assertRaisesRegex(RuntimeError, "owned decoder canary"):
                    function(b"x" * MAX_COMPRESSED_BYTES, source_date_epoch=SOURCE_DATE_EPOCH)
                self.assertEqual(dispatches, ["decode"])
                dispatches.clear()
                error = captured_error(
                    self,
                    language.CanonicalArchiveError,
                    lambda: function(
                        b"x" * (MAX_COMPRESSED_BYTES + 1),
                        source_date_epoch=SOURCE_DATE_EPOCH,
                    ),
                )
                self.assertEqual(str(error), "release archive is invalid")
                self.assertEqual(dispatches, [])

    def test_owned_bounded_reader_orders_structural_preflight(self) -> None:
        language = require_canonical(self)
        bounded_read = language._read_bounded_members

        def invoke(
            rows: tuple[tuple[str, int], ...],
        ) -> tuple[list[str], tuple[tuple[str, bytes], ...] | None]:
            reads: list[str] = []

            def read(name: str) -> bytes:
                reads.append(name)
                size = dict(rows)[name]
                return b"x" * size

            try:
                result = bounded_read(rows, read)
            except language.CanonicalArchiveError:
                return reads, None
            return reads, result

        count_rows = tuple((f"member-{index}", 0) for index in range(MAX_MEMBERS))
        reads, result = invoke(count_rows)
        self.assertEqual(reads, [name for name, _ in count_rows])
        self.assertEqual(result, tuple((name, b"") for name, _ in count_rows))
        over_reads, over_result = invoke(
            tuple((f"member-{index}", 0) for index in range(MAX_MEMBERS + 1))
        )
        self.assertEqual(over_reads, [])
        self.assertIsNone(over_result)

        for size, admitted in (
            (MAX_MEMBER_NAME_BYTES, True),
            (MAX_MEMBER_NAME_BYTES + 1, False),
        ):
            name = "n" * size
            reads, result = invoke(((name, 0),))
            self.assertEqual(reads, [name] if admitted else [])
            self.assertEqual(result is not None, admitted)

        reads, result = invoke((("payload", MAX_MEMBER_BYTES),))
        self.assertEqual(reads, ["payload"])
        self.assertEqual(len(result[0][1]), MAX_MEMBER_BYTES)
        reads, result = invoke((("payload", MAX_MEMBER_BYTES + 1),))
        self.assertEqual(reads, [])
        self.assertIsNone(result)

        exact = tuple((f"payload-{index}", MAX_MEMBER_BYTES) for index in range(8))
        self.assertEqual(sum(size for _, size in exact), MAX_EXPANDED_BYTES)
        reads, result = invoke(exact)
        self.assertEqual(reads, [name for name, _ in exact])
        self.assertIsNotNone(result)
        over = (*exact[:-1], (exact[-1][0], exact[-1][1] + 1))
        reads, result = invoke(over)
        self.assertEqual(reads, [])
        self.assertIsNone(result)

        read_fault = RuntimeError("payload reader canary")
        with self.assertRaises(RuntimeError) as raised:
            bounded_read((("payload", 0),), lambda name: (_ for _ in ()).throw(read_fault))
        self.assertIs(raised.exception, read_fault)

    def test_unexpected_internal_faults_remain_raw(self) -> None:
        language = require_canonical(self)
        for exception in (TypeError("internal type"), RuntimeError("internal runtime")):
            with self.subTest(exception=type(exception)), mock.patch.object(
                language, "_decode_wheel", side_effect=exception
            ):
                with self.assertRaises(type(exception)) as raised:
                    language.canonicalize_wheel(
                        b"candidate", source_date_epoch=SOURCE_DATE_EPOCH
                    )
                self.assertIs(raised.exception, exception)


if __name__ == "__main__":
    unittest.main()
