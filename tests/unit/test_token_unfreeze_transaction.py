import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
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

def test_build_transaction_body(mock_account_ids):
    """Test building the token unfreeze transaction body with valid account ID and token ID."""

    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)
    unfreeze_tx.node_account_id = node_account_id
    transaction_body = unfreeze_tx.build_transaction_body()

    assert transaction_body.tokenUnfreeze.token.shardNum == 1
    assert transaction_body.tokenUnfreeze.token.realmNum == 1
    assert transaction_body.tokenUnfreeze.token.tokenNum == 1

    proto_account = freeze_id._to_proto()
    assert transaction_body.tokenUnfreeze.account == proto_account

def test_missing_token_id(mock_account_ids):
    """Test that building a transaction without setting 
    TokenID raises a ValueError."""

    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids


    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_account_id(freeze_id) 
    with pytest.raises(ValueError,match = "Missing required TokenID."):
        unfreeze_tx.build_transaction_body()

def test_missing_account_id(mock_account_ids):
    """Test that building a transaction without setting AccountID raises a ValueError."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    with pytest.raises(ValueError, match="Missing required AccountID."):
        unfreeze_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token unfreeze transaction with a freeze key."""
    account_id, freeze_id, _, token_id, _= mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    unfreeze_tx.freeze_with(mock_client)

    unfreeze_tx.sign(freeze_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = unfreeze_tx._transaction_body_bytes[node_id]

    assert len(unfreeze_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = unfreeze_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'
    assert sig_pair.ed25519 == b'signature'

def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token unfreeze transaction."""
    _, freeze_id, _, token_id, _ = mock_account_ids
    
    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    
    schedulable_body = unfreeze_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenUnfreeze")
    assert schedulable_body.tokenUnfreeze.token == token_id._to_proto()
    assert schedulable_body.tokenUnfreeze.account == freeze_id._to_proto()

def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token unfreeze transaction to protobuf format after signing."""
    account_id, freeze_id, _, token_id, _= mock_account_ids

    unfreeze_tx = TokenUnfreezeTransaction()
    unfreeze_tx.set_token_id(token_id)
    unfreeze_tx.set_account_id(freeze_id)
    unfreeze_tx.transaction_id = generate_transaction_id(account_id)

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'mock_pubkey'
    
    unfreeze_tx.freeze_with(mock_client)

    unfreeze_tx.sign(freeze_key)
    proto = unfreeze_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
