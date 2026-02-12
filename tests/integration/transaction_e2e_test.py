import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
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
