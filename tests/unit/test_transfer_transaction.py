import pytest
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.transaction.transaction import TransactionId
from hiero_sdk_python.hapi.services import timestamp_pb2

pytestmark = pytest.mark.unit

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    tx_id = TransactionId(
        valid_start=tx_timestamp,
        account_id=account_id_proto
    )
    return tx_id

def test_constructor_with_parameters(mock_account_ids):
    """Test constructor initialization with parameters."""
    account_id_sender, account_id_recipient, _, token_id_1, token_id_2 = mock_account_ids
    
    hbar_transfers = {
        account_id_sender: -1000,
        account_id_recipient: 1000
    }
    
    token_transfers = {
        token_id_1: {
            account_id_sender: -50,
            account_id_recipient: 50
        },
        token_id_2: {
            account_id_sender: -25,
            account_id_recipient: 25
        }
    }
    
    nft_transfers = {
        token_id_1: [
            (
                account_id_sender,
                account_id_recipient,
                1,
                True
            )
        ]
    }
    
    # Initialize with parameters
    transfer_tx = TransferTransaction(
        hbar_transfers=hbar_transfers,
        token_transfers=token_transfers,
        nft_transfers=nft_transfers
    )
    
    # Verify all transfers were added correctly
    assert transfer_tx.hbar_transfers[account_id_sender] == -1000
    assert transfer_tx.hbar_transfers[account_id_recipient] == 1000
    
    assert transfer_tx.token_transfers[token_id_1][account_id_sender] == -50
    assert transfer_tx.token_transfers[token_id_1][account_id_recipient] == 50
    assert transfer_tx.token_transfers[token_id_2][account_id_sender] == -25
    assert transfer_tx.token_transfers[token_id_2][account_id_recipient] == 25
    
    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved is True


# This test uses fixture mock_account_ids as parameter
def test_add_token_transfer(mock_account_ids):
    """Test adding token transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)

    token_transfers = transfer_tx.token_transfers[token_id_1][account_id_sender]
    assert token_transfers == -100
    token_transfers = transfer_tx.token_transfers[token_id_1][account_id_recipient]
    assert token_transfers == 100

# This test uses fixture mock_account_ids as parameter
def test_add_hbar_transfer(mock_account_ids):
    """Test adding HBAR transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)

    assert transfer_tx.hbar_transfers[account_id_sender] == -500
    assert transfer_tx.hbar_transfers[account_id_recipient] == 500

# This test uses fixture mock_account_ids as parameter
def test_add_nft_transfer(mock_account_ids):
    """Test adding NFT transfers and ensure amounts are correctly added."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()

    transfer_tx.add_nft_transfer(NftId(token_id_1, 0), account_id_sender, account_id_recipient, True)

    assert transfer_tx.nft_transfers[token_id_1][0].sender_id == account_id_sender
    assert transfer_tx.nft_transfers[token_id_1][0].receiver_id == account_id_recipient
    assert transfer_tx.nft_transfers[token_id_1][0].is_approved == True

# This test uses fixture mock_account_ids as parameter
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
        transfer_tx.add_nft_transfer(12345, mock_account_ids[0], mock_account_ids[1], True)

def test_accumulating_hbar_transfers(mock_account_ids):
    """Test accumulating multiple HBAR transfers for the same account."""
    account_id_sender, account_id_recipient, _, _, _ = mock_account_ids
    transfer_tx = TransferTransaction()
    
    # Add multiple transfers for the same accounts
    transfer_tx.add_hbar_transfer(account_id_sender, -200)
    transfer_tx.add_hbar_transfer(account_id_sender, -300)
    transfer_tx.add_hbar_transfer(account_id_recipient, 200)
    transfer_tx.add_hbar_transfer(account_id_recipient, 300)
    
    # Verify amounts accumulated correctly
    assert transfer_tx.hbar_transfers[account_id_sender] == -500
    assert transfer_tx.hbar_transfers[account_id_recipient] == 500

def test_accumulating_token_transfers(mock_account_ids):
    """Test accumulating multiple token transfers for the same account and token."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()
    
    # Add multiple transfers for the same token and accounts
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -30)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -70)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 30)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 70)
    
    # Verify amounts accumulated correctly
    assert transfer_tx.token_transfers[token_id_1][account_id_sender] == -100
    assert transfer_tx.token_transfers[token_id_1][account_id_recipient] == 100

def test_multiple_nft_transfers(mock_account_ids):
    """Test adding multiple NFT transfers for the same token."""
    account_id_sender, account_id_recipient, _, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()
    
    # Add multiple NFT transfers for the same token
    transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient, False)
    transfer_tx.add_nft_transfer(NftId(token_id_1, 2), account_id_sender, account_id_recipient, True)
    
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
        transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient)

def test_build_transaction_body(mock_account_ids):
    """Test building transaction body with various transfers."""
    account_id_sender, account_id_recipient, node_account_id, token_id_1, _ = mock_account_ids
    transfer_tx = TransferTransaction()
    
    # Add various transfers
    transfer_tx.add_hbar_transfer(account_id_sender, -500)
    transfer_tx.add_hbar_transfer(account_id_recipient, 500)
    transfer_tx.add_token_transfer(token_id_1, account_id_sender, -100)
    transfer_tx.add_token_transfer(token_id_1, account_id_recipient, 100)
    transfer_tx.add_nft_transfer(NftId(token_id_1, 1), account_id_sender, account_id_recipient)
    
    # Set required fields for building transaction
    transfer_tx.transaction_id = generate_transaction_id(account_id_sender)
    transfer_tx.node_account_id = node_account_id
    
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
    token_amounts = token_transfers[1].transfers
    assert len(token_amounts) == 2
    
    for transfer in token_amounts:
        if transfer.accountID.accountNum == account_id_sender.num:
            assert transfer.amount == -100
        elif transfer.accountID.accountNum == account_id_recipient.num:
            assert transfer.amount == 100
    
    # Verify NFT transfers
    nft_transfers = result.cryptoTransfer.tokenTransfers[0].nftTransfers
    assert len(nft_transfers) == 1
    assert nft_transfers[0].senderAccountID.accountNum == account_id_sender.num
    assert nft_transfers[0].receiverAccountID.accountNum == account_id_recipient.num
    assert nft_transfers[0].serialNumber == 1