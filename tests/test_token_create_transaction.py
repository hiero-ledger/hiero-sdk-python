import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2, transaction_pb2, transaction_body_pb2
from hiero_sdk_python.transaction.transaction_id import TransactionId
from cryptography.hazmat.primitives import serialization

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

def test_build_transaction_body_without_admin_key(mock_account_ids):
    """Test building a token creation transaction body without an admin key."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000
    assert not transaction_body.tokenCreation.HasField("adminKey")

def test_build_transaction_body(mock_account_ids):
    """Test building a token creation transaction body with valid values."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b'admin_signature'
    private_key_admin.public_key().to_bytes_raw.return_value = b'admin_public_key'

    private_key_freeze = MagicMock()
    private_key_freeze.sign.return_value = b'admin_signature'
    private_key_freeze.public_key().to_bytes_raw.return_value = b'admin_public_key'

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.set_supply_key(private_key_admin)
    token_tx.set_freeze_key(private_key_freeze)

    token_tx.node_account_id = node_account_id

    transaction_body = token_tx.build_transaction_body()

    assert transaction_body.tokenCreation.name == "MyToken"
    assert transaction_body.tokenCreation.symbol == "MTK"
    assert transaction_body.tokenCreation.decimals == 2
    assert transaction_body.tokenCreation.initialSupply == 1000
    assert transaction_body.tokenCreation.adminKey.ed25519 == b'admin_public_key'
    assert transaction_body.tokenCreation.supplyKey.ed25519 == b'admin_public_key'

    assert transaction_body.tokenCreation.freezeKey.ed25519 == b'admin_public_key'


def test_missing_fields():
    """Test that building a transaction without required fields raises a ValueError."""
    token_tx = TokenCreateTransaction()
    with pytest.raises(ValueError, match="Missing required fields"):
        token_tx.build_transaction_body()

def test_sign_transaction(mock_account_ids):
    """Test signing the token creation transaction with a private key."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b'admin_signature'
    private_key_admin.public_key().to_bytes_raw.return_value = b'admin_public_key'

    token_tx.sign(private_key)
    token_tx.sign(private_key_admin)

    assert len(token_tx.signature_map.sigPair) == 2

    sig_pair = token_tx.signature_map.sigPair[0]
    assert sig_pair.pubKeyPrefix == b'public_key' 
    assert sig_pair.ed25519 == b'signature'

    sig_pair_admin = token_tx.signature_map.sigPair[1]
    assert sig_pair_admin.pubKeyPrefix == b'admin_public_key'
    assert sig_pair_admin.ed25519 == b'admin_signature'

def test_to_proto_without_admin_key(mock_account_ids):
    """Test protobuf conversion when admin key is not set."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    token_tx.sign(private_key)
    proto = token_tx.to_proto()

    assert len(proto.signedTransactionBytes) > 0

    transaction = transaction_pb2.Transaction.FromString(proto.signedTransactionBytes)
    transaction_body = transaction_body_pb2.TransactionBody.FromString(transaction.bodyBytes)

    assert not transaction_body.tokenCreation.HasField("adminKey")

def test_to_proto(mock_account_ids):
    """Test converting the token creation transaction to protobuf format after signing."""
    treasury_account, _, node_account_id, _, _ = mock_account_ids

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    private_key_admin = MagicMock()
    private_key_admin.sign.return_value = b'admin_signature'
    private_key_admin.public_key().to_bytes_raw.return_value = b'admin_public_key'

    token_tx = TokenCreateTransaction()
    token_tx.set_token_name("MyToken")
    token_tx.set_token_symbol("MTK")
    token_tx.set_decimals(2)
    token_tx.set_initial_supply(1000)
    token_tx.set_treasury_account_id(treasury_account)
    token_tx.set_admin_key(private_key_admin)
    token_tx.transaction_id = generate_transaction_id(treasury_account)
    token_tx.node_account_id = node_account_id

    token_tx.sign(private_key)
    token_tx.sign(private_key_admin)
    proto = token_tx.to_proto()

    assert len(proto.signedTransactionBytes) > 0

    transaction = transaction_pb2.Transaction.FromString(proto.signedTransactionBytes)

    assert transaction.body.tokenCreation.adminKey.ed25519 == b'admin_public_key'
