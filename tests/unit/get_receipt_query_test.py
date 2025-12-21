"""Tests for the TransactionGetReceiptQuery functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
)
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.response_code import ResponseCode

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture transaction_id as parameter
def test_transaction_get_receipt_query(transaction_id):
    """Test basic functionality of TransactionGetReceiptQuery with a mocked client."""
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = TransactionGetReceiptQuery().set_transaction_id(transaction_id)

        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

        assert result.status == ResponseCode.SUCCESS


# This test uses fixture transaction_id as parameter
def test_receipt_query_retry_on_receipt_not_found(transaction_id):
    """Test that receipt query retries when the receipt status is RECEIPT_NOT_FOUND."""
    # First response has RECEIPT_NOT_FOUND, second has SUCCESS
    not_found_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.RECEIPT_NOT_FOUND
            ),
        )
    )

    success_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(
                    shardNum=0, realmNum=0, accountNum=1234
                ),
            ),
        )
    )

    response_sequences = [[not_found_response, success_response]]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("time.sleep") as mock_sleep,
    ):
        query = TransactionGetReceiptQuery().set_transaction_id(transaction_id)

        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")

        # Verify query was successful after retry
        assert result.status == ResponseCode.SUCCESS

        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"

        # Verify we didn't switch nodes (RECEIPT_NOT_FOUND is retriable without node switch)
        assert client.network.current_node._account_id == AccountId(0, 0, 3)


# This test uses fixture transaction_id as parameter
def test_receipt_query_receipt_status_error(transaction_id):
    """Test that receipt query fails on receipt status error."""
    # Create a response with a receipt status error
    error_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.UNKNOWN
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.UNKNOWN
            ),
        )
    )

    response_sequences = [[error_response]]

    with mock_hedera_servers(response_sequences) as client, patch("time.sleep"):
        client.max_attempts = 1
        query = TransactionGetReceiptQuery().set_transaction_id(transaction_id)

        # Create the query and verify it fails with the expected error
        with pytest.raises(MaxAttemptsError) as exc_info:
            query.execute(client)

        assert str(
            f"Receipt for transaction {transaction_id} contained error status: UNKNOWN ({ResponseCode.UNKNOWN})"
        ) in str(exc_info.value)


def test_receipt_query_does_not_require_payment():
    """Test that the receipt query does not require payment."""
    query = TransactionGetReceiptQuery()
    assert not query._is_payment_required()


def test_transaction_get_receipt_query_sets_include_child_receipts_in_request(
    transaction_id,
):
    """
    Test that _make_request() sets include_child_receipts correctly in the protobuf query.
    """
    query = (
        TransactionGetReceiptQuery()
        .set_transaction_id(transaction_id)
        .set_include_children(True)
    )

    request = query._make_request()

    # request is query_pb2.Query and should contain transactionGetReceipt
    assert request.transactionGetReceipt.include_child_receipts is True


def test_transaction_get_receipt_query_returns_child_receipts_when_requested(
    transaction_id,
):
    """
    Test that execute() maps child_transaction_receipts into TransactionReceipt.children
    when include_child_receipts is enabled and the network returns child receipts.
    """
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
            child_transaction_receipts=[
                transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
                transaction_receipt_pb2.TransactionReceipt(
                    status=ResponseCode.FAIL_INVALID
                ),
            ],
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
            .set_include_children(True)
        )

        result = query.execute(client)

        assert query.include_children is True
        assert len(response.transactionGetReceipt.child_transaction_receipts) == 2
        assert result.status == ResponseCode.SUCCESS
        assert len(result.children) == 2
        assert result.children[0].status == ResponseCode.SUCCESS
        assert result.children[1].status == ResponseCode.FAIL_INVALID


def test_transaction_get_receipt_query_children_empty_when_not_requested(
    transaction_id,
):
    """
    Test that execute() does not populate children by default (backward compatible behavior),
    even if the network includes child_transaction_receipts in the response.
    """
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
            child_transaction_receipts=[
                transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
            ],
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery().set_transaction_id(transaction_id)
        )

        result = query.execute(client)

        assert result.status == ResponseCode.SUCCESS
        assert result.children == []


def test_transaction_get_receipt_query_include_children_with_no_children(transaction_id):
    """ Testing that nothing explode if no children ar passed"""
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
            # no child_transaction_receipts
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
            .set_include_children(True)
        )
        result = query.execute(client)

        assert result.status == ResponseCode.SUCCESS
        assert result.children == []


def test_transaction_get_receipt_query_returns_duplicate_receipts_when_requested(
    transaction_id,
):
    """
    Test that execute() maps duplicate_transaction_receipts into TransactionReceipt.duplicates
    when include_duplicate_receipts is enabled and the network returns duplicate receipts.
    """
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
            duplicateTransactionReceipts=[
                transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
                transaction_receipt_pb2.TransactionReceipt(
                    status=ResponseCode.FAIL_INVALID
                ),
            ],
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
            .set_include_duplicates(True)
        )

        result = query.execute(client)

        assert len(response.transactionGetReceipt.duplicateTransactionReceipts) == 2
        assert result.status == ResponseCode.SUCCESS
        assert len(result.duplicates) == 2
        assert result.duplicates[0].status == ResponseCode.SUCCESS
        assert result.duplicates[1].status == ResponseCode.FAIL_INVALID


def test_transaction_get_receipt_query_returns_empty_duplicate_receipts_when_requested(
    transaction_id,
):
    """
    Test that execute() maps duplicate_transaction_receipts into TransactionReceipt.duplicates
    when include_duplicate_receipts is enabled and the network returns duplicate receipts.
    """
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        ),
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
            .set_include_duplicates(True)
        )

        result = query.execute(client)

        assert len(response.transactionGetReceipt.duplicateTransactionReceipts) == 0
        assert result.status == ResponseCode.SUCCESS
        assert len(result.duplicates) == 0


def test_transaction_get_receipt_query_returns_empty_duplicate_receipts_when_not_requested(
    transaction_id,
):
    """
    Test that execute() maps duplicate_transaction_receipts into TransactionReceipt.duplicates
    when include_duplicate_receipts is enabled and the network returns duplicate receipts.
    """
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
            duplicateTransactionReceipts=[
                transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
                transaction_receipt_pb2.TransactionReceipt(
                    status=ResponseCode.FAIL_INVALID
                ),
            ],
        ),
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )

        result = query.execute(client)

        assert len(response.transactionGetReceipt.duplicateTransactionReceipts) == 0
        assert result.status == ResponseCode.SUCCESS
        assert len(result.duplicates) == 0
