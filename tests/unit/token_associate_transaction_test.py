import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
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
    """Test building the token associate transaction body with valid account ID and token IDs."""
    account_id, _, node_account_id, token_id_1, token_id_2 = mock_account_ids
    associate_tx = TokenAssociateTransaction()

    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.add_token_id(token_id_2)
    associate_tx.transaction_id = generate_transaction_id(account_id)
    associate_tx.node_account_id = node_account_id

    transaction_body = associate_tx.build_transaction_body()

    assert transaction_body.tokenAssociate.account.shardNum == account_id.shard
    assert transaction_body.tokenAssociate.account.realmNum == account_id.realm
    assert transaction_body.tokenAssociate.account.accountNum == account_id.num
    assert len(transaction_body.tokenAssociate.tokens) == 2
    assert transaction_body.tokenAssociate.tokens[0].tokenNum == token_id_1.num
    assert transaction_body.tokenAssociate.tokens[1].tokenNum == token_id_2.num


def test_missing_fields():
    """Test that building the transaction without account ID or token IDs raises a ValueError."""
    associate_tx = TokenAssociateTransaction()

    with pytest.raises(ValueError, match="Account ID and token IDs must be set."):
        associate_tx.build_transaction_body()

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token associate transaction with a private key."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.transaction_id = generate_transaction_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    # Freeze the transaction
    associate_tx.freeze_with(mock_client)
    
    # Sign the transaction
    associate_tx.sign(private_key)
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = associate_tx._transaction_body_bytes[node_id]

    assert body_bytes in associate_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(associate_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = associate_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token associate transaction to protobuf format after signing."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.transaction_id = generate_transaction_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    associate_tx.freeze_with(mock_client)

    associate_tx.sign(private_key)
    proto = associate_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token associate transaction."""
    account_id, _, _, token_id_1, token_id_2 = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.add_token_id(token_id_2)
    
    schedulable_body = associate_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenAssociate")
    assert schedulable_body.tokenAssociate.account == account_id._to_proto()
    assert len(schedulable_body.tokenAssociate.tokens) == 2
    assert schedulable_body.tokenAssociate.tokens[0] == token_id_1._to_proto()
    assert schedulable_body.tokenAssociate.tokens[1] == token_id_2._to_proto()
