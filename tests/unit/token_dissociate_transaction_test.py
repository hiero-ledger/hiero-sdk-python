import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
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

# This test uses fixture mock_account_ids as parameter
def test_build_transaction_body(mock_account_ids):
    """Test building the token dissociate transaction body with valid account ID and token ID."""
    account_id, _, node_account_id, token_id_1, _ = mock_account_ids

    dissociate_tx = TokenDissociateTransaction()
    dissociate_tx.set_account_id(account_id)
    dissociate_tx.add_token_id(token_id_1)
    dissociate_tx.transaction_id = generate_transaction_id(account_id)
    dissociate_tx.node_account_id = node_account_id

    transaction_body = dissociate_tx.build_transaction_body()

    assert transaction_body.tokenDissociate.account.shardNum == account_id.shard
    assert transaction_body.tokenDissociate.account.realmNum == account_id.realm
    assert transaction_body.tokenDissociate.account.accountNum == account_id.num

    assert len(transaction_body.tokenDissociate.tokens) == 1
    assert transaction_body.tokenDissociate.tokens[0].tokenNum == token_id_1.num

# This test uses fixture mock_account_ids as parameter
def test_transaction_body_with_multiple_tokens(mock_account_ids):
    """Test building the transaction body for dissociating multiple tokens."""
    account_id, operator_id, node_account_id, token_id_1, token_id_2 = mock_account_ids
    token_ids = [token_id_1, token_id_2]

    dissociate_tx = TokenDissociateTransaction()
    dissociate_tx.set_account_id(account_id)
    for token_id in token_ids:
        dissociate_tx.add_token_id(token_id)
    dissociate_tx.operator_account_id = operator_id 
    dissociate_tx.transaction_id = generate_transaction_id(account_id)
    dissociate_tx.node_account_id = node_account_id

    transaction_body = dissociate_tx.build_transaction_body()
    
    assert transaction_body.tokenDissociate.account.shardNum == account_id.shard
    assert transaction_body.tokenDissociate.account.realmNum == account_id.realm
    assert transaction_body.tokenDissociate.account.accountNum == account_id.num
    
    assert len(transaction_body.tokenDissociate.tokens) == len(token_ids)
    for i, token_id in enumerate(token_ids):
        assert transaction_body.tokenDissociate.tokens[i].tokenNum == token_id.num

def test_missing_fields():
    """Test that building the transaction without account ID or token IDs raises a ValueError."""
    dissociate_tx = TokenDissociateTransaction()

    with pytest.raises(ValueError, match="Account ID and token IDs must be set."):
        dissociate_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token dissociate transaction with a private key."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    dissociate_tx = TokenDissociateTransaction()
    dissociate_tx.set_account_id(account_id)
    dissociate_tx.add_token_id(token_id_1)
    dissociate_tx.transaction_id = generate_transaction_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    dissociate_tx.freeze_with(mock_client)

    dissociate_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = dissociate_tx._transaction_body_bytes[node_id]

    assert len(dissociate_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = dissociate_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token dissociate transaction to protobuf format after signing."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    dissociate_tx = TokenDissociateTransaction()
    dissociate_tx.set_account_id(account_id)
    dissociate_tx.add_token_id(token_id_1)
    dissociate_tx.transaction_id = generate_transaction_id(account_id)  
    
    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    dissociate_tx.freeze_with(mock_client)

    dissociate_tx.sign(private_key)
    proto = dissociate_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token dissociate transaction."""
    account_id, _, _, token_id_1, token_id_2 = mock_account_ids
    token_ids = [token_id_1, token_id_2]
    
    dissociate_tx = TokenDissociateTransaction()
    dissociate_tx.set_account_id(account_id)
    for token_id in token_ids:
        dissociate_tx.add_token_id(token_id)
    
    schedulable_body = dissociate_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenDissociate")
    assert schedulable_body.tokenDissociate.account == account_id._to_proto()
    assert len(schedulable_body.tokenDissociate.tokens) == len(token_ids)
    for i, token_id in enumerate(token_ids):
        assert schedulable_body.tokenDissociate.tokens[i] == token_id._to_proto()
