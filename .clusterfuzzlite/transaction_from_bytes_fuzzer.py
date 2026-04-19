"""Atheris fuzz target: Transaction.from_bytes deserialization."""

from __future__ import annotations

import sys

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import Transaction


def TestOneInput(data: bytes) -> None:
    """Feed arbitrary bytes into Transaction.from_bytes and re-serialise."""
    try:
        tx = Transaction.from_bytes(data)
        tx.to_bytes()
    except Exception:
        # All parsing / validation failures are expected; only unhandled
        # exceptions that escape this function are reported as fuzzer crashes.
        pass


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
