from __future__ import annotations

import sys

import atheris
from google.protobuf.message import DecodeError


with atheris.instrument_imports():
    from hiero_sdk_python import Transaction


EXPECTED_EXCEPTIONS = (DecodeError, TypeError, ValueError)


def TestOneInput(data: bytes) -> None:
    try:
        Transaction.from_bytes(data)
    except EXPECTED_EXCEPTIONS:
        return


def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
