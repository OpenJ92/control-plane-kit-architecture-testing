from __future__ import annotations

import unittest
from unittest import mock

from canonical_archive_fixture import (
    CANONICAL,
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


class _ProbeInfo:
    def __init__(self, name: str, size: int, ledger: list[tuple[str, object]]) -> None:
        self._name = name
        self._size = size
        self._ledger = ledger
        self.compress_type = 0
        self.create_system = 3
        self.external_attr = 0o100644 << 16
        self.date_time = (2027, 1, 15, 8, 0, 0)
        self.flag_bits = 0

    @property
    def filename(self) -> str:
        self._ledger.append(("name", self._name))
        return self._name

    @property
    def file_size(self) -> int:
        self._ledger.append(("size", self._name))
        return self._size

    def is_dir(self) -> bool:
        return False


class _ProbeZipFile:
    def __init__(
        self,
        rows: tuple[tuple[str, int], ...],
        ledger: list[tuple[str, object]],
    ) -> None:
        self._infos = tuple(_ProbeInfo(name, size, ledger) for name, size in rows)
        self._ledger = ledger
        self.comment = b""

    def __enter__(self) -> "_ProbeZipFile":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def infolist(self) -> list[_ProbeInfo]:
        self._ledger.append(("headers", len(self._infos)))
        return list(self._infos)

    def namelist(self) -> list[str]:
        return [info.filename for info in self._infos]

    def read(self, member: _ProbeInfo | str) -> bytes:
        if type(member) is str:
            selected = next(info for info in self._infos if info._name == member)
        else:
            selected = member
        self._ledger.append(("payload", selected._name))
        return b"x" * selected._size


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

    def test_complete_compressed_bound_precedes_format_dispatch(self) -> None:
        language = require_canonical(self)
        for function_name, dependency_name, parser_name in (
            ("canonicalize_wheel", "zipfile", "ZipFile"),
            ("canonicalize_sdist", "zlib", "decompressobj"),
        ):
            function = getattr(language, function_name)
            dependency = getattr(language, dependency_name)
            dispatches: list[str] = []

            def parser_canary(*args: object, **kwargs: object) -> object:
                dispatches.append("parser")
                raise RuntimeError("format parser canary")

            with self.subTest(function=function_name), mock.patch.object(
                dependency, parser_name, parser_canary
            ):
                with self.assertRaisesRegex(RuntimeError, "format parser canary"):
                    function(b"x" * MAX_COMPRESSED_BYTES, source_date_epoch=SOURCE_DATE_EPOCH)
                self.assertEqual(dispatches, ["parser"])
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

    def test_structural_ceilings_are_preflight_not_semantic_acceptance(self) -> None:
        language = require_canonical(self)
        expected_names = (
            "control_plane_kit_architecture_testing/__init__.py",
            "control_plane_kit_architecture_testing/architecture_policy.py",
            "control_plane_kit_architecture_testing/py.typed",
            "control_plane_kit_architecture_testing/python_source.py",
            "control_plane_kit_architecture_testing-0.1.0.dist-info/METADATA",
            "control_plane_kit_architecture_testing-0.1.0.dist-info/WHEEL",
            "control_plane_kit_architecture_testing-0.1.0.dist-info/licenses/LICENSE",
            "control_plane_kit_architecture_testing-0.1.0.dist-info/RECORD",
        )

        def invoke(rows: tuple[tuple[str, int], ...]) -> list[tuple[str, object]]:
            ledger: list[tuple[str, object]] = []
            archive = _ProbeZipFile(rows, ledger)
            with mock.patch.object(language.zipfile, "ZipFile", return_value=archive):
                captured_error(
                    self,
                    language.CanonicalArchiveError,
                    lambda: language.canonicalize_wheel(
                        b"candidate", source_date_epoch=SOURCE_DATE_EPOCH
                    ),
                )
            return ledger

        at_count = invoke(tuple((f"member-{index}", 0) for index in range(MAX_MEMBERS)))
        self.assertIn(("headers", MAX_MEMBERS), at_count)
        self.assertTrue(any(stage == "name" for stage, _ in at_count))
        over_count = invoke(
            tuple((f"member-{index}", 0) for index in range(MAX_MEMBERS + 1))
        )
        self.assertEqual(over_count, [("headers", MAX_MEMBERS + 1)])

        at_name = invoke((("n" * MAX_MEMBER_NAME_BYTES, 0),))
        self.assertIn(("name", "n" * MAX_MEMBER_NAME_BYTES), at_name)
        over_name = invoke((("n" * (MAX_MEMBER_NAME_BYTES + 1), 0),))
        self.assertFalse(any(stage in ("size", "payload") for stage, _ in over_name))

        at_member_rows = tuple(
            (name, MAX_MEMBER_BYTES if index == 0 else 0)
            for index, name in enumerate(expected_names)
        )
        at_member = invoke(at_member_rows)
        self.assertIn(("payload", expected_names[0]), at_member)
        over_member = invoke(
            tuple(
                (name, MAX_MEMBER_BYTES + 1 if index == 0 else 0)
                for index, name in enumerate(expected_names)
            )
        )
        self.assertFalse(any(stage == "payload" for stage, _ in over_member))

        at_aggregate = invoke(tuple((name, MAX_MEMBER_BYTES) for name in expected_names))
        self.assertEqual(MAX_MEMBER_BYTES * len(expected_names), MAX_EXPANDED_BYTES)
        self.assertEqual(
            tuple(value for stage, value in at_aggregate if stage == "payload"),
            expected_names,
        )
        over_aggregate = invoke(
            tuple(
                (name, MAX_MEMBER_BYTES + 1 if index == 7 else MAX_MEMBER_BYTES)
                for index, name in enumerate(expected_names)
            )
        )
        self.assertNotIn(("payload", expected_names[-1]), over_aggregate)

    def test_unexpected_internal_faults_remain_raw(self) -> None:
        language = require_canonical(self)
        for exception in (TypeError("internal type"), RuntimeError("internal runtime")):
            with self.subTest(exception=type(exception)), mock.patch.object(
                language.zipfile, "ZipFile", side_effect=exception
            ):
                with self.assertRaises(type(exception)) as raised:
                    language.canonicalize_wheel(
                        b"candidate", source_date_epoch=SOURCE_DATE_EPOCH
                    )
                self.assertIs(raised.exception, exception)


if __name__ == "__main__":
    unittest.main()
