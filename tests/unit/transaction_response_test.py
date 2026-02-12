import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_get_record_pb2,
    transaction_receipt_pb2,
    transaction_record_pb2,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.transaction_get_receipt_query import (
    TransactionGetReceiptQuery,
)
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_record import TransactionRecord
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def transaction_response():
    """Create a populated TransactionResponse for testing."""
    response = TransactionResponse()
    response.transaction_id = TransactionId.from_string("0.0.1001@1234567890.000000001")
    response.node_id = AccountId.from_string("0.0.3")
    response.validate_status = True
    return response


def test_get_receipt_query_builds_query(transaction_response):
    """Test get_receipt_query builds and returns the transaction receipt query."""
    query = transaction_response.get_receipt_query()

    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.transaction_id == transaction_response.transaction_id
    assert len(query.node_account_ids) == 1
    assert query.node_account_ids[0] == transaction_response.node_id


def test_get_receipt_executes_and_returns_receipt(transaction_response):
    """Test get_receipt execute receipt query and return transaction receipt."""
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(
                    shardNum=0,
                    realmNum=0,
                    accountNum=1234,
                ),
            ),
        )
    )

    with mock_hedera_servers([[receipt_response]]) as client:
        receipt = transaction_response.get_receipt(client)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.account_id.num == 1234


def test_get_record_query_builds_query(transaction_response):
    """Test get_record_query builds and returns the transaction record query."""
    query = transaction_response.get_record_query()

    assert isinstance(query, TransactionRecordQuery)
    assert query.transaction_id == transaction_response.transaction_id
    assert len(query.node_account_ids) == 1
    assert query.node_account_ids[0] == transaction_response.node_id


def test_get_record_executes_and_returns_record(transaction_response):
    """Test get_record execute record query and return transaction record."""
    receipt = transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS)
    record = transaction_record_pb2.TransactionRecord(
        receipt=receipt, memo="record", transactionFee=100
    )

    record_response = [
        [
            response_pb2.Response(
                transactionGetRecord=transaction_get_record_pb2.TransactionGetRecordResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.COST_ANSWER,
                        cost=2,
                    )
                )
            ),
            response_pb2.Response(
                transactionGetRecord=transaction_get_record_pb2.TransactionGetRecordResponse(
                    header=response_header_pb2.ResponseHeader(
                        nodeTransactionPrecheckCode=ResponseCode.OK,
                        responseType=ResponseType.ANSWER_ONLY,
                        cost=2,
                    ),
                    transactionRecord=record,
                )
            ),
        ]
    ]

    with mock_hedera_servers(record_response) as client:
        record = transaction_response.get_record(client)

        assert isinstance(record, TransactionRecord)
        assert record.receipt.status == ResponseCode.SUCCESS
