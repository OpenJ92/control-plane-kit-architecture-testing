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
import warnings
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


def gzip_document(
    payload: bytes,
    *,
    level: int = 6,
    filename: bytes | None = None,
    comment: bytes | None = None,
    extra: bytes | None = None,
    reserved: bool = False,
) -> bytes:
    flags = 0x20 if reserved else 0
    optional = b""
    if extra is not None:
        flags |= 0x04
        optional += struct.pack("<H", len(extra)) + extra
    if filename is not None:
        flags |= 0x08
        optional += filename + b"\0"
    if comment is not None:
        flags |= 0x10
        optional += comment + b"\0"
    compressor = zlib.compressobj(level, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = compressor.compress(payload) + compressor.flush()
    return (
        b"\x1f\x8b\x08"
        + bytes((flags,))
        + struct.pack("<I", 0)
        + (b"\x02" if level == 9 else b"\x00")
        + b"\xff"
        + optional
        + compressed
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


def sdist_variant_bytes(
    *,
    setup_cfg: bytes = SETUP_CFG,
    reverse_members: bool = False,
    reverse_directories: bool = False,
    mtime_offset: int = 0,
    uid: int = 0,
    gid: int = 0,
    uname: str = "",
    gname: str = "",
    ordinary_modes: bool = False,
    gzip_filename: bytes | None = None,
    gzip_comment: bytes | None = None,
    gzip_extra: bytes | None = None,
    gzip_reserved: bool = False,
    archive_format: int = tarfile.USTAR_FORMAT,
    omit: str | None = None,
    extra_member: tuple[str, bytes] | None = None,
    duplicate: str | None = None,
    renamed: tuple[str, str] | None = None,
    member_type: tuple[str, bytes] | None = None,
    pax_member: str | None = None,
) -> bytes:
    entries = [
        (name, payload)
        for name, payload in ({**SDIST_MEMBER_CONTENTS, SETUP_CFG_NAME: setup_cfg}).items()
        if name != omit
    ]
    if renamed is not None:
        old, new = renamed
        entries = [(new if name == old else name, payload) for name, payload in entries]
    if extra_member is not None:
        entries.append(extra_member)
    if duplicate is not None:
        payload = next(payload for name, payload in entries if name == duplicate)
        entries.append((duplicate, payload))
    if reverse_members:
        entries.reverse()

    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=archive_format) as archive:
        directories = ["", *SDIST_DIRECTORY_MEMBERS]
        if reverse_directories:
            directories.reverse()
        for relative in directories:
            name = SDIST_PREFIX if not relative else f"{SDIST_PREFIX}/{relative}"
            info = tarfile.TarInfo(name)
            info.type = tarfile.DIRTYPE
            info.mode = 0o775 if ordinary_modes else 0o755
            info.uid = uid
            info.gid = gid
            info.uname = uname
            info.gname = gname
            info.mtime = SOURCE_DATE_EPOCH + mtime_offset
            archive.addfile(info)
        for relative, payload in entries:
            name = relative if relative.startswith("/") else f"{SDIST_PREFIX}/{relative}"
            info = tarfile.TarInfo(name)
            info.type = (
                member_type[1]
                if member_type is not None and relative == member_type[0]
                else tarfile.REGTYPE
            )
            info.mode = (
                0o700 if ordinary_modes and relative == "test.sh"
                else 0o600 if ordinary_modes
                else 0o755 if relative == "test.sh"
                else 0o644
            )
            info.uid = uid
            info.gid = gid
            info.uname = uname
            info.gname = gname
            info.mtime = SOURCE_DATE_EPOCH + mtime_offset
            if pax_member == relative:
                info.pax_headers = {"comment": "candidate"}
            if info.type == tarfile.REGTYPE:
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            else:
                info.size = 0
                info.linkname = "candidate"
                archive.addfile(info)
    return gzip_document(
        output.getvalue(),
        filename=gzip_filename,
        comment=gzip_comment,
        extra=gzip_extra,
        reserved=gzip_reserved,
    )


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


class _NonSeekableBytesIO(io.BytesIO):
    def seekable(self) -> bool:
        return False

    def seek(self, *args: object, **kwargs: object) -> int:
        raise io.UnsupportedOperation("not seekable")


def wheel_variant_bytes(
    *,
    reverse_members: bool = False,
    compression: int = zipfile.ZIP_STORED,
    mode: int = 0o644,
    epoch_offset: int = 0,
    comment: bytes = b"",
    omit: str | None = None,
    extra_member: tuple[str, bytes] | None = None,
    duplicate: str | None = None,
    renamed: tuple[str, str] | None = None,
    symlink: str | None = None,
    directory: str | None = None,
    nonseekable: bool = False,
    force_zip64: bool = False,
    members: dict[str, bytes] | None = None,
) -> bytes:
    selected = WHEEL_MEMBER_CONTENTS if members is None else members
    entries = [(name, payload) for name, payload in selected.items() if name != omit]
    if renamed is not None:
        old, new = renamed
        entries = [(new if name == old else name, payload) for name, payload in entries]
    if extra_member is not None:
        entries.append(extra_member)
    if duplicate is not None:
        payload = next(payload for name, payload in entries if name == duplicate)
        entries.append((duplicate, payload))
    if reverse_members:
        entries.reverse()
    output = _NonSeekableBytesIO() if nonseekable else io.BytesIO()
    with warnings.catch_warnings(), zipfile.ZipFile(
        output, "w", compression=compression, allowZip64=True
    ) as archive:
        warnings.filterwarnings("ignore", message="Duplicate name:", category=UserWarning)
        archive.comment = comment
        for index, (name, payload) in enumerate(entries):
            info = zipfile.ZipInfo(name, date_time=_zip_datetime(SOURCE_DATE_EPOCH + epoch_offset))
            info.create_system = 3
            info.compress_type = compression
            selected_mode = (
                stat.S_IFLNK | 0o777
                if name == symlink
                else stat.S_IFDIR | 0o755
                if name == directory
                else stat.S_IFREG | mode
            )
            info.external_attr = selected_mode << 16
            if force_zip64 and index == 0:
                with archive.open(info, "w", force_zip64=True) as destination:
                    destination.write(payload)
            else:
                archive.writestr(info, payload)
    return output.getvalue()


def _set_zip_flag(encoded: bytes, flag: int) -> bytes:
    candidate = bytearray(encoded)
    local = candidate.find(b"PK\x03\x04")
    central = candidate.find(b"PK\x01\x02")
    if local < 0 or central < 0:
        raise AssertionError("fixture ZIP headers are absent")
    struct.pack_into("<H", candidate, local + 6, struct.unpack_from("<H", candidate, local + 6)[0] | flag)
    struct.pack_into("<H", candidate, central + 8, struct.unpack_from("<H", candidate, central + 8)[0] | flag)
    return bytes(candidate)


def encrypted_wheel_bytes() -> bytes:
    return _set_zip_flag(wheel_variant_bytes(), 0x0001)


def declared_size_drift_wheel_bytes() -> bytes:
    candidate = bytearray(wheel_variant_bytes())
    local = candidate.find(b"PK\x03\x04")
    central = candidate.find(b"PK\x01\x02")
    local_size = struct.unpack_from("<I", candidate, local + 22)[0]
    central_size = struct.unpack_from("<I", candidate, central + 24)[0]
    struct.pack_into("<I", candidate, local + 22, local_size + 1)
    struct.pack_into("<I", candidate, central + 24, central_size + 1)
    return bytes(candidate)


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


def admitted_sdist_variants() -> tuple[tuple[str, bytes], ...]:
    setup_variants = (
        b"[egg_info]\ntag_date=0\ntag_build=\n",
        b"# generated\n[egg_info]\n tag_build = \n tag_date = 0\n",
        b"[egg_info]\n; generated\ntag_date : 0\ntag_build :\n",
    )
    return (
        ("base raw", sdist_variant_bytes()),
        ("member order", sdist_variant_bytes(reverse_members=True)),
        ("directory order", sdist_variant_bytes(reverse_directories=True)),
        ("mtime", sdist_variant_bytes(mtime_offset=-8)),
        (
            "owner names",
            sdist_variant_bytes(uid=41, gid=42, uname="builder", gname="builder"),
        ),
        ("ordinary modes", sdist_variant_bytes(ordinary_modes=True)),
        ("gzip FNAME", sdist_variant_bytes(gzip_filename=b"candidate.tar")),
        *(
            (f"setup formatting {index}", sdist_variant_bytes(setup_cfg=value))
            for index, value in enumerate(setup_variants)
        ),
    )


def invalid_sdist_variants() -> tuple[tuple[str, bytes], ...]:
    accepted = sdist_variant_bytes()
    trailer = bytearray(accepted)
    trailer[-8] ^= 0x01
    return (
        ("gzip reserved", sdist_variant_bytes(gzip_reserved=True)),
        ("gzip multistream", accepted + accepted),
        ("gzip extra", sdist_variant_bytes(gzip_extra=b"candidate")),
        ("gzip comment", sdist_variant_bytes(gzip_comment=b"candidate")),
        ("gzip trailer", bytes(trailer)),
        ("tar duplicate", sdist_variant_bytes(duplicate="AGENTS.md")),
        ("tar traversal", sdist_variant_bytes(renamed=("AGENTS.md", "../AGENTS.md"))),
        ("tar absolute", sdist_variant_bytes(renamed=("AGENTS.md", "/AGENTS.md"))),
        (
            "tar backslash",
            sdist_variant_bytes(renamed=("AGENTS.md", "candidate\\AGENTS.md")),
        ),
        (
            "tar nonascii",
            sdist_variant_bytes(renamed=("AGENTS.md", "candid\u00e1te.md")),
        ),
        ("tar fifo", sdist_variant_bytes(member_type=("AGENTS.md", tarfile.FIFOTYPE))),
        (
            "tar pax",
            sdist_variant_bytes(
                archive_format=tarfile.PAX_FORMAT,
                pax_member="AGENTS.md",
            ),
        ),
        ("tar gnu", sdist_variant_bytes(archive_format=tarfile.GNU_FORMAT)),
        ("tar link", sdist_variant_bytes(member_type=("AGENTS.md", tarfile.SYMTYPE))),
        ("tar device", sdist_variant_bytes(member_type=("AGENTS.md", tarfile.CHRTYPE))),
        ("tar unknown", sdist_variant_bytes(extra_member=("candidate", b""))),
        ("tar missing", sdist_variant_bytes(omit="AGENTS.md")),
        (
            "setup duplicate section",
            sdist_variant_bytes(setup_cfg=SETUP_CFG + b"[egg_info]\ntag_date=0\n"),
        ),
        (
            "setup duplicate option",
            sdist_variant_bytes(setup_cfg=SETUP_CFG + b"tag_date=0\n"),
        ),
        (
            "setup defaults",
            sdist_variant_bytes(setup_cfg=b"[DEFAULT]\ncandidate=x\n" + SETUP_CFG),
        ),
        (
            "setup interpolation",
            sdist_variant_bytes(
                setup_cfg=b"[egg_info]\ntag_build=%(candidate)s\ntag_date=0\n"
            ),
        ),
        (
            "setup unknown section",
            sdist_variant_bytes(setup_cfg=SETUP_CFG + b"[candidate]\nvalue=1\n"),
        ),
        (
            "setup unknown option",
            sdist_variant_bytes(setup_cfg=SETUP_CFG + b"candidate=1\n"),
        ),
    )


def admitted_wheel_variants() -> tuple[tuple[str, bytes], ...]:
    return (
        ("member order", wheel_variant_bytes(reverse_members=True)),
        ("stored", wheel_variant_bytes(compression=zipfile.ZIP_STORED)),
        ("deflated", wheel_variant_bytes(compression=zipfile.ZIP_DEFLATED)),
        ("ordinary mode", wheel_variant_bytes(mode=0o600)),
        ("timestamp", wheel_variant_bytes(epoch_offset=-4)),
    )


def invalid_wheel_variants() -> tuple[tuple[str, bytes], ...]:
    record_drift = dict(WHEEL_MEMBER_CONTENTS)
    record_drift[WHEEL_RECORD_NAME] = record_drift[WHEEL_RECORD_NAME].replace(
        b"sha256=", b"sha256=x", 1
    )
    return (
        (
            "duplicate",
            wheel_variant_bytes(
                duplicate="control_plane_kit_architecture_testing/py.typed"
            ),
        ),
        (
            "traversal",
            wheel_variant_bytes(
                renamed=("control_plane_kit_architecture_testing/py.typed", "../py.typed")
            ),
        ),
        (
            "absolute",
            wheel_variant_bytes(
                renamed=("control_plane_kit_architecture_testing/py.typed", "/py.typed")
            ),
        ),
        (
            "backslash",
            wheel_variant_bytes(
                renamed=(
                    "control_plane_kit_architecture_testing/py.typed",
                    "candidate\\py.typed",
                )
            ),
        ),
        (
            "directory",
            wheel_variant_bytes(directory="control_plane_kit_architecture_testing/py.typed"),
        ),
        (
            "symlink",
            wheel_variant_bytes(symlink="control_plane_kit_architecture_testing/py.typed"),
        ),
        ("extra", wheel_variant_bytes(extra_member=("candidate", b""))),
        ("comment", wheel_variant_bytes(comment=b"candidate")),
        ("encryption", encrypted_wheel_bytes()),
        ("data descriptor", wheel_variant_bytes(nonseekable=True)),
        ("ZIP64", wheel_variant_bytes(force_zip64=True)),
        ("unsupported compression", wheel_variant_bytes(compression=zipfile.ZIP_BZIP2)),
        ("RECORD", wheel_variant_bytes(members=record_drift)),
        ("declared size", declared_size_drift_wheel_bytes()),
    )
