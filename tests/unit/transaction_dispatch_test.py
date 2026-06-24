from __future__ import annotations

import pytest

from hiero_sdk_python.transaction.transaction import _TRANSACTION_TYPE_MAP, Transaction


pytestmark = pytest.mark.unit


def test_transaction_type_map_is_module_level():
    """_TRANSACTION_TYPE_MAP must be a module-level constant, not inline."""
    import hiero_sdk_python.transaction.transaction as tx_module

    assert hasattr(tx_module, "_TRANSACTION_TYPE_MAP")
    assert isinstance(tx_module._TRANSACTION_TYPE_MAP, dict)


def test_transaction_type_map_contains_expected_keys():
    keys = set(_TRANSACTION_TYPE_MAP.keys())
    expected = {
        "cryptoCreateAccount",
        "cryptoTransfer",
        "tokenCreation",
        "consensusCreateTopic",
        "consensusUpdateTopic",
        "fileCreate",
        "contractCreateInstance",
        "util_prng",
        "tokenReject",
        "tokenClaimAirdrop",
        "tokenCancelAirdrop",
        "nodeCreate",
        "nodeUpdate",
        "nodeDelete",
        "atomic_batch",
    }
    assert expected.issubset(keys)


def test_unimplemented_types_map_to_none():
    assert _TRANSACTION_TYPE_MAP["cryptoAddLiveHash"] is None
    assert _TRANSACTION_TYPE_MAP["cryptoDeleteLiveHash"] is None
    assert _TRANSACTION_TYPE_MAP["systemDelete"] is None
    assert _TRANSACTION_TYPE_MAP["systemUndelete"] is None


def test_get_transaction_class_returns_none_for_unimplemented():
    assert Transaction._get_transaction_class("cryptoAddLiveHash") is None
    assert Transaction._get_transaction_class("cryptoDeleteLiveHash") is None


def test_get_transaction_class_returns_none_for_unknown_type():
    assert Transaction._get_transaction_class("unknownTransactionType") is None


@pytest.mark.parametrize(
    "tx_type,expected_class_name",
    [
        ("cryptoCreateAccount", "AccountCreateTransaction"),
        ("cryptoTransfer", "TransferTransaction"),
        ("tokenCreation", "TokenCreateTransaction"),
        ("consensusCreateTopic", "TopicCreateTransaction"),
        ("util_prng", "PrngTransaction"),
        ("tokenClaimAirdrop", "TokenClaimAirdropTransaction"),
        ("tokenCancelAirdrop", "TokenCancelAirdropTransaction"),
        ("tokenReject", "TokenRejectTransaction"),
        ("nodeDelete", "NodeDeleteTransaction"),
        ("atomic_batch", "BatchTransaction"),
    ],
)
def test_get_transaction_class_returns_correct_class(tx_type, expected_class_name):
    cls = Transaction._get_transaction_class(tx_type)
    assert cls is not None
    assert cls.__name__ == expected_class_name


def test_all_non_none_entries_importable():
    """Every non-None entry in _TRANSACTION_TYPE_MAP must be importable."""
    for tx_type, class_path in _TRANSACTION_TYPE_MAP.items():
        if class_path is None:
            continue
        cls = Transaction._get_transaction_class(tx_type)
        assert cls is not None, f"Failed to import class for '{tx_type}'"
        assert callable(cls), f"Class for '{tx_type}' is not callable"
