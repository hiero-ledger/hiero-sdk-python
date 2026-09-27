"""
Unit tests for MirrorNodeAccountBalance.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_mirror_node_balance import (
    MirrorNodeAccountBalance,
)
from hiero_sdk_python.hbar import Hbar


def test_init_rejects_none():
    with pytest.raises(
        ValueError,
        match="hbars must be an instance of Hbar",
    ):
        MirrorNodeAccountBalance(None)


def test_init_rejects_non_hbar():
    with pytest.raises(
        ValueError,
        match="hbars must be an instance of Hbar",
    ):
        MirrorNodeAccountBalance(100)


def test_init_with_hbar_currently_raises_attribute_error():
    hbars = Hbar.from_tinybars(100)

    with pytest.raises(
        AttributeError,
        match=r"(property 'hbars'.*has no setter|can't set attribute 'hbars')",
    ):
        MirrorNodeAccountBalance(hbars)
