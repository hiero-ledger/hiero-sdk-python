import time
import pytest
from unittest.mock import patch
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.hapi.services import basic_types_pb2, response_pb2
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services import transaction_get_receipt_pb2, response_header_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
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

# This test uses fixture mock_account_ids as parameter
def test_account_create_transaction_build_scheduled_body(mock_account_ids):
    """Test building a schedulable account create transaction body."""
    operator_id, node_account_id = mock_account_ids

    new_private_key = PrivateKey.generate()
    new_public_key = new_private_key.public_key()

    account_tx = (
        AccountCreateTransaction()
        .set_key(new_public_key)
        .set_initial_balance(200000000)
        .set_account_memo("Schedulable account")
        .set_receiver_signature_required(True)
    )
    account_tx.transaction_id = generate_transaction_id(operator_id)
    account_tx.node_account_id = node_account_id

    # Build the scheduled transaction body
    schedulable_body = account_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with account create type
    assert schedulable_body.HasField("cryptoCreateAccount")

    # Verify fields in the schedulable body
    expected_public_key_bytes = new_public_key.to_bytes_raw()
    assert schedulable_body.cryptoCreateAccount.key.ed25519 == expected_public_key_bytes
    assert schedulable_body.cryptoCreateAccount.initialBalance == 200000000
    assert schedulable_body.cryptoCreateAccount.memo == "Schedulable account"
    assert schedulable_body.cryptoCreateAccount.receiverSigRequired == True

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_account_create_transaction_sign(mock_account_ids, mock_client):
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
    account_tx.freeze_with(mock_client)

    # Add first signiture
    account_tx.sign(mock_client.operator_private_key)
    body_bytes = account_tx._transaction_body_bytes[node_account_id]
    
    assert body_bytes in account_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(account_tx._signature_map[body_bytes].sigPair) == 1, \
        "Transaction should have exactly one signature"
    
    # Add second signiture
    account_tx.sign(operator_private_key)
    body_bytes = account_tx._transaction_body_bytes[node_account_id]
    
    assert body_bytes in account_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(account_tx._signature_map[body_bytes].sigPair) == 2, \
        "Transaction should have exactly two signatures"

def test_account_create_transaction():
    """Integration test for AccountCreateTransaction with retry and response handling."""
    # Create test transaction responses
    busy_response = TransactionResponseProto()
    busy_response.nodeTransactionPrecheckCode = ResponseCode.BUSY
    
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK
    
    # Create a mock receipt for a successful account creation
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS,
        accountID=basic_types_pb2.AccountID(
            shardNum=0,
            realmNum=0,
            accountNum=1234
        )
    )
    
    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto
        )
    )
    
    response_sequences = [
        [ok_response, receipt_query_response],
    ]
    
    # Use the context manager to set up and tear down the mock environment
    with mock_hedera_servers(response_sequences) as client, \
         patch('time.sleep'):
        
        # Create the transaction
        new_key = PrivateKey.generate()
        transaction = (
            AccountCreateTransaction()
            .set_key(new_key.public_key())
            .set_initial_balance(100000000)  # 1 HBAR
        )
        
        # Execute the transaction and get receipt
        receipt = transaction.execute(client)
        
        # Verify the results
        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"
        assert receipt.account_id.num == 1234, "Should have created account with ID 1234"

def test_sign_account_create_without_freezing_raises_error(mock_account_ids):
    """Test that signing a transaction without freezing it first raises an error."""
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

    with pytest.raises(Exception, match="Transaction is not frozen"):
        account_tx.sign(new_private_key)

@pytest.fixture
def mock_account_ids():
    """Fixture to provide mock account IDs for testing."""
    operator_account_id = AccountId(0, 0, 1001)
    node_account_id = AccountId(0, 0, 3)
    return operator_account_id, node_account_id