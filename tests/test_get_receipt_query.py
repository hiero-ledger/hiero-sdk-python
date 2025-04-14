"""Tests for the TransactionGetReceiptQuery functionality."""

import pytest
from unittest.mock import patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError, ReceiptStatusError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
)
from hiero_sdk_python.query.transaction_get_receipt_query import TransactionGetReceiptQuery
from hiero_sdk_python.response_code import ResponseCode

from tests.mock_server import mock_hedera_servers

def test_transaction_get_receipt_query(transaction_id):
    """Test basic functionality of TransactionGetReceiptQuery with a mocked client."""
    response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            )
        )
    )

    response_sequences = [[response]]

    with mock_hedera_servers(response_sequences) as client:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

        assert result.status == ResponseCode.SUCCESS


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
            )
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
                    shardNum=0,
                    realmNum=0,
                    accountNum=1234
                )
            )
        )
    )
    
    response_sequences = [[not_found_response, success_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify query was successful after retry
        assert result.status == ResponseCode.SUCCESS
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"
        
        # Verify we didn't switch nodes (RECEIPT_NOT_FOUND is retriable without node switch)
        assert client.node_account_id == AccountId(0, 0, 3)


def test_receipt_query_retry_on_header_busy(transaction_id):
    """Test that receipt query retries when the header status is BUSY."""
    # First response has BUSY in header, second has OK and SUCCESS
    busy_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.BUSY
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt()
        )
    )
    
    success_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            )
        )
    )
    
    response_sequences = [[busy_response, success_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep') as mock_sleep:
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )
        
        try:
            result = query.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        
        # Verify query was successful after retry
        assert result.status == ResponseCode.SUCCESS
        
        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"


def test_receipt_query_fails_on_nonretriable_error(transaction_id):
    """Test that receipt query fails on non-retriable error."""
    # Create a response with a non-retriable error in the header
    error_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION_ID
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt()
        )
    )
    
    response_sequences = [[error_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )
        
        # Create the query and verify it fails with the expected error
        with pytest.raises(PrecheckError) as exc_info:
            query.execute(client)
        
        # Verify the error contains the expected status
        assert str(ResponseCode.INVALID_TRANSACTION_ID) in str(exc_info.value)

def test_receipt_query_receipt_status_error(transaction_id):
    """Test that receipt query fails on receipt status error."""
    # Create a response with a receipt status error
    error_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.BUSY
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.BUSY
            )
        )
    )
    
    response_sequences = [[error_response]]
    
    with mock_hedera_servers(response_sequences) as client, patch('time.sleep'):
        client.max_attempts = 1
        query = (
            TransactionGetReceiptQuery()
            .set_transaction_id(transaction_id)
        )
        
        # Create the query and verify it fails with the expected error
        with pytest.raises(MaxAttemptsError) as exc_info:
            query.execute(client)
        
        assert str(f"Receipt for transaction {transaction_id} contained error status: BUSY ({ResponseCode.BUSY})") in str(exc_info.value)
