"""
Tests for TransactionResponse behavior.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_transaction_response_fields(transaction_id):
    """asserting response is correctly populated"""
    resp = TransactionResponse()
    resp.transaction_id = transaction_id
    resp.node_id = AccountId(0, 0, 3)

    assert resp.transaction_id == transaction_id
    assert resp.node_id == AccountId(0, 0, 3)


def test_transaction_response_get_receipt_is_pinned_to_submitting_node(transaction_id):
    """
    mock_hedera_servers assigns:
      - server[0] -> node 0.0.3
      - server[1] -> node 0.0.4

    We make node 0.0.3 return a NON-retryable precheck error, and node 0.0.4 return SUCCESS.
    If TransactionResponse.get_receipt() does not pin, it will likely hit 0.0.3 and fail.
    If it pins to self.node_id (0.0.4), it will succeed.
    """
    bad_node_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.UNKNOWN
            ),
        )
    )

    good_node_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )

    response_sequences = [
        [bad_node_response],  # node 0.0.3
        [good_node_response],  # node 0.0.4
    ]

    with mock_hedera_servers(response_sequences) as client:
        resp = TransactionResponse()
        resp.transaction_id = transaction_id
        resp.node_id = AccountId(0, 0, 4)  # submitting node (server[1])

        receipt = resp.get_receipt(client)

        assert receipt.status == ResponseCode.SUCCESS
