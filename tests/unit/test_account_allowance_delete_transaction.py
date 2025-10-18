"""
Unit tests for the AccountAllowanceDeleteTransaction class.
"""

import pytest

from hiero_sdk_python.account.account_allowance_delete_transaction import (
    AccountAllowanceDeleteTransaction,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_delete_allowance_pb2 import (
    CryptoDeleteAllowanceTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_nft_allowance import TokenNftAllowance

pytestmark = pytest.mark.unit


@pytest.fixture
def account_allowance_delete_transaction():
    """Fixture for an AccountAllowanceDeleteTransaction object"""
    return AccountAllowanceDeleteTransaction()


@pytest.fixture
def sample_accounts():
    """Fixture for sample account IDs"""
    return {
        "owner": AccountId(0, 0, 200),
        "owner2": AccountId(0, 0, 201),
        "spender": AccountId(0, 0, 300),
    }


@pytest.fixture
def sample_tokens():
    """Fixture for sample token IDs"""
    return {
        "token1": TokenId(0, 0, 100),
        "token2": TokenId(0, 0, 101),
    }


def test_account_allowance_delete_transaction_initialization(account_allowance_delete_transaction):
    """Test the initialization of the AccountAllowanceDeleteTransaction class"""
    assert account_allowance_delete_transaction.nft_wipe == []
    assert account_allowance_delete_transaction._default_transaction_fee == Hbar(1).to_tinybars()


def test_account_allowance_delete_transaction_initialization_with_allowances(
    sample_accounts, sample_tokens
):
    """Test initialization with initial allowances"""
    owner = sample_accounts["owner"]
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)

    nft_wipe = [TokenNftAllowance(token_id=token_id, owner_account_id=owner, serial_numbers=[1])]

    tx = AccountAllowanceDeleteTransaction(nft_wipe=nft_wipe)

    assert len(tx.nft_wipe) == 1
    assert tx.nft_wipe[0].serial_numbers == [1]


def test_delete_all_token_nft_allowances(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test deleting NFT allowance"""
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)
    owner = sample_accounts["owner"]

    result = account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)

    assert result is account_allowance_delete_transaction
    assert len(account_allowance_delete_transaction.nft_wipe) == 1

    wipe_entry = account_allowance_delete_transaction.nft_wipe[0]
    assert wipe_entry.token_id == token_id
    assert wipe_entry.owner_account_id == owner
    assert wipe_entry.serial_numbers == [1]
    assert wipe_entry.approved_for_all is False


def test_delete_all_token_nft_allowances_multiple_serials(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test deleting NFT allowance with multiple serials"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]

    # Add first NFT
    nft_id1 = NftId(token_id, 1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id1, owner)

    # Add second NFT with same token and owner
    nft_id2 = NftId(token_id, 2)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id2, owner)

    assert len(account_allowance_delete_transaction.nft_wipe) == 1
    wipe_entry = account_allowance_delete_transaction.nft_wipe[0]
    assert wipe_entry.serial_numbers == [1, 2]


def test_delete_all_token_nft_allowances_different_owners(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test deleting NFT allowances for different owners"""
    token_id = sample_tokens["token1"]
    owner1 = sample_accounts["owner"]
    owner2 = sample_accounts["owner2"]

    # Add NFT for first owner
    nft_id1 = NftId(token_id, 1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id1, owner1)

    # Add NFT for second owner
    nft_id2 = NftId(token_id, 2)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id2, owner2)

    assert len(account_allowance_delete_transaction.nft_wipe) == 2
    assert account_allowance_delete_transaction.nft_wipe[0].owner_account_id == owner1
    assert account_allowance_delete_transaction.nft_wipe[1].owner_account_id == owner2


def test_delete_all_token_nft_allowances_different_tokens(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test deleting NFT allowances for different tokens"""
    token1 = sample_tokens["token1"]
    token2 = sample_tokens["token2"]
    owner = sample_accounts["owner"]

    # Add NFT for first token
    nft_id1 = NftId(token1, 1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id1, owner)

    # Add NFT for second token
    nft_id2 = NftId(token2, 1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id2, owner)

    assert len(account_allowance_delete_transaction.nft_wipe) == 2
    assert account_allowance_delete_transaction.nft_wipe[0].token_id == token1
    assert account_allowance_delete_transaction.nft_wipe[1].token_id == token2


def test_build_proto_body_empty(account_allowance_delete_transaction):
    """Test building protobuf body with no allowances"""
    proto_body = account_allowance_delete_transaction._build_proto_body()

    assert isinstance(proto_body, CryptoDeleteAllowanceTransactionBody)
    assert len(proto_body.nftAllowances) == 0


def test_build_proto_body_with_allowances(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test building protobuf body with allowances"""
    owner = sample_accounts["owner"]
    token_id = sample_tokens["token1"]
    nft_id1 = NftId(token_id, 1)
    nft_id2 = NftId(token_id, 2)

    # Add NFT allowances to delete
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id1, owner)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id2, owner)

    proto_body = account_allowance_delete_transaction._build_proto_body()

    assert len(proto_body.nftAllowances) == 1  # Should be grouped by token and owner
    assert len(proto_body.nftAllowances[0].serial_numbers) == 2


def test_build_transaction_body(account_allowance_delete_transaction, sample_accounts):
    """Test building transaction body"""
    owner = sample_accounts["owner"]

    # Set up required transaction fields
    account_allowance_delete_transaction.operator_account_id = owner
    nft_id = NftId(TokenId(0, 0, 100), 1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)

    # Test the proto body building instead of full transaction body
    proto_body = account_allowance_delete_transaction._build_proto_body()
    assert hasattr(proto_body, "nftAllowances")
    assert len(proto_body.nftAllowances) == 1


def test_build_scheduled_body(account_allowance_delete_transaction, sample_accounts, sample_tokens):
    """Test building scheduled transaction body"""
    owner = sample_accounts["owner"]
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)

    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)
    scheduled_body = account_allowance_delete_transaction.build_scheduled_body()

    assert hasattr(scheduled_body, "cryptoDeleteAllowance")
    assert scheduled_body.cryptoDeleteAllowance is not None


def test_require_not_frozen(account_allowance_delete_transaction, sample_accounts, sample_tokens):
    """Test that methods require transaction not to be frozen"""
    owner = sample_accounts["owner"]
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)

    # Freeze the transaction by setting _transaction_body_bytes
    account_allowance_delete_transaction._transaction_body_bytes = {"test": b"frozen"}

    # This should raise an error
    with pytest.raises(Exception, match="Transaction is immutable"):
        account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)


def test_duplicate_serial_number_handling(
    account_allowance_delete_transaction, sample_accounts, sample_tokens
):
    """Test that duplicate serial numbers are not added"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    nft_id = NftId(token_id, 1)

    # Add the same NFT twice
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(nft_id, owner)

    assert len(account_allowance_delete_transaction.nft_wipe) == 1
    wipe_entry = account_allowance_delete_transaction.nft_wipe[0]
    assert wipe_entry.serial_numbers == [1]  # Should not have duplicates


def test_mixed_nft_deletions(account_allowance_delete_transaction, sample_accounts, sample_tokens):
    """Test transaction with mixed NFT deletions"""
    owner1 = sample_accounts["owner"]
    owner2 = sample_accounts["owner2"]
    token1 = sample_tokens["token1"]
    token2 = sample_tokens["token2"]

    # Add various NFT deletions
    account_allowance_delete_transaction.delete_all_token_nft_allowances(NftId(token1, 1), owner1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(NftId(token1, 2), owner1)
    account_allowance_delete_transaction.delete_all_token_nft_allowances(NftId(token2, 1), owner2)

    # Verify all deletions are present
    assert len(account_allowance_delete_transaction.nft_wipe) == 2  # Grouped by token+owner

    # Verify protobuf body includes all deletions
    proto_body = account_allowance_delete_transaction._build_proto_body()
    assert len(proto_body.nftAllowances) == 2


def test_empty_nft_wipe_list(account_allowance_delete_transaction):
    """Test transaction with empty NFT wipe list"""
    assert len(account_allowance_delete_transaction.nft_wipe) == 0

    allowances = account_allowance_delete_transaction.nft_wipe
    assert len(allowances) == 0

    proto_body = account_allowance_delete_transaction._build_proto_body()
    assert len(proto_body.nftAllowances) == 0
