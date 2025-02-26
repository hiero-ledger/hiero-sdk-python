import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.transaction.transaction_id import TransactionId

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

    proto_account = freeze_id.to_proto()
    assert transaction_body.tokenFreeze.account == proto_account

def test_missing_token_id(mock_account_ids):
    """Test that building a transaction without setting TokenID raises a ValueError."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_account_id(freeze_id)
    with pytest.raises(ValueError, match="Missing required TokenID."):
        freeze_tx.build_transaction_body()

def test_missing_account_id(mock_account_ids):
    """Test that building a transaction without setting AccountID raises a ValueError."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids

    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    with pytest.raises(ValueError, match="Missing required AccountID."):
        freeze_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids):
    """Test signing the token freeze transaction with a freeze key."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids
    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)
    freeze_tx.transaction_id = generate_transaction_id(account_id)
    freeze_tx.node_account_id = node_account_id

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'public_key'

    freeze_tx.sign(freeze_key)

    assert len(freeze_tx.signature_map.sigPair) == 1
    sig_pair = freeze_tx.signature_map.sigPair[0]
    assert sig_pair.pubKeyPrefix == b'public_key'
    assert sig_pair.ed25519 == b'signature'

def test_to_proto(mock_account_ids):
    """Test converting the token freeze transaction to protobuf format after signing."""
    account_id, freeze_id, node_account_id, token_id, _= mock_account_ids
    freeze_tx = TokenFreezeTransaction()
    freeze_tx.set_token_id(token_id)
    freeze_tx.set_account_id(freeze_id)
    freeze_tx.transaction_id = generate_transaction_id(account_id)
    freeze_tx.node_account_id = node_account_id

    freeze_key = MagicMock()
    freeze_key.sign.return_value = b'signature'
    freeze_key.public_key().to_bytes_raw.return_value = b'public_key'

    freeze_tx.sign(freeze_key)
    proto = freeze_tx.to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
