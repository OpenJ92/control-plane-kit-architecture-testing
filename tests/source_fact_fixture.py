from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any, Callable
import unittest


MODULE_NAME = "control_plane_kit_architecture_testing.python_source"


def load_language() -> ModuleType | None:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as error:
        if error.name != MODULE_NAME:
            raise
        return None


LANGUAGE = load_language()


def require_language(case: unittest.TestCase) -> Any:
    case.assertIsNotNone(
        LANGUAGE,
        "immutable Python source facts are not implemented",
    )
    return LANGUAGE


def forge(exact_type: type, **fields: object) -> object:
    value = object.__new__(exact_type)
    for name, field_value in fields.items():
        object.__setattr__(value, name, field_value)
    return value


def captured_error(
    case: unittest.TestCase,
    expected: type[BaseException],
    callback: Callable[[], object],
) -> BaseException:
    with case.assertRaises(expected) as raised:
        callback()
    error = raised.exception
    case.assertIsNone(error.__cause__)
    case.assertIsNone(error.__context__)
    return error


class HostileStr(str):
    def encode(self, *args: object, **kwargs: object) -> bytes:
        raise RuntimeError("hostile string encode dispatched")

    def isidentifier(self) -> bool:
        raise RuntimeError("hostile string identifier dispatched")

    def __len__(self) -> int:
        raise RuntimeError("hostile string length dispatched")


class HostileInt(int):
    def __index__(self) -> int:
        raise RuntimeError("hostile integer index dispatched")


class HostileTuple(tuple):
    def __iter__(self):
        raise RuntimeError("hostile tuple iteration dispatched")
