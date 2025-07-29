import pytest

from unittest.mock import MagicMock
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.transaction.transaction_id import TransactionId

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

def test_build_transaction_body(mock_account_ids):
    """Test building the token airdrop transaction body"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender=sender, receiver=receiver)
    airdrop_tx.transaction_id = generate_transaction_id(sender)
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == 0
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == False
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == False
    
    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 0
    assert len(token_transfer_2.nftTransfers) == 1
    assert token_transfer_2.nftTransfers[0].serialNumber == serial_number
    assert token_transfer_2.nftTransfers[0].senderAccountID.accountNum == sender.num
    assert token_transfer_2.nftTransfers[0].receiverAccountID.accountNum == receiver.num
    assert token_transfer_2.nftTransfers[0].is_approval == False

def test_build_transaction_body_with_approved_transfer(mock_account_ids):
    """Test building the token airdrop transaction body with approved transfers"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_approved_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_approved_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_approved_nft_transfer(nft_id=nft_id, sender=sender, receiver=receiver)
    airdrop_tx.transaction_id = generate_transaction_id(sender)
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == 0
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == True
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == True
    
    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 0
    assert len(token_transfer_2.nftTransfers) == 1
    assert token_transfer_2.nftTransfers[0].serialNumber == serial_number
    assert token_transfer_2.nftTransfers[0].senderAccountID.accountNum == sender.num
    assert token_transfer_2.nftTransfers[0].receiverAccountID.accountNum == receiver.num
    assert token_transfer_2.nftTransfers[0].is_approval == True

def test_build_transaction_body_with_expected_decimal(mock_account_ids):
    """Test building the token airdrop transaction body with expected decimals"""
    sender, receiver, node_account_id, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    decimal = 1
    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer_with_decimals(token_id=token_id_1, account_id=sender, amount=-amount, decimals=decimal)
    airdrop_tx.add_token_transfer_with_decimals(token_id=token_id_1, account_id=receiver, amount=amount, decimals=decimal)
    airdrop_tx.add_approved_token_transfer_with_decimals(token_id=token_id_2, account_id=sender, amount=-amount, decimals=decimal)
    airdrop_tx.add_approved_token_transfer_with_decimals(token_id=token_id_2, account_id=receiver, amount=amount, decimals=decimal)
    airdrop_tx.transaction_id = generate_transaction_id(sender)
    airdrop_tx.node_account_id = node_account_id
    transaction_body = airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenAirdrop.token_transfers) == 2
    
    token_transfer_1 = transaction_body.tokenAirdrop.token_transfers[0]
    assert token_transfer_1.token.tokenNum == token_id_1.num
    assert token_transfer_1.expected_decimals.value == decimal
    assert len(token_transfer_1.transfers) == 2
    assert token_transfer_1.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_1.transfers[0].amount == -amount
    assert token_transfer_1.transfers[0].is_approval == False
    assert token_transfer_1.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_1.transfers[1].amount == amount
    assert token_transfer_1.transfers[1].is_approval == False

    token_transfer_2 = transaction_body.tokenAirdrop.token_transfers[1]
    assert token_transfer_2.token.tokenNum == token_id_2.num
    assert len(token_transfer_2.transfers) == 2
    assert token_transfer_2.expected_decimals.value == decimal
    assert token_transfer_2.transfers[0].accountID.accountNum== sender.num
    assert token_transfer_2.transfers[0].amount == -amount
    assert token_transfer_2.transfers[0].is_approval == True
    assert token_transfer_2.transfers[1].accountID.accountNum == receiver.num
    assert token_transfer_2.transfers[1].amount == amount
    assert token_transfer_2.transfers[1].is_approval == True

def test_add_zero_transfer_amount(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()

    with pytest.raises(ValueError):
        airdrop_tx.add_token_transfer(account_id, token_id, 0)

    with pytest.raises(ValueError):
        airdrop_tx.add_token_transfer_with_decimals(account_id, token_id, 0, 1)

    with pytest.raises(ValueError):
        airdrop_tx.add_approved_token_transfer(account_id, token_id, 0)
        
    with pytest.raises(ValueError):
        airdrop_tx.add_approved_token_transfer_with_decimals(account_id, token_id, 0, 1)

def test_add_unbalanced_transfer_amount(mock_account_ids):
    sender, receiver, _, token_id, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()
    airdrop_tx.add_token_transfer(sender, token_id, -1)
    airdrop_tx.add_token_transfer(receiver, token_id, -2)

    with pytest.raises(ValueError):
        airdrop_tx.build_transaction_body()

def test_add_invalid_transfer(mock_account_ids):
    _, _, _, _, _ = mock_account_ids
    airdrop_tx = TokenAirdropTransaction()

    with pytest.raises(ValueError):
        airdrop_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token airdrop transaction with a private key."""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender=sender, receiver=receiver)
    airdrop_tx.transaction_id = generate_transaction_id(sender)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    # Freeze the transaction
    airdrop_tx.freeze_with(mock_client)
    
    # Sign the transaction
    airdrop_tx.sign(private_key)
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = airdrop_tx._transaction_body_bytes[node_id]

    assert body_bytes in airdrop_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(airdrop_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = airdrop_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token airdrop transaction to protobuf format after signing."""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    amount = 1
    serial_number = 1

    nft_id = NftId(token_id_2, serial_number)

    airdrop_tx = TokenAirdropTransaction()

    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=sender, amount=-amount)
    airdrop_tx.add_token_transfer(token_id=token_id_1, account_id=receiver, amount=amount)
    airdrop_tx.add_nft_transfer(nft_id=nft_id, sender=sender, receiver=receiver)
    airdrop_tx.transaction_id = generate_transaction_id(sender)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    airdrop_tx.freeze_with(mock_client)

    airdrop_tx.sign(private_key)
    proto = airdrop_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0