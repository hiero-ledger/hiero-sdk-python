import pytest
from unittest.mock import MagicMock, patch
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import basic_types_pb2, transaction_receipt_pb2, timestamp_pb2
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
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

def test_account_create_transaction_build(mock_account_ids):
    """Test building an account create transaction body with valid parameters."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    expected_public_key_bytes = new_public_key.to_bytes_raw()

    assert transaction_body.cryptoCreateAccount.key.ed25519 == expected_public_key_bytes
    assert transaction_body.cryptoCreateAccount.initialBalance == 100000000
    assert transaction_body.cryptoCreateAccount.memo == "Test account"

def test_account_create_transaction_sign(mock_account_ids):
    """Test signing the account create transaction."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()
    operator_private_key = PrivateKey.generate()

    account_tx = (
        AccountCreateTransaction()
        .set_key(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id
    account_tx.freeze_with(None)  
    account_tx.sign(operator_private_key)

    assert len(account_tx.signature_map.sigPair) == 1

def test_account_create_transaction_execute(mock_account_ids):
    """Test executing the account create transaction."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()
    operator_private_key = PrivateKey.generate()

    account_tx = (
        AccountCreateTransaction()
        .set_key(new_public_key)
        .set_initial_balance(100000000)
        .set_account_memo("Test account")
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    # Setup mock client
    mock_client = MagicMock(spec=Client)
    mock_client.operator_account_id = operator_id
    mock_client.operator_private_key = operator_private_key
    mock_client.max_attempts = 1
    mock_client.node_account_id = node_account_id

    # Mock the channel and method
    mock_channel = MagicMock()
    mock_client.channel = mock_channel

    # Create a proper TransactionResponseProto mock
    mock_response = MagicMock(spec=TransactionResponseProto)
    mock_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Mock the _execute method to avoid actual execution
    with patch.object(account_tx, '_execute') as mock_execute:
        from hiero_sdk_python.transaction.transaction_response import TransactionResponse
        # Setup the return value from _execute
        transaction_response = TransactionResponse()
        transaction_response.transaction_id = account_tx.transaction_id
        transaction_response.node_id = node_account_id
        # Mock hash value
        transaction_response.hash = b'mock_hash_value'
        mock_execute.return_value = transaction_response

        # Mock the get_receipt method
        mock_receipt_proto = transaction_receipt_pb2.TransactionReceipt(
            status=ResponseCode.SUCCESS,
            accountID=basic_types_pb2.AccountID(
                shardNum=0,
                realmNum=0,
                accountNum=1002
            )
        )
        mock_receipt = TransactionReceipt(mock_receipt_proto)
        
        # Patch the get_receipt method on TransactionResponse
        with patch.object(TransactionResponse, 'get_receipt', return_value=mock_receipt):
            # Execute the transaction
            receipt = account_tx.execute(mock_client)

    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.accountId.num == 1002
    print(f"Account creation successful. New Account ID: {receipt.accountId}")


@pytest.fixture
def mock_account_ids():
    """Fixture to provide mock account IDs for testing."""
    operator_account_id = AccountId(0, 0, 1001)
    node_account_id = AccountId(0, 0, 3)
    return operator_account_id, node_account_id
