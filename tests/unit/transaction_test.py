from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import ReceiptStatusError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit



def test_execute_waits_for_receipt_receipt():
    """Test execute return TransactionReceipt when wait_for_receipt is True (default)."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Default value of wait_for_receipt = True
        receipt = tx.execute(client, wait_for_receipt=True)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.SUCCESS


def test_execute_without_wait_returns_transaction_response():
    """Test execute return TransactionResponse when wait_for_receipt is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Explicitly pass wait_for_receipt=False to get TransactionResponse
        response = tx.execute(client, wait_for_receipt=False)

        assert isinstance(response, TransactionResponse)
        assert response.transaction is tx
        assert response.node_id == tx.node_account_id
        assert response.validate_status is True


def test_execute_raises_error_when_validation_enabled_and_transaction_fails():
    """Test execute raises error for failing transactions when validate_status is True."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        with pytest.raises(ReceiptStatusError) as e:
            tx.execute(client, validate_status=True)

        assert e.value.status == ResponseCode.INVALID_SIGNATURE


def test_execute_returns_receipt_without_error_when_validation_disabled():
    """Test execute returns a receipt normally on failure when validate_status is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        receipt = tx.execute(client)

        assert receipt.status == ResponseCode.INVALID_SIGNATURE
@pytest.fixture
def file_id():
    """Returns a file_is for test."""
    return FileId.from_string("0.0.1")


@pytest.fixture
def account_id():
    """Returns an account_id for test."""
    return AccountId.from_string("0.0.9")


@pytest.fixture
def transaction_id():
    """Returns a transaction_id for test."""
    return TransactionId.from_string("0.0.9@1770911831.331000137")


def test_same_size_for_identical_transactions(transaction_id, account_id):
    """Test two identical transactions should have the same size."""
    key = PrivateKey.generate()

    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.size == tx2.size


def test_signed_tx_have_larger_size(transaction_id, account_id):
    """Test signed Transaction should have larger size."""
    key = PrivateKey.generate()

    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
        .sign(PrivateKey.generate())
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.size > tx2.size


def test_tx_with_larger_content_should_have_larger_tx_body(transaction_id, account_id):
    """Test transaction with larger content should have larger transaction body."""
    tx1 = (
        FileCreateTransaction()
        .set_contents("smallBody")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        FileCreateTransaction()
        .set_contents("veryLargeBody")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    assert tx1.body_size < tx2.body_size


def test_tx_without_optional_fields_should_have_smaller_tx_body(
    transaction_id, account_id
):
    """Test transaction with without optional fields should have smaller transaction body."""
    key = PrivateKey.generate()
    tx1 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    tx2 = (
        AccountCreateTransaction()
        .set_key_without_alias(key)
        .set_initial_balance(Hbar(2))
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .set_transaction_valid_duration(10)
        .freeze()
    )

    assert tx1.body_size < tx2.body_size


def test_chunk_tx_should_return_list_of_body_sizes(file_id, account_id, transaction_id):
    """Test should return array of body sizes for multi-chunk transaction."""
    chunk_size = 1024
    content = "a" * (chunk_size * 3)

    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_chunk_size(chunk_size)
        .set_contents(content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 3


def test_single_chunk_tx_return_list_of_len_one(file_id, account_id, transaction_id):
    """Test should return array of one size for single-chunk transaction."""
    content = "small_content"
    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 1


def test_tx_with_no_content_should_return_single_body_chunk(
    file_id, account_id, transaction_id
):
    """Test should return single body chunk for transaction with no content."""
    tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(" ")
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    sizes = tx.body_size_all_chunks
    assert isinstance(sizes, list)
    assert len(sizes) == 1


def test_chunked_tx_return_proper_sizes(file_id, account_id, transaction_id):
    """Test should return proper sizes for FileAppend transactions when chunking occurs."""
    large_content = "a" * 2048

    large_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(large_content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    large_size = large_tx.size

    small_content = "a" * 512

    small_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(small_content)
        .set_transaction_id(transaction_id)
        .set_node_account_id(account_id)
        .freeze()
    )

    small_size = small_tx.size

    # Since large content is 2KB and chunk size is 1KB, this should create 2 chunks
    # Size should be greater than single chunk size
    large_size > 1024

    # The larger chunked transaction should be bigger than the small single-chunk transaction
    large_size > small_size
