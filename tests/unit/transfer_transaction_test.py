"""
Unit tests for the TransferTransaction class
"""

import pytest

from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hbar_unit import HbarUnit
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

pytestmark = pytest.mark.unit


def test_constructor_with_parameters(mock_account_ids):
    """Test constructor initialization with parameters."""
    account_id_sender, account_id_recipient, _, token_id_1, token_id_2 = mock_account_ids

    hbar_transfers = {account_id_sender: -1000, account_id_recipient: 1000}

    token_transfers = {
        token_id_1: {account_id_sender: -50, account_id_recipient: 50},
        token_id_2: {account_id_sender: -25, account_id_recipient: 25},
    }

    nft_transfers = {token_id_1: [
        (account_id_sender, account_id_recipient, 1, True)]}

    # Initialize with parameters
    transfer_tx = TransferTransaction(
        hbar_transfers=hbar_transfers, token_transfers=token_transfers, nft_transfers=nft_transfers
    )

    # Verify all transfers were added correctly
    # Check HBAR transfers
    hbar_amounts = {
        transfer.account_id: transfer.amount for transfer in transfer_tx.hbar_transfers}
    assert hbar_amounts[account_id_sender] == -1000
    assert hbar_amounts[account_id_recipient] == 1000

    # Check token transfers
    token_amounts_1 = {
        transfer.account_id: transfer.amount for transfer in transfer_tx.token_transfers[token_id_1]
    }
    assert token_amounts_1[account_id_sender] == -50
    assert token_amounts_1[account_id_recipient] == 50

    token_amounts_2 = {
        transfer.account_id: transfer.amount for transfer in transfer_tx.token_transfers[token_id_2]
    }
    assert token_amounts_2[account_id_sender] == -25
    assert token_amounts_2[account_id_recipient] == 25

    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is True


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    transfer_tx = TransferTransaction()

    assert not transfer_tx.hbar_transfers
    assert not transfer_tx.token_transfers
    assert not transfer_tx.nft_transfers
    assert transfer_tx._default_transaction_fee == 100_000_000


def test_add_token_transfer(mock_account_ids):
    """Test adding token transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)

    # Find the transfers for each account
    sender_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.token_transfers[token_id_1] if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -100
    assert recipient_transfer.amount == 100


def test_add_hbar_transfer(mock_account_ids):
    """Test adding HBAR transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)

    # Find the transfers for each account
    sender_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -500
    assert recipient_transfer.amount == 500


def test_add_nft_transfer(mock_account_ids):
    """Test adding NFT transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 0), account_id_sender, account_id_recipient, True
    )

    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is True


def test_add_invalid_transfer(mock_account_ids):
    """Test adding invalid transfers raises the appropriate error."""
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError):
        transfer_tx.add_hbar_transfer(12345, -500)

    with pytest.raises(ValueError):
        transfer_tx.add_hbar_transfer(mock_account_ids[0], 0)

    with pytest.raises(TypeError):
        transfer_tx.add_token_transfer(12345, mock_account_ids[0], -100)

    with pytest.raises(TypeError):
        transfer_tx.add_nft_transfer(
            12345, mock_account_ids[0], mock_account_ids[1], True)


def test_hbar_accumulation(mock_account_ids):
    """Test that HBAR transfers accumulate for the same account."""
    account_id_1, account_id_2, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple transfers for the same account
    transfer_tx.add_hbar_transfer(account_id_1, 100)
    transfer_tx.add_hbar_transfer(account_id_1, 200)
    transfer_tx.add_hbar_transfer(account_id_2, 50)

    # Verify accumulation
    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 300  # 100 + 200
    assert amounts[account_id_2] == 50
    assert len(transfer_tx.hbar_transfers) == 2


def test_token_accumulation(mock_account_ids):
    """Test that token transfers accumulate for the same token and account."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple transfers for the same token and account
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 200)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 50)

    # Verify accumulation
    amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert amounts[account_id_1] == 300  # 100 + 200
    assert amounts[account_id_2] == 50
    assert len(transfer_tx.token_transfers[token_id_1]) == 2


def test_hbar_negative_amounts(mock_account_ids):
    """Test HBAR transfers with negative amounts (subtraction)."""
    account_id_1, account_id_2, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with positive amounts
    transfer_tx.add_hbar_transfer(account_id_1, 1000)
    transfer_tx.add_hbar_transfer(account_id_2, 500)

    # Add negative amounts (subtraction)
    transfer_tx.add_hbar_transfer(account_id_1, -200)
    transfer_tx.add_hbar_transfer(account_id_2, -100)

    # Verify subtraction
    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 800  # 1000 - 200
    assert amounts[account_id_2] == 400  # 500 - 100


def test_token_negative_amounts(mock_account_ids):
    """Test token transfers with negative amounts (subtraction)."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with positive amounts
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1000)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 500)

    # Add negative amounts (subtraction)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, -200)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, -100)

    # Verify subtraction
    amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert amounts[account_id_1] == 800  # 1000 - 200
    assert amounts[account_id_2] == 400  # 500 - 100


def test_zero_to_positive_transfers(mock_account_ids):
    """Test transfers that go from zero to positive."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Start with negative, then add to positive
    transfer_tx.add_hbar_transfer(account_id_1, -500)
    transfer_tx.add_hbar_transfer(account_id_1, 1000)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == 500

    # Same for tokens
    transfer_tx.add_token_transfer(token_id_1, account_id_1, -200)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 500)

    token_amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert token_amounts[account_id_1] == 300


def test_multiple_tokens_same_account(mock_account_ids):
    """Test multiple tokens for the same account."""
    account_id_1, _, _, token_id_1, token_id_2 = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add different amounts for different tokens to the same account
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 100)
    transfer_tx.add_token_transfer(token_id_2, account_id_1, 200)
    transfer_tx.add_token_transfer(
        token_id_1, account_id_1, 50)  # Accumulate token1
    transfer_tx.add_token_transfer(
        token_id_2, account_id_1, -50)  # Subtract from token2

    # Verify each token maintains separate balance
    token1_amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    token2_amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_2]}

    assert token1_amounts[account_id_1] == 150  # 100 + 50
    assert token2_amounts[account_id_1] == 150  # 200 - 50

    # Verify we have separate transfer objects for each token
    assert len(transfer_tx.token_transfers[token_id_1]) == 1
    assert len(transfer_tx.token_transfers[token_id_2]) == 1


def test_edge_case_amounts(mock_account_ids):
    """Test edge cases with very large and very small amounts."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test very large amounts
    large_amount = 2**63 - 1  # Max int64
    transfer_tx.add_hbar_transfer(account_id_1, large_amount)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_1] == large_amount

    # Test very large negative amounts
    large_negative = -(2**63)  # Min int64
    transfer_tx.add_hbar_transfer(account_id_2, large_negative)

    amounts = {t.account_id: t.amount for t in transfer_tx.hbar_transfers}
    assert amounts[account_id_2] == large_negative

    # Test small amounts
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1)
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 1)

    token1_amounts = {
        t.account_id: t.amount for t in transfer_tx.token_transfers[token_id_1]}
    assert token1_amounts[account_id_1] == 2


def test_zero_amount_validation(mock_account_ids):
    """Test that zero amounts are properly rejected."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test zero HBAR amount should raise ValueError with updated message
    with pytest.raises(ValueError, match="Amount must be a non-zero value"):
        transfer_tx.add_hbar_transfer(account_id_1, 0)

    # Test zero token amount should raise ValueError
    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_token_transfer(token_id_1, account_id_1, 0)


def test_multiple_nft_transfers(mock_account_ids):
    """Test adding multiple NFT transfers for the same token."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add multiple NFT transfers for the same token
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient, False
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 2), account_id_sender, account_id_recipient, True
    )

    # Verify all transfers were added correctly
    assert len(transfer_tx.nft_transfers[token_id_1]) == 2
    assert transfer_tx.nft_transfers[token_id_1][0].serial_number == 1
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is False
    assert transfer_tx.nft_transfers[token_id_1][1].serial_number == 2
    assert transfer_tx.nft_transfers[token_id_1][1].is_approved is True


def test_frozen_transaction(mock_account_ids, mock_client):
    """Test that operations fail when transaction is frozen."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Freeze the transaction
    transfer_tx.freeze_with(mock_client)

    # Test adding transfers
    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_hbar_transfer(account_id_sender, -100)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen."):
        transfer_tx.add_nft_transfer(
            NftId(token_id_1, 1), account_id_sender, account_id_recipient)


def test_build_transaction_body(mock_account_ids):
    """Test building transaction body with various transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add various transfers
    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient)

    # Set required fields for building transaction
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    # Build the transaction body
    result = transfer_tx.build_transaction_body()

    # Verify the transaction was built correctly
    assert result.HasField("cryptoTransfer")

    # Verify HBAR transfers
    hbar_transfers = result.cryptoTransfer.transfers.accountAmounts
    assert len(hbar_transfers) == 2

    # Check sender and recipient HBAR transfers
    for transfer in hbar_transfers:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -500
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 500

    # Verify token transfers
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 2

    # Check if token matches
    assert token_transfers[0].token == token_id_1._to_proto()
    assert token_transfers[1].token == token_id_1._to_proto()

    # Check token amounts
    token_amounts = token_transfers[0].transfers
    assert len(token_amounts) == 2

    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 100

    # Verify NFT transfers
    nft_transfers = result.cryptoTransfer.tokenTransfers[1].nftTransfers
    assert len(nft_transfers) == 1
    assert nft_transfers[0].senderAccountID.accountNum == account_id_sender.num
    assert nft_transfers[0].receiverAccountID.accountNum == account_id_recipient.num
    assert nft_transfers[0].serialNumber == 1


def test_build_scheduled_body(mock_account_ids):
    """Test building scheduled body with various transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add various transfers
    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient)

    # Build the scheduled body
    result = transfer_tx.build_scheduled_body()

    # Verify the scheduled body was built correctly
    assert result.HasField("cryptoTransfer")
    assert isinstance(result, SchedulableTransactionBody)

    # Verify HBAR transfers
    hbar_transfers = result.cryptoTransfer.transfers.accountAmounts
    assert len(hbar_transfers) == 2

    # Check sender and recipient HBAR transfers
    for transfer in hbar_transfers:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -500
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 500

    # Verify token transfers
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 2

    # Check if token matches
    assert token_transfers[0].token == token_id_1._to_proto()
    assert token_transfers[1].token == token_id_1._to_proto()

    # Check token amounts
    token_amounts = token_transfers[0].transfers
    assert len(token_amounts) == 2

    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 100

    # Verify NFT transfers
    nft_transfers = result.cryptoTransfer.tokenTransfers[1].nftTransfers
    assert len(nft_transfers) == 1
    assert nft_transfers[0].senderAccountID.accountNum == account_id_sender.num
    assert nft_transfers[0].receiverAccountID.accountNum == account_id_recipient.num
    assert nft_transfers[0].serialNumber == 1


def test_approved_token_transfer_with_decimals(mock_account_ids):
    """Test adding approved token transfers with decimals."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add approved token transfer with decimals
    transfer_tx.add_approved_token_transfer_with_decimals(
        token_id_1, account_id_1, 1000, 6)

    # Verify the transfer was added correctly
    transfer = transfer_tx.token_transfers[token_id_1][0]
    assert transfer.account_id == account_id_1
    assert transfer.amount == 1000
    assert transfer.expected_decimals == 6
    assert transfer.is_approved is True


def test_approved_token_transfer_accumulation(mock_account_ids):
    """Test that approved token transfers accumulate for the same account."""
    account_id_1, account_id_2, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Add initial transfers
    transfer_tx.add_token_transfer(token_id_1, account_id_1, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_2, 300)

    # Verify initial state
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    transfer_2 = transfer_tx.token_transfers[token_id_1][1]
    assert transfer_1.amount == 500
    assert transfer_1.is_approved is False
    assert transfer_1.expected_decimals is None
    assert transfer_2.amount == 300
    assert transfer_2.is_approved is False
    assert transfer_2.expected_decimals is None

    # Add approved transfer with decimals for account_1 (accumulates)
    transfer_tx.add_approved_token_transfer_with_decimals(
        token_id_1, account_id_1, 200, 8)

    # Verify accumulation
    transfer_1 = transfer_tx.token_transfers[token_id_1][0]
    transfer_2 = transfer_tx.token_transfers[token_id_1][1]
    assert transfer_1.amount == 700  # 500 + 200
    assert transfer_1.is_approved is False  # unchanged
    assert transfer_1.expected_decimals == 8  # updated from the accumulation
    assert transfer_2.amount == 300  # unchanged
    assert transfer_2.is_approved is False  # unchanged
    assert transfer_2.expected_decimals is None  # unchanged


def test_approved_token_transfer_validation(mock_account_ids):
    """Test validation for approved token transfers with decimals."""
    account_id_1, _, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    # Test invalid expected_decimals type
    with pytest.raises(TypeError, match="expected_decimals must be an integer"):
        transfer_tx.add_approved_token_transfer_with_decimals(
            token_id_1, account_id_1, 1000, "invalid"
        )

    # Test zero amount
    with pytest.raises(ValueError, match="Amount must be a non-zero integer"):
        transfer_tx.add_approved_token_transfer_with_decimals(
            token_id_1, account_id_1, 0, 6)


def test_add_hbar_transfer_with_hbar_object(mock_account_ids):
    """Test adding HBAR transfers with Hbar objects (covers Hbar normalization)."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_sender, Hbar(-500))
    transfer_tx.add_hbar_transfer(account_id_recipient, Hbar(500))

    sender_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -50_000_000_000
    assert recipient_transfer.amount == 50_000_000_000


def test_add_hbar_transfer_with_hbar_tinybars(mock_account_ids):
    """Test adding HBAR transfers with Hbar objects in TINYBAR units."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(
        account_id_sender, Hbar(-500, HbarUnit.TINYBAR))
    transfer_tx.add_hbar_transfer(
        account_id_recipient, Hbar(500, HbarUnit.TINYBAR))

    sender_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_sender
    )
    recipient_transfer = next(
        t for t in transfer_tx.hbar_transfers if t.account_id == account_id_recipient
    )

    assert sender_transfer.amount == -500
    assert recipient_transfer.amount == 500


def test_add_approved_hbar_transfer_with_hbar_object(mock_account_ids):
    """Test adding approved HBAR transfers with Hbar objects."""
    account_id_sender, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_approved_hbar_transfer(account_id_sender, Hbar(1000))

    transfer = transfer_tx.hbar_transfers[0]
    assert transfer.account_id == account_id_sender
    assert transfer.amount == 100_000_000_000
    assert transfer.is_approved is True


def test_hbar_accumulation_with_mixed_int_and_hbar(mock_account_ids):
    """Test that HBAR transfers accumulate correctly with mixed int and Hbar inputs."""
    account_id_1, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_1, 100)
    transfer_tx.add_hbar_transfer(account_id_1, Hbar(1))
    transfer_tx.add_hbar_transfer(account_id_1, -50)

    transfer = transfer_tx.hbar_transfers[0]
    assert transfer.amount == 100 + 100_000_000 - 50


def test_zero_hbar_value_validation(mock_account_ids):
    """Test that zero Hbar amounts are properly rejected."""
    account_id_1, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(ValueError, match="Amount must be a non-zero value"):
        transfer_tx.add_hbar_transfer(account_id_1, Hbar(0))

    with pytest.raises(ValueError, match="Amount must be a non-zero value"):
        transfer_tx.add_hbar_transfer(account_id_1, 0)


def test_add_hbar_transfer_with_various_hbar_units(mock_account_ids):
    """Test adding HBAR transfers with various Hbar units."""
    account_id_1, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_1, Hbar(1, HbarUnit.HBAR))
    transfer_tx.add_hbar_transfer(account_id_1, Hbar(1000, HbarUnit.MICROBAR))
    transfer_tx.add_hbar_transfer(account_id_1, Hbar(100, HbarUnit.MILLIBAR))

    transfer = transfer_tx.hbar_transfers[0]
    assert transfer.amount == 100_000_000 + 100_000 + 10_000_000


def test_invalid_amount_type_hbar_transfer(mock_account_ids):
    """Test that invalid amount types raise TypeError (covers type checking)."""
    account_id_1, _, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    with pytest.raises(TypeError, match="amount must be an int or Hbar instance"):
        transfer_tx.add_hbar_transfer(account_id_1, "invalid")

    with pytest.raises(TypeError, match="amount must be an int or Hbar instance"):
        transfer_tx.add_hbar_transfer(account_id_1, 123.45)


def test_token_transfer_with_expected_decimals_building(mock_account_ids):
    """Test token transfer with expected_decimals is properly built in transaction body."""
    account_id_1, account_id_2, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_1, -100, 8)
    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_2, 100, 8)
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_1

    result = transfer_tx.build_transaction_body()

    assert result.HasField("cryptoTransfer")
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 1
    assert token_transfers[0].token == token_id_1._to_proto()

    token_amounts = token_transfers[0].transfers
    assert len(token_amounts) == 2
    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_1.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_2.num:
            assert transfer.amount == 100


def test_nft_transfer_with_approval_building(mock_account_ids):
    """Test NFT transfers with approval flag are properly built."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient, False
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 2), account_id_sender, account_id_recipient, True
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    result = transfer_tx.build_transaction_body()

    assert result.HasField("cryptoTransfer")
    token_transfers = result.cryptoTransfer.tokenTransfers
    assert len(token_transfers) == 1

    nft_transfers = token_transfers[0].nftTransfers
    assert len(nft_transfers) == 2

    assert nft_transfers[0].serialNumber == 1
    assert nft_transfers[0].is_approval is False
    assert nft_transfers[1].serialNumber == 2
    assert nft_transfers[1].is_approval is True


def test_nft_transfer_reconstruction_from_protobuf(mock_account_ids):
    """Test NFT transfer reconstruction from protobuf preserves all fields."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 5), account_id_sender, account_id_recipient, True
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    assert len(reconstructed.nft_transfers[token_id_1]) == 1
    nft = reconstructed.nft_transfers[token_id_1][0]
    assert nft.token_id == token_id_1
    assert nft.sender_id == account_id_sender
    assert nft.receiver_id == account_id_recipient
    assert nft.serial_number == 5
    assert nft.is_approved is True


def test_nft_transfers_unapproved_reconstruction(mock_account_ids):
    """Test NFT transfer reconstruction with is_approved=False."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 10), account_id_sender, account_id_recipient, False
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    assert len(reconstructed.nft_transfers[token_id_1]) == 1
    nft = reconstructed.nft_transfers[token_id_1][0]
    assert nft.is_approved is False


def test_token_transfer_with_expected_decimals_reconstruction(mock_account_ids):
    """Test token transfer with expected_decimals reconstruction from protobuf."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_sender, -100, 6
    )
    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_recipient, 100, 6
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    assert len(reconstructed.token_transfers[token_id_1]) == 2
    for token_transfer in reconstructed.token_transfers[token_id_1]:
        assert token_transfer.expected_decimals == 6
        if token_transfer.account_id == account_id_sender:
            assert token_transfer.amount == -100
        elif token_transfer.account_id == account_id_recipient:
            assert token_transfer.amount == 100


def test_combined_transfers_reconstruction(mock_account_ids):
    """Test reconstruction of transaction with HBAR, token, and NFT transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_sender, -1000)
    transfer_tx.add_hbar_transfer(account_id_recipient, 1000)
    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_sender, -50, 8
    )
    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_recipient, 50, 8
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 1), account_id_sender, account_id_recipient, True
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    assert len(reconstructed.hbar_transfers) == 2
    assert len(reconstructed.token_transfers[token_id_1]) == 2
    assert len(reconstructed.nft_transfers[token_id_1]) == 1

    nft = reconstructed.nft_transfers[token_id_1][0]
    assert nft.sender_id == account_id_sender
    assert nft.receiver_id == account_id_recipient
    assert nft.serial_number == 1
    assert nft.is_approved is True


def test_expected_decimals_field_preservation(mock_account_ids):
    """Test that expected_decimals field is properly preserved during protobuf round-trip."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_sender, -200, 8
    )
    transfer_tx.add_token_transfer_with_decimals(
        token_id_1, account_id_recipient, 200, 8
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    for token_transfer in reconstructed.token_transfers[token_id_1]:
        assert token_transfer.expected_decimals is not None
        assert token_transfer.expected_decimals == 8
        assert isinstance(token_transfer.expected_decimals, int)


def test_nft_transfer_fields_preservation(mock_account_ids):
    """Test that all NFT transfer fields are preserved during protobuf round-trip."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 42), account_id_sender, account_id_recipient, True
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    nft_transfers = reconstructed.nft_transfers[token_id_1]
    assert len(nft_transfers) == 1

    nft = nft_transfers[0]
    assert nft.token_id == token_id_1
    assert nft.sender_id == account_id_sender
    assert nft.receiver_id == account_id_recipient
    assert nft.serial_number == 42
    assert nft.is_approved is True


def test_multiple_nft_transfers_all_fields(mock_account_ids):
    """Test that multiple NFT transfers with varying is_approved values are preserved."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 100), account_id_sender, account_id_recipient, True
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 101), account_id_sender, account_id_recipient, False
    )
    transfer_tx.add_nft_transfer(
        NftId(token_id_1, 102), account_id_sender, account_id_recipient, True
    )
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    nft_transfers = reconstructed.nft_transfers[token_id_1]
    assert len(nft_transfers) == 3

    serial_to_approval = {
        nft.serial_number: nft.is_approved for nft in nft_transfers}
    assert serial_to_approval[100] is True
    assert serial_to_approval[101] is False
    assert serial_to_approval[102] is True

    for nft in nft_transfers:
        assert nft.token_id == token_id_1
        assert nft.sender_id == account_id_sender
        assert nft.receiver_id == account_id_recipient


def test_token_transfer_without_expected_decimals(mock_account_ids):
    """Test token transfer reconstruction when expected_decimals is not set."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -300)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 300)
    transfer_tx.node_account_id = node_account_id
    transfer_tx.operator_account_id = account_id_sender

    body = transfer_tx.build_transaction_body()
    body_bytes = body.SerializeToString()

    reconstructed = TransferTransaction._from_protobuf(body, body_bytes, None)

    token_transfers = reconstructed.token_transfers[token_id_1]
    assert len(token_transfers) == 2

    for token_transfer in token_transfers:
        assert token_transfer.expected_decimals is None
        if token_transfer.account_id == account_id_sender:
            assert token_transfer.amount == -300
        elif token_transfer.account_id == account_id_recipient:
            assert token_transfer.amount == 300
