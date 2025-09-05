import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
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
    """Test building a token freeze transaction body with a valid value."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)
    freeze_tx.transaction_id = generate_transaction_id(account_id)
    freeze_tx.node_account_id = node_account_id

    transaction_body = freeze_tx.build_transaction_body()

    assert transaction_body.tokenFreeze.token.shardNum == 1
    assert transaction_body.tokenFreeze.token.realmNum == 1
    assert transaction_body.tokenFreeze.token.tokenNum == 1

    proto_account = freeze_id._to_proto()
    assert transaction_body.tokenFreeze.account == proto_account

# This test uses fixture mock_account_ids as parameter
def test_missing_token_id(mock_account_ids):
    """Test that building a transaction without setting TokenID raises a ValueError."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_account_id(freeze_id)
    with pytest.raises(ValueError, match="Missing required TokenID."):
        freeze_tx.build_transaction_body()

# This test uses fixture mock_account_ids as parameter
def test_missing_account_id(mock_account_ids):
    """Test that building a transaction without setting AccountID raises a ValueError."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    with pytest.raises(ValueError, match="Missing required AccountID."):
        freeze_tx.build_transaction_body()

# This test uses fixtures (mock_account_id, mock_client) as parameters
def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token freeze transaction with a freeze key."""
    account_id, freeze_id, _, token_id, _= mock_account_ids
    
    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)
    freeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    freeze_tx.freeze_with(mock_client)

    freeze_tx.sign(freeze_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = freeze_tx._transaction_body_bytes[node_id]

    assert len(freeze_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = freeze_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b'public_key'
    assert sig_pair.ed25519 == b'signature'

# This test uses fixtures (mock_account_ids) as parameters
def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token freeze transaction to protobuf format after signing."""
    account_id, freeze_id, _, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)
    freeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    freeze_tx.freeze_with(mock_client)

    freeze_tx.sign(freeze_key)
    proto = freeze_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token freeze transaction."""
    _, freeze_id, _, token_id, _ = mock_account_ids
    
    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)

    schedulable_body = freeze_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenFreeze")
    assert schedulable_body.tokenFreeze.token == token_id._to_proto()
    assert schedulable_body.tokenFreeze.account == freeze_id._to_proto()
