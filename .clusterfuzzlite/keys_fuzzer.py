"""Atheris fuzz target: PrivateKey and PublicKey parsing."""

from __future__ import annotations

import sys
import warnings

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import PrivateKey, PublicKey


def _quiet(fn, *args):
    """Call *fn* with *args*, suppressing UserWarning."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return fn(*args)


def TestOneInput(data: bytes) -> None:
    """Feed arbitrary bytes/strings into key parsers."""
    fdp = atheris.FuzzedDataProvider(data)
    choice = fdp.ConsumeIntInRange(0, 3)

    try:
        if choice == 0:
            text = fdp.ConsumeUnicodeNoSurrogates(256)
            _quiet(PrivateKey.from_string, text)
        elif choice == 1:
            raw = fdp.ConsumeBytes(128)
            _quiet(PrivateKey.from_bytes, raw)
        elif choice == 2:
            text = fdp.ConsumeUnicodeNoSurrogates(256)
            _quiet(PublicKey.from_string, text)
        else:
            raw = fdp.ConsumeBytes(128)
            _quiet(PublicKey.from_bytes, raw)
    except Exception:
        pass


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
