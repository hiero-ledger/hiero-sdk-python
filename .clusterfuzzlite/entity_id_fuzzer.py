"""Atheris fuzz target: entity ID string parsing."""

from __future__ import annotations

import sys

import atheris


with atheris.instrument_imports():
    from hiero_sdk_python import AccountId, ContractId, FileId, TokenId, TopicId

_CLASSES = (AccountId, TokenId, ContractId, FileId, TopicId)


def _try_parse_entity_id(entity_id_class, text: str) -> None:
    try:
        entity_id_class.from_string(text)
    except (TypeError, ValueError, IndexError, OverflowError):
        # Expected errors from malformed string input (parsing, indexing, conversions)
        pass


def TestOneInput(data: bytes) -> None:
    """Feed arbitrary strings into entity ID parsers."""
    fdp = atheris.FuzzedDataProvider(data)
    text = fdp.ConsumeUnicodeNoSurrogates(256)

    for cls in _CLASSES:
        _try_parse_entity_id(cls, text)


atheris.Setup(sys.argv, TestOneInput)
atheris.Fuzz()
