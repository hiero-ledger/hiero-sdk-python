from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from hiero_sdk_python import HbarUnit


@dataclass(frozen=True)
class EntityIdCase:
    """A parsed entity ID expectation for public string parsers."""

    text: str
    shard: int
    realm: int
    value: int
    checksum: str | None = None


@dataclass(frozen=True)
class AccountIdAliasCase:
    """A valid account alias or EVM-address input."""

    text: str
    shard: int
    realm: int
    alias_hex: str | None = None
    evm_hex: str | None = None


@dataclass(frozen=True)
class HbarStringCase:
    """A valid public Hbar string and its exact tinybar value."""

    text: str
    tinybars: int


@dataclass(frozen=True)
class HbarConstructorCase:
    """A valid Hbar constructor input and its exact tinybar value."""

    amount: int | float | Decimal
    unit: HbarUnit
    tinybars: int


@dataclass(frozen=True)
class ContractValueCase:
    """A valid contract parameter case routed to an explicit public add_* method."""

    method_name: str
    value: Any


@dataclass(frozen=True)
class InvalidContractValueCase:
    """An invalid contract parameter case with a precise expected exception."""

    method_name: str
    value: Any
    expected_exception: type[BaseException]
