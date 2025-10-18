"""
Unit tests for the AccountAllowanceApproveTransaction class.
"""

import pytest

from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.crypto_approve_allowance_pb2 import (
    CryptoApproveAllowanceTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit


@pytest.fixture
def account_allowance_transaction():
    """Fixture for an AccountAllowanceApproveTransaction object"""
    return AccountAllowanceApproveTransaction()


@pytest.fixture
def sample_accounts():
    """Fixture for sample account IDs"""
    return {
        "owner": AccountId(0, 0, 200),
        "spender": AccountId(0, 0, 300),
        "spender2": AccountId(0, 0, 400),
    }


@pytest.fixture
def sample_tokens():
    """Fixture for sample token IDs"""
    return {
        "token1": TokenId(0, 0, 100),
        "token2": TokenId(0, 0, 101),
    }


def test_account_allowance_transaction_initialization(account_allowance_transaction):
    """Test the initialization of the AccountAllowanceApproveTransaction class"""
    assert account_allowance_transaction.hbar_allowances == []
    assert account_allowance_transaction.token_allowances == []
    assert account_allowance_transaction.nft_allowances == []
    assert account_allowance_transaction._default_transaction_fee == Hbar(1).to_tinybars()


def test_approve_hbar_allowance(account_allowance_transaction, sample_accounts):
    """Test approving HBAR allowance"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]
    amount = Hbar(100)

    result = account_allowance_transaction.approve_hbar_allowance(owner, spender, amount)

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.hbar_allowances) == 1

    allowance = account_allowance_transaction.hbar_allowances[0]
    assert allowance.owner_account_id == owner
    assert allowance.spender_account_id == spender
    assert allowance.amount == amount.to_tinybars()


def test_approve_hbar_allowance_multiple(account_allowance_transaction, sample_accounts):
    """Test approving multiple HBAR allowances"""
    owner = sample_accounts["owner"]
    spender1 = sample_accounts["spender"]
    spender2 = sample_accounts["spender2"]

    account_allowance_transaction.approve_hbar_allowance(owner, spender1, Hbar(100))
    account_allowance_transaction.approve_hbar_allowance(owner, spender2, Hbar(200))

    assert len(account_allowance_transaction.hbar_allowances) == 2
    assert account_allowance_transaction.hbar_allowances[0].amount == Hbar(100).to_tinybars()
    assert account_allowance_transaction.hbar_allowances[1].amount == Hbar(200).to_tinybars()


def test_approve_token_allowance(account_allowance_transaction, sample_accounts, sample_tokens):
    """Test approving token allowance"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]
    amount = 1000

    result = account_allowance_transaction.approve_token_allowance(token_id, owner, spender, amount)

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.token_allowances) == 1

    allowance = account_allowance_transaction.token_allowances[0]
    assert allowance.token_id == token_id
    assert allowance.owner_account_id == owner
    assert allowance.spender_account_id == spender
    assert allowance.amount == amount


def test_approve_token_allowance_multiple(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test approving multiple token allowances"""
    token1 = sample_tokens["token1"]
    token2 = sample_tokens["token2"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    account_allowance_transaction.approve_token_allowance(token1, owner, spender, 1000)
    account_allowance_transaction.approve_token_allowance(token2, owner, spender, 2000)

    assert len(account_allowance_transaction.token_allowances) == 2
    assert account_allowance_transaction.token_allowances[0].amount == 1000
    assert account_allowance_transaction.token_allowances[1].amount == 2000


def test_approve_token_nft_allowance(account_allowance_transaction, sample_accounts, sample_tokens):
    """Test approving NFT allowance"""
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    result = account_allowance_transaction.approve_token_nft_allowance(nft_id, owner, spender)

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.nft_allowances) == 1

    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.token_id == token_id
    assert allowance.owner_account_id == owner
    assert allowance.spender_account_id == spender
    assert allowance.serial_numbers == [1]
    assert allowance.approved_for_all is False


def test_approve_token_nft_allowance_multiple_serials(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test approving NFT allowance with multiple serials"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    # Add first NFT
    nft_id1 = NftId(token_id, 1)
    account_allowance_transaction.approve_token_nft_allowance(nft_id1, owner, spender)

    # Add second NFT with same token and spender
    nft_id2 = NftId(token_id, 2)
    account_allowance_transaction.approve_token_nft_allowance(nft_id2, owner, spender)

    assert len(account_allowance_transaction.nft_allowances) == 1
    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.serial_numbers == [1, 2]


def test_approve_token_nft_allowance_all_serials(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test approving NFT allowance for all serials"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    result = account_allowance_transaction.approve_token_nft_allowance_all_serials(
        token_id, owner, spender
    )

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.nft_allowances) == 1

    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.token_id == token_id
    assert allowance.owner_account_id == owner
    assert allowance.spender_account_id == spender
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is True


def test_approve_token_nft_allowance_all_serials_existing(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test approving NFT allowance for all serials when allowance already exists"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    # First add a specific NFT
    nft_id = NftId(token_id, 1)
    account_allowance_transaction.approve_token_nft_allowance(nft_id, owner, spender)

    # Then approve all serials
    account_allowance_transaction.approve_token_nft_allowance_all_serials(token_id, owner, spender)

    assert len(account_allowance_transaction.nft_allowances) == 1
    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is True


def test_delete_token_nft_allowance_all_serials(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test deleting NFT allowance for all serials"""
    token_id = sample_tokens["token1"]
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    result = account_allowance_transaction.delete_token_nft_allowance_all_serials(
        token_id, owner, spender
    )

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.nft_allowances) == 1

    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.token_id == token_id
    assert allowance.owner_account_id == owner
    assert allowance.spender_account_id == spender
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is False


def test_add_all_token_nft_approval(account_allowance_transaction, sample_accounts, sample_tokens):
    """Test adding all token NFT approval"""
    token_id = sample_tokens["token1"]
    spender = sample_accounts["spender"]

    result = account_allowance_transaction.add_all_token_nft_approval(token_id, spender)

    assert result is account_allowance_transaction
    assert len(account_allowance_transaction.nft_allowances) == 1

    allowance = account_allowance_transaction.nft_allowances[0]
    assert allowance.token_id == token_id
    assert allowance.owner_account_id is None
    assert allowance.spender_account_id == spender
    assert allowance.serial_numbers == []
    assert allowance.approved_for_all is True


def test_build_proto_body_empty(account_allowance_transaction):
    """Test building protobuf body with no allowances"""
    proto_body = account_allowance_transaction._build_proto_body()

    assert isinstance(proto_body, CryptoApproveAllowanceTransactionBody)
    assert len(proto_body.cryptoAllowances) == 0
    assert len(proto_body.tokenAllowances) == 0
    assert len(proto_body.nftAllowances) == 0


def test_build_proto_body_with_allowances(
    account_allowance_transaction, sample_accounts, sample_tokens
):
    """Test building protobuf body with allowances"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)

    # Add all types of allowances
    account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(100))
    account_allowance_transaction.approve_token_allowance(token_id, owner, spender, 1000)
    account_allowance_transaction.approve_token_nft_allowance(nft_id, owner, spender)

    proto_body = account_allowance_transaction._build_proto_body()

    assert len(proto_body.cryptoAllowances) == 1
    assert len(proto_body.tokenAllowances) == 1
    assert len(proto_body.nftAllowances) == 1


def test_build_transaction_body(account_allowance_transaction, sample_accounts):
    """Test building transaction body"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    # Set up required transaction fields
    account_allowance_transaction.operator_account_id = owner
    account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(100))

    # Test the proto body building instead of full transaction body
    proto_body = account_allowance_transaction._build_proto_body()
    assert hasattr(proto_body, "cryptoAllowances")
    assert len(proto_body.cryptoAllowances) == 1


def test_build_scheduled_body(account_allowance_transaction, sample_accounts):
    """Test building scheduled transaction body"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(100))
    scheduled_body = account_allowance_transaction.build_scheduled_body()

    assert hasattr(scheduled_body, "cryptoApproveAllowance")
    assert scheduled_body.cryptoApproveAllowance is not None


def test_require_not_frozen(account_allowance_transaction, sample_accounts):
    """Test that methods require transaction not to be frozen"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]

    # Freeze the transaction by setting _transaction_body_bytes
    account_allowance_transaction._transaction_body_bytes = {"test": b"frozen"}

    # These should raise an error
    with pytest.raises(Exception, match="Transaction is immutable"):
        account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(100))

    with pytest.raises(Exception, match="Transaction is immutable"):
        account_allowance_transaction.approve_token_allowance(
            TokenId(0, 0, 100), owner, spender, 1000
        )

    with pytest.raises(Exception, match="Transaction is immutable"):
        account_allowance_transaction.approve_token_nft_allowance(
            NftId(TokenId(0, 0, 100), 1), owner, spender
        )


def test_mixed_allowance_types(account_allowance_transaction, sample_accounts, sample_tokens):
    """Test transaction with mixed allowance types"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]
    token_id = sample_tokens["token1"]
    nft_id = NftId(token_id, 1)

    # Add all types of allowances
    account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(100))
    account_allowance_transaction.approve_token_allowance(token_id, owner, spender, 1000)
    account_allowance_transaction.approve_token_nft_allowance(nft_id, owner, spender)
    account_allowance_transaction.approve_token_nft_allowance_all_serials(
        sample_tokens["token2"], owner, spender
    )

    # Verify all allowances are present
    assert len(account_allowance_transaction.hbar_allowances) == 1
    assert len(account_allowance_transaction.token_allowances) == 1
    assert len(account_allowance_transaction.nft_allowances) == 2

    # Verify protobuf body includes all allowances
    proto_body = account_allowance_transaction._build_proto_body()
    assert len(proto_body.cryptoAllowances) == 1
    assert len(proto_body.tokenAllowances) == 1
    assert len(proto_body.nftAllowances) == 2


def test_zero_amount_allowances(account_allowance_transaction, sample_accounts, sample_tokens):
    """Test allowances with zero amounts (for removal)"""
    owner = sample_accounts["owner"]
    spender = sample_accounts["spender"]
    token_id = sample_tokens["token1"]

    # Add zero amount allowances (for removal)
    account_allowance_transaction.approve_hbar_allowance(owner, spender, Hbar(0))
    account_allowance_transaction.approve_token_allowance(token_id, owner, spender, 0)

    assert len(account_allowance_transaction.hbar_allowances) == 1
    assert len(account_allowance_transaction.token_allowances) == 1
    assert account_allowance_transaction.hbar_allowances[0].amount == 0
    assert account_allowance_transaction.token_allowances[0].amount == 0
