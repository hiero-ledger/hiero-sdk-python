import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.query.transaction_get_receipt_query import (
    TransactionGetReceiptQuery,
)
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from tests.integration.utils import env


def create_transaction():
    """Create a minimal valid AccountCreateTransaction for integration tests."""
    return (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate())
        .set_initial_balance(1)
    )


@pytest.mark.integration
def test_execute_waits_for_receipt_receipt(env):
    """Test execute return TransactionReceipt when wait_for_receipt is True (default)."""
    tx = create_transaction()
    # Default value for wait_for_receipt = True
    receipt = tx.execute(env.client)
    assert isinstance(receipt, TransactionReceipt)
    assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.integration
def test_execute_without_wait_returns_transaction_response(env):
    """Test execute return TransactionResponse when wait_for_receipt is False."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)
    assert not isinstance(response, TransactionReceipt)

    assert response.transaction is tx
    assert response.transaction_id == tx.transaction_id
    assert response.validate_status is True


@pytest.mark.integration
def test_transaction_response_get_receipt(env):
    """Test transaction response return receipt for transaction response."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)
    assert response.transaction is tx

    receipt = response.get_receipt(env.client)
    assert isinstance(receipt, TransactionReceipt)
    assert receipt.transaction_id == tx.transaction_id
    assert receipt.account_id is not None
    assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.integration
def test_transaction_response_get_receipt_via_query(env):
    """Test transaction response return receipt query for transaction response."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)
    assert response.transaction is tx

    query = response.get_receipt_query()
    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.transaction_id == tx.transaction_id
    assert len(query.node_account_ids) == 1
    assert query.node_account_ids[0] == response.node_id

    receipt = query.execute(env.client)
    assert isinstance(receipt, TransactionReceipt)
    assert receipt.transaction_id == tx.transaction_id
    assert receipt.account_id is not None
    assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.integration
def test_get_receipt_vs_query_returns_same_receipt(env):
    """Verify that get_receipt and execute via get_receipt_query return the same result."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)

    # Get receipt via TransactionResponse method
    receipt_via_response = response.get_receipt(env.client)
    assert isinstance(receipt_via_response, TransactionReceipt)

    # Get receipt via the query returned by get_receipt_query
    query = response.get_receipt_query()
    receipt_via_query = query.execute(env.client)
    assert isinstance(receipt_via_query, TransactionReceipt)

    assert receipt_via_response.transaction_id == receipt_via_query.transaction_id
    assert receipt_via_response.status == receipt_via_query.status
    assert receipt_via_response.account_id == receipt_via_query.account_id


@pytest.mark.integration
def test_transaction_response_get_record(env):
    """Test transaction response return record for transaction response."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)
    assert response.transaction is tx

    record = response.get_record(env.client)
    assert isinstance(record, TransactionRecord)
    assert record.transaction_id == tx.transaction_id
    assert record.transaction_hash is not None


@pytest.mark.integration
def test_transaction_response_get_record_via_query(env):
    """Test transaction response return record query for transaction response."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)
    assert response.transaction is tx

    query = response.get_record_query()
    assert isinstance(query, TransactionRecordQuery)
    assert query.transaction_id == tx.transaction_id
    assert len(query.node_account_ids) == 1
    assert query.node_account_ids[0] == response.node_id

    record = query.execute(env.client)
    assert isinstance(record, TransactionRecord)
    assert record.transaction_id == tx.transaction_id
    assert record.transaction_hash is not None


@pytest.mark.integration
def test_get_record_vs_query_returns_same_record(env):
    """Verify that get_record and execute via get_record_query return the same result."""
    tx = create_transaction()
    response = tx.execute(env.client, wait_for_receipt=False)

    assert isinstance(response, TransactionResponse)

    # Get record via TransactionResponse method
    record_via_response = response.get_record(env.client)
    assert isinstance(record_via_response, TransactionRecord)

    # Get record via the query returned by get_record_query
    query = response.get_record_query()
    record_via_query = query.execute(env.client)
    assert isinstance(record_via_query, TransactionRecord)

    assert record_via_response.transaction_id == record_via_query.transaction_id
    assert record_via_response.transaction_hash == record_via_query.transaction_hash

@pytest.mark.integration
def test_chuck_tx_returns_responses_without_wait_for_receipt(env):
    """Test chunck transaction return only response when execute without wait for receipt."""
    topic_receipt = TopicCreateTransaction(memo="Python SDK topic").execute(env.client)
    assert topic_receipt.status == ResponseCode.SUCCESS, (
        f"Topic creation failed: {ResponseCode(topic_receipt.status).name}"
    )

    topic_id = topic_receipt.topic_id
    message = "A" * (1024 * 14) # message with (1024 * 14) bytes ie 14 chunks

    # Create a chuck transaction
    message_tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message(message)
        .freeze_with(env.client)
    )

    message_responses = message_tx.execute_all(env.client, wait_for_receipt=False)
    
    assert len(message_responses) == 14
    assert isinstance(message_responses[0], TransactionResponse)
    assert message_responses[0].transaction is message_tx
    assert message_responses[0].validate_status is True

    # Verify topic_message receipt (i.e reach consensus)
    for response in message_responses:
        message_receipt = response.get_receipt(env.client)
        assert message_receipt.status == ResponseCode.SUCCESS

    # Validates all chucks has been send
    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert info.sequence_number == 14



@pytest.mark.integration
def test_chuck_tx_returns_receipts_with_wait_for_receipt(env):
    """Test chunck transaction return only receipts when execute with wait for receipt."""
    topic_receipt = TopicCreateTransaction(memo="Python SDK topic").execute(env.client)
    assert topic_receipt.status == ResponseCode.SUCCESS, (
        f"Topic creation failed: {ResponseCode(topic_receipt.status).name}"
    )

    topic_id = topic_receipt.topic_id
    message = "A" * (1024 * 14) # message with (1024 * 14) bytes ie 14 chunks

    # Create a chuck transaction
    message_tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(topic_id)
        .set_message(message)
        .freeze_with(env.client)
    )

    message_receipt = message_tx.execute_all(env.client, wait_for_receipt=True)
    
    assert len(message_receipt) == 14
    assert isinstance(message_receipt[0], TransactionReceipt)

    # Verify topic_message receipt status
    for receipt in message_receipt:
        assert receipt.status == ResponseCode.SUCCESS

    # Validates all chucks has been send
    info = TopicInfoQuery().set_topic_id(topic_id).execute(env.client)
    assert info.sequence_number == 14

