from unittest.mock import MagicMock
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_airdrop_transaction_cancel import TokenCancelAirdropTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
import pytest

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

def test_constructor_for_token_cancel_airdrop(mock_account_ids):
    """Test constructor of TokenCancelAirdropTransaction"""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id_2, 10)
    pending_airdrops = [
        PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1),
        PendingAirdropId(sender_id=sender, receiver_id=receiver, nft_id=nft_id)
    ]
    # Without any param
    cancel_airdrop_tx_1 = TokenCancelAirdropTransaction()
    assert cancel_airdrop_tx_1.pending_airdrops == []

    # With default list of pending airdrops id
    cancel_airdrop_tx_2 = TokenCancelAirdropTransaction(pending_airdrops=pending_airdrops)
    assert len(cancel_airdrop_tx_2.pending_airdrops) == 2
    assert cancel_airdrop_tx_2.pending_airdrops == pending_airdrops

def test_build_transaction_body(mock_account_ids):
    """Test building the token cancel airdrop transaction body with valid params."""
    sender_id, receiver_id, node_account_id, token_id_1, token_id_2 = mock_account_ids
    nft_id = NftId(token_id_2, 10)

    token_pending_airdrop = PendingAirdropId(sender_id=sender_id, receiver_id=receiver_id, token_id=token_id_1)
    nft_pending_airdrop = PendingAirdropId(sender_id=sender_id, receiver_id=receiver_id, nft_id=nft_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    cancel_airdrop_tx.add_pending_airdrop(token_pending_airdrop)
    cancel_airdrop_tx.add_pending_airdrop(nft_pending_airdrop)
    cancel_airdrop_tx.transaction_id = generate_transaction_id(sender_id)
    cancel_airdrop_tx.node_account_id = node_account_id
    transaction_body = cancel_airdrop_tx.build_transaction_body()

    assert len(transaction_body.tokenCancelAirdrop.pending_airdrops) == 2
    pending_airdrops = transaction_body.tokenCancelAirdrop.pending_airdrops

    assert pending_airdrops[0].sender_id.shardNum == sender_id.shard
    assert pending_airdrops[0].sender_id.realmNum == sender_id.realm
    assert pending_airdrops[0].sender_id.accountNum == sender_id.num
    assert pending_airdrops[0].receiver_id.shardNum == receiver_id.shard
    assert pending_airdrops[0].receiver_id.realmNum == receiver_id.realm
    assert pending_airdrops[0].receiver_id.accountNum == receiver_id.num
    assert pending_airdrops[0].fungible_token_type.shardNum == token_id_1.shard
    assert pending_airdrops[0].fungible_token_type.realmNum == token_id_1.realm
    assert pending_airdrops[0].fungible_token_type.tokenNum == token_id_1.num
    assert pending_airdrops[0].HasField("non_fungible_token") == False

    assert pending_airdrops[1].sender_id.shardNum == sender_id.shard
    assert pending_airdrops[1].sender_id.realmNum == sender_id.realm
    assert pending_airdrops[1].sender_id.accountNum == sender_id.num
    assert pending_airdrops[1].receiver_id.shardNum== receiver_id.shard
    assert pending_airdrops[1].receiver_id.realmNum == receiver_id.realm
    assert pending_airdrops[1].receiver_id.accountNum == receiver_id.num
    assert pending_airdrops[1].non_fungible_token.serial_number == 10
    assert pending_airdrops[1].non_fungible_token.token_ID.shardNum == token_id_2.shard
    assert pending_airdrops[1].non_fungible_token.token_ID.realmNum == token_id_2.realm
    assert pending_airdrops[1].non_fungible_token.token_ID.tokenNum == token_id_2.num
    assert pending_airdrops[1].HasField("fungible_token_type") == False

def test_transaction_for_invalid_params(mock_account_ids):
    """Test building the token cancel airdrop transaction body with invalid params."""
    sender_id, receiver_id, _, token_id, _ = mock_account_ids
    sample_pending_airdrop = PendingAirdropId(sender_id=sender_id, receiver_id=receiver_id, token_id=token_id)

    # With empty pending airdrops list
    cancel_airdrop_tx_1 = TokenCancelAirdropTransaction()
    with pytest.raises(ValueError, match="Pending airdrops list must contain mininum 1 and maximum 10 pendingAirdrop."):
        cancel_airdrop_tx_1.build_transaction_body()

    # With pending airdrops list containing more than 10 ids
    cancel_airdrop_tx_2 = TokenCancelAirdropTransaction()
    for _ in range(11):
        cancel_airdrop_tx_2.add_pending_airdrop(sample_pending_airdrop)
    with pytest.raises(ValueError, match="Pending airdrops list must contain mininum 1 and maximum 10 pendingAirdrop."):
        cancel_airdrop_tx_2.build_transaction_body()

def test_set_pending_airdrops(mock_account_ids):
    """Test set_pending_airdrops() method"""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_id = NftId(token_id_2, 10)
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, nft_id=nft_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    assert len(cancel_airdrop_tx.pending_airdrops) == 0

    cancel_airdrop_tx.set_pending_airdrops([token_pending_airdrop, nft_pending_airdrop])
    assert len(cancel_airdrop_tx.pending_airdrops) == 2
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.shard == sender.shard
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.realm == sender.realm
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.num == sender.num
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.shard == receiver.shard
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.realm == receiver.realm
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.num == receiver.num
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.shard == token_id_1.shard
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.realm == token_id_1.realm
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.num == token_id_1.num
    assert cancel_airdrop_tx.pending_airdrops[0].nft_id == None
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.shard == sender.shard
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.realm == sender.realm
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.num == sender.num
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.shard == receiver.shard
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.realm == receiver.realm
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.num == receiver.num
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.serial_number == 10
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.shard == token_id_2.shard
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.realm == token_id_2.realm
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.num == token_id_2.num
    assert cancel_airdrop_tx.pending_airdrops[1].token_id == None

def test_add_pending_airdrop(mock_account_ids):
    """Test add_pending_airdrop() method"""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_id = NftId(token_id_2, 10)
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, nft_id=nft_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    assert len(cancel_airdrop_tx.pending_airdrops) == 0

    cancel_airdrop_tx.add_pending_airdrop(pending_airdrop=token_pending_airdrop)
    cancel_airdrop_tx.add_pending_airdrop(pending_airdrop=nft_pending_airdrop)
    assert len(cancel_airdrop_tx.pending_airdrops) == 2
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.shard == sender.shard
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.realm == sender.realm
    assert cancel_airdrop_tx.pending_airdrops[0].sender_id.num == sender.num
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.shard == receiver.shard
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.realm == receiver.realm
    assert cancel_airdrop_tx.pending_airdrops[0].receiver_id.num == receiver.num
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.shard == token_id_1.shard
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.realm == token_id_1.realm
    assert cancel_airdrop_tx.pending_airdrops[0].token_id.num == token_id_1.num
    assert cancel_airdrop_tx.pending_airdrops[0].nft_id == None
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.shard == sender.shard
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.realm == sender.realm
    assert cancel_airdrop_tx.pending_airdrops[1].sender_id.num == sender.num
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.shard == receiver.shard
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.realm == receiver.realm
    assert cancel_airdrop_tx.pending_airdrops[1].receiver_id.num == receiver.num
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.serial_number == 10
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.shard == token_id_2.shard
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.realm == token_id_2.realm
    assert cancel_airdrop_tx.pending_airdrops[1].nft_id.token_id.num == token_id_2.num
    assert cancel_airdrop_tx.pending_airdrops[1].token_id == None

def test_clear_pending_airdrops(mock_account_ids):
    """Test clear_pending_airdrops() method"""
    sender, receiver, _, token_id_1, token_id_2 = mock_account_ids
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_id = NftId(token_id_2, 10)
    token_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id_1)
    nft_pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, nft_id=nft_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    assert len(cancel_airdrop_tx.pending_airdrops) == 0

    cancel_airdrop_tx.set_pending_airdrops([token_pending_airdrop, nft_pending_airdrop])
    assert len(cancel_airdrop_tx.pending_airdrops) == 2

    cancel_airdrop_tx.clear_pending_airdrops()
    assert len(cancel_airdrop_tx.pending_airdrops) == 0
    
def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token cancel airdrop transaction with a private key."""
    sender, receiver, _, token_id, _ = mock_account_ids
    pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    cancel_airdrop_tx.add_pending_airdrop(pending_airdrop)
    cancel_airdrop_tx.transaction_id = generate_transaction_id(sender)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    # Freeze the transaction
    cancel_airdrop_tx.freeze_with(mock_client)
    # Sign the transaction
    cancel_airdrop_tx.sign(private_key)
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = cancel_airdrop_tx._transaction_body_bytes[node_id]

    assert body_bytes in cancel_airdrop_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(cancel_airdrop_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = cancel_airdrop_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token cancel airdrop transaction to protobuf format after signing."""
    sender, receiver, _, token_id, _ = mock_account_ids
    pending_airdrop = PendingAirdropId(sender_id=sender, receiver_id=receiver, token_id=token_id)

    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    cancel_airdrop_tx.add_pending_airdrop(pending_airdrop)
    cancel_airdrop_tx.transaction_id = generate_transaction_id(sender)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    cancel_airdrop_tx.freeze_with(mock_client)
    cancel_airdrop_tx.sign(private_key)
    proto = cancel_airdrop_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token cancel airdrop transaction."""
    sender_id, receiver_id, _, token_id, token_id_2 = mock_account_ids
    
    token_pending_airdrop = PendingAirdropId(sender_id=sender_id, receiver_id=receiver_id, token_id=token_id)
    nft_pending_airdrop = PendingAirdropId(sender_id=sender_id, receiver_id=receiver_id, nft_id=NftId(token_id_2, 10))
    
    cancel_airdrop_tx = TokenCancelAirdropTransaction()
    cancel_airdrop_tx.add_pending_airdrop(token_pending_airdrop)
    cancel_airdrop_tx.add_pending_airdrop(nft_pending_airdrop)
    
    schedulable_body = cancel_airdrop_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenCancelAirdrop")
    assert len(schedulable_body.tokenCancelAirdrop.pending_airdrops) == 2
    
    # Verify the pending airdrop fields
    proto_pending_airdrop = schedulable_body.tokenCancelAirdrop.pending_airdrops[0]
    assert proto_pending_airdrop.sender_id == sender_id._to_proto()
    assert proto_pending_airdrop.receiver_id == receiver_id._to_proto()
    assert proto_pending_airdrop.fungible_token_type == token_id._to_proto()
    assert proto_pending_airdrop.HasField("non_fungible_token") == False

    proto_pending_airdrop = schedulable_body.tokenCancelAirdrop.pending_airdrops[1]
    assert proto_pending_airdrop.sender_id == sender_id._to_proto()
    assert proto_pending_airdrop.receiver_id == receiver_id._to_proto()
    assert proto_pending_airdrop.non_fungible_token.token_ID == token_id_2._to_proto()
    assert proto_pending_airdrop.non_fungible_token.serial_number == 10
    assert proto_pending_airdrop.HasField("fungible_token_type") == False