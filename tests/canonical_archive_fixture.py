from __future__ import annotations

from base64 import urlsafe_b64encode
from datetime import datetime, timezone
from hashlib import sha256
import importlib
import io
import stat
import struct
import tarfile
from types import ModuleType
from typing import Any, Callable
import unittest
import zipfile
import zlib

from release_build_fixture import (
    SDIST_DIRECTORY_MEMBERS,
    SDIST_MEMBER_CONTENTS,
    SDIST_PREFIX,
    SOURCE_DATE_EPOCH,
    WHEEL_MEMBER_CONTENTS,
    WHEEL_RECORD_NAME,
)


MODULE_NAME = "test_support.canonical_archives"
MAX_COMPRESSED_BYTES = 4_194_304
MAX_MEMBERS = 128
MAX_MEMBER_BYTES = 1_048_576
MAX_EXPANDED_BYTES = 8_388_608
MAX_MEMBER_NAME_BYTES = 512
SETUP_CFG_NAME = "setup.cfg"
SETUP_CFG = b"[egg_info]\ntag_build =\ntag_date = 0\n"


def load_canonical_archives() -> ModuleType | None:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as error:
        if error.name != MODULE_NAME:
            raise
        return None


CANONICAL = load_canonical_archives()


def require_canonical(case: unittest.TestCase) -> Any:
    case.assertIsNotNone(CANONICAL, "canonical archive language is not implemented")
    return CANONICAL


def captured_error(
    case: unittest.TestCase,
    expected: type[BaseException] | tuple[type[BaseException], ...],
    callback: Callable[[], object],
) -> BaseException:
    with case.assertRaises(expected) as raised:
        callback()
    error = raised.exception
    case.assertIsNone(error.__cause__)
    case.assertIsNone(error.__context__)
    return error


def _zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    instant = datetime.fromtimestamp(epoch, timezone.utc)
    return (
        instant.year,
        instant.month,
        instant.day,
        instant.hour,
        instant.minute,
        instant.second - instant.second % 2,
    )


def _raw_deflate(payload: bytes) -> bytes:
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    return compressor.compress(payload) + compressor.flush()


def canonical_gzip(payload: bytes) -> bytes:
    return (
        b"\x1f\x8b\x08\x00"
        + struct.pack("<I", 0)
        + b"\x02\xff"
        + _raw_deflate(payload)
        + struct.pack("<II", zlib.crc32(payload), len(payload) & 0xFFFFFFFF)
    )


def canonical_sdist_members() -> dict[str, bytes]:
    return dict(SDIST_MEMBER_CONTENTS)


def raw_sdist_members() -> dict[str, bytes]:
    return {**SDIST_MEMBER_CONTENTS, SETUP_CFG_NAME: SETUP_CFG}


def _tar_bytes(
    members: dict[str, bytes],
    *,
    canonical: bool,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> bytes:
    output = io.BytesIO()
    archive_format = tarfile.USTAR_FORMAT if canonical else tarfile.PAX_FORMAT
    with tarfile.open(fileobj=output, mode="w", format=archive_format) as archive:
        directory_names = ("", *SDIST_DIRECTORY_MEMBERS)
        ordered_directories = directory_names if canonical else tuple(reversed(directory_names))
        for relative in ordered_directories:
            name = SDIST_PREFIX if not relative else f"{SDIST_PREFIX}/{relative}"
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            info.mode = 0o755 if canonical else 0o775
            info.uid = 0 if canonical else 41
            info.gid = 0 if canonical else 42
            info.uname = "" if canonical else "builder"
            info.gname = "" if canonical else "builder"
            info.mtime = source_date_epoch if canonical else source_date_epoch - 6
            archive.addfile(info)
        ordered_members = tuple(members.items())
        if not canonical:
            ordered_members = tuple(reversed(ordered_members))
        for relative, payload in ordered_members:
            info = tarfile.TarInfo(f"{SDIST_PREFIX}/{relative}")
            info.type = tarfile.REGTYPE
            info.mode = 0o755 if relative == "test.sh" else 0o644
            info.uid = 0 if canonical else 41
            info.gid = 0 if canonical else 42
            info.uname = "" if canonical else "builder"
            info.gname = "" if canonical else "builder"
            info.mtime = source_date_epoch if canonical else source_date_epoch - 6
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return output.getvalue()


def canonical_sdist_bytes(
    members: dict[str, bytes] | None = None,
    *,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> bytes:
    selected = canonical_sdist_members() if members is None else members
    return canonical_gzip(
        _tar_bytes(selected, canonical=True, source_date_epoch=source_date_epoch)
    )


def raw_sdist_bytes(
    members: dict[str, bytes] | None = None,
    *,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> bytes:
    selected = raw_sdist_members() if members is None else members
    payload = _tar_bytes(selected, canonical=False, source_date_epoch=source_date_epoch)
    compressor = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    return compressor.compress(payload) + compressor.flush()


def stage_one_accepted_noncanonical_sdist_bytes() -> bytes:
    payload = _tar_bytes(
        SDIST_MEMBER_CONTENTS,
        canonical=True,
        source_date_epoch=SOURCE_DATE_EPOCH,
    )
    compressor = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)
    return compressor.compress(payload) + compressor.flush()


def canonical_wheel_bytes(
    members: dict[str, bytes] | None = None,
    *,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> bytes:
    selected = WHEEL_MEMBER_CONTENTS if members is None else members
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, payload in selected.items():
            info = zipfile.ZipInfo(name, date_time=_zip_datetime(source_date_epoch))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, payload)
    return output.getvalue()


def raw_wheel_bytes(
    members: dict[str, bytes] | None = None,
    *,
    source_date_epoch: int = SOURCE_DATE_EPOCH,
) -> bytes:
    selected = WHEEL_MEMBER_CONTENTS if members is None else members
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in reversed(tuple(selected.items())):
            info = zipfile.ZipInfo(name, date_time=_zip_datetime(source_date_epoch - 4))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            archive.writestr(info, payload)
    return output.getvalue()


def stage_one_accepted_noncanonical_wheel_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in WHEEL_MEMBER_CONTENTS.items():
            info = zipfile.ZipInfo(name, date_time=_zip_datetime(SOURCE_DATE_EPOCH))
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, payload)
    return output.getvalue()


def sdist_payloads(encoded: bytes) -> tuple[tuple[str, bytes], ...]:
    with tarfile.open(fileobj=io.BytesIO(encoded), mode="r:gz") as archive:
        selected = []
        for member in archive.getmembers():
            if member.isfile():
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise AssertionError("regular fixture member was not readable")
                selected.append((member.name.split("/", 1)[1], extracted.read()))
        return tuple(selected)


def wheel_payloads(encoded: bytes) -> tuple[tuple[str, bytes], ...]:
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        return tuple((info.filename, archive.read(info)) for info in archive.infolist())


def wheel_record_is_consistent(encoded: bytes) -> bool:
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        names = tuple(archive.namelist())
        rows = tuple(
            line.split(",")
            for line in archive.read(WHEEL_RECORD_NAME).decode("utf-8").splitlines()
        )
        if len(rows) != len(names) or tuple(row[0] for row in rows) != names:
            return False
        for name, digest, size in rows[:-1]:
            payload = archive.read(name)
            encoded_digest = urlsafe_b64encode(sha256(payload).digest()).rstrip(b"=")
            if digest != f"sha256={encoded_digest.decode('ascii')}" or size != str(len(payload)):
                return False
        return rows[-1] == [WHEEL_RECORD_NAME, "", ""]


class HostileBytes(bytes):
    def __len__(self) -> int:
        raise RuntimeError("hostile bytes length dispatched")


class HostileInt(int):
    def __index__(self) -> int:
        raise RuntimeError("hostile integer index dispatched")
