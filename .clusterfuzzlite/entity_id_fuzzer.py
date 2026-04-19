"""Atheris fuzz target: entity ID string parsing (AccountId, TokenId, ContractId)."""

from __future__ import annotations

import sys

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import AccountId, TokenId
    from hiero_sdk_python.contract.contract_id import ContractId

_CLASSES = (AccountId, TokenId, ContractId)


def TestOneInput(data: bytes) -> None:
    """Feed arbitrary strings into entity ID parsers."""
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(256)

    for cls in _CLASSES:
        try:
            cls.from_string(text)
        except Exception:  # noqa: PERF203
            pass


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
