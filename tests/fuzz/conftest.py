"""Shared Hypothesis setup, fixtures, and compatibility re-exports for fuzz tests."""

from __future__ import annotations

from tests.fuzz.support.classes import (
    AccountIdAliasCase,
    ContractValueCase,
    EntityIdCase,
    HbarConstructorCase,
    HbarStringCase,
    InvalidContractValueCase,
)
from tests.fuzz.support.profiles import load_hypothesis_profile
from tests.fuzz.support.registry import (
    FUZZ_STRATEGIES,
    fuzz_strategies_fixture,
    get_strategy,
    get_strategy_fixture,
)


load_hypothesis_profile()

__all__ = [
    "AccountIdAliasCase",
    "ContractValueCase",
    "EntityIdCase",
    "FUZZ_STRATEGIES",
    "HbarConstructorCase",
    "HbarStringCase",
    "InvalidContractValueCase",
    "fuzz_strategies_fixture",
    "get_strategy",
    "get_strategy_fixture",
]
