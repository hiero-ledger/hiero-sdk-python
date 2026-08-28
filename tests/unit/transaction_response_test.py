"""
Tests for TransactionResponse behavior.

Includes receipt handling, record queries, and validation scenarios.
"""

# pylint: disable=no-member,no-name-in-module
# no-member is disabled because Protobuf uses runtime descriptors
# no-name-in-module is disabled above because of the dynamic nature of the generated protobuf
from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import ReceiptStatusError
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
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
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


def test_get_receipt_query_set_validate_status(transaction_response):
    """Test receipt query correctly initializes with the validate_status flag."""
    query = transaction_response.get_receipt_query(validate_status=True)

    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.validate_status is True
    assert query.transaction_id == transaction_response.transaction_id
    assert len(query.node_account_ids) == 1
    assert query.node_account_ids[0] == transaction_response.node_id


def test_get_receipt_returns_failure_status_without_validate_status(
    transaction_response,
):
    """
    Test failing status behavior.
    Ensures a receipt is returned instead of raising an error
    when validation is disabled.
    """
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    with mock_hedera_servers([[receipt_response]]) as client:
        receipt = transaction_response.get_receipt(client)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.INVALID_SIGNATURE


def test_get_receipt_raises_exception_with_validate_status(transaction_response):
    """Test get_receipt error is raised for non-success statuses when validation is enabled."""
    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    with mock_hedera_servers([[receipt_response]]) as client:
        with pytest.raises(ReceiptStatusError) as e:
            transaction_response.get_receipt(client, validate_status=True)

        assert e.value.status == ResponseCode.INVALID_SIGNATURE


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
        receipt=receipt,
        memo="record",
        transactionFee=100,
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
        result = transaction_response.get_record(client)

        assert isinstance(result, TransactionRecord)
        assert result.receipt.status == ResponseCode.SUCCESS
        assert result.transaction_fee == record.transactionFee
        assert result.transaction_memo == record.memo


# Tests for TransactionResponse behavior.


def test_transaction_response_fields(transaction_id):
    """Asserting response is correctly populated."""
    resp = TransactionResponse()

    # Assert public attributes exist (PRIORITY 1: protect against breaking changes)
    assert hasattr(resp, "transaction_id")
    assert hasattr(resp, "node_id")
    assert hasattr(resp, "hash")
    assert hasattr(resp, "validate_status")
    assert hasattr(resp, "transaction")

    # Assert default values
    assert resp.hash == b""
    assert resp.validate_status is False
    assert resp.transaction is None

    resp.transaction_id = transaction_id
    resp.node_id = AccountId(0, 0, 3)

    assert resp.transaction_id == transaction_id
    assert resp.node_id == AccountId(0, 0, 3)


def test_transaction_response_get_receipt_is_pinned_to_submitting_node(
    transaction_id,
):
    """
    Test receipt retrieval behavior with node pinning.
    mock_hedera_servers assigns:
      - server[0] -> node 0.0.3
      - server[1] -> node 0.0.4

    We make node 0.0.3 return a NON-retryable precheck error, and node 0.0.4 return SUCCESS.
    If TransactionResponse.get_receipt() does not pin, it will likely hit 0.0.3 and fail.
    If it pins to self.node_id (0.0.4), it will succeed.
    """
    bad_node_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.UNKNOWN),
        )
    )

    good_node_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.SUCCESS),
        )
    )

    response_sequences = [
        [bad_node_response],  # node 0.0.3
        [good_node_response],  # node 0.0.4
    ]

    with mock_hedera_servers(response_sequences) as client:
        resp = TransactionResponse()
        resp.transaction_id = transaction_id
        resp.node_id = AccountId(0, 0, 4)

        #  # submitting node (server[1])
        receipt = resp.get_receipt(client)

        assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.parametrize("status", [1, 1.2, None, Client(), "True", [], {}])
def test_get_receipt_query_invalid_status_type(status):
    """Test that get_receipt_query raises TypeError for an invalid status type."""
    response = TransactionResponse()
    with pytest.raises(TypeError, match="validate_status must be a boolean"):
        response.get_receipt_query(validate_status=status)


@pytest.mark.parametrize(
    "client",
    [1, 1.2, True, "True", [], {}],  # None is allow for client
)
def test_get_receipt_query_invalid_client_type(client):
    """Test that get_receipt_query raises TypeError for an invalid client type."""
    response = TransactionResponse()
    with pytest.raises(TypeError, match="client must be an instance of Client"):
        response.get_receipt_query(client=client)


@pytest.mark.parametrize(
    "client",
    [1, 1.2, True, "True", [], {}],  # None is allow for client
)
def test_get_record_query_invalid_client_type(client):
    """Test that get_record_query raises TypeError for an invalid client type."""
    response = TransactionResponse()
    with pytest.raises(TypeError, match="client must be an instance of Client"):
        response.get_record_query(client=client)


def test_resolve_node_account_ids_with_failover_diabled(mock_client):
    """Test that only the transaction node is returned when no client or failover is disabled."""
    response = TransactionResponse()
    response.node_id = AccountId.from_string("0.0.3")

    # When client is None
    node_ids = response._resolve_node_account_ids(None)
    assert node_ids == [AccountId.from_string("0.0.3")]

    # With failover disabled
    node_ids = response._resolve_node_account_ids(mock_client)
    assert node_ids == [AccountId.from_string("0.0.3")]


def test_resolve_node_account_ids_with_transaction_nodes(mock_client):
    """Test that transaction nodes are used when receipt failover is enabled."""
    response = TransactionResponse()
    response.node_id = AccountId.from_string("0.0.3")
    response._transaction_node_ids = [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4")]

    mock_client.set_allow_receipt_node_failover(True)
    node_ids = response._resolve_node_account_ids(mock_client)
    assert node_ids == [AccountId.from_string("0.0.3"), AccountId.from_string("0.0.4")]


def test_resolve_node_account_ids_uses_client_nodes_when_transaction_nodes_unavailable(mock_client):
    """Test that client nodes are used when transaction nodes are unavailable."""
    response = TransactionResponse()
    response.node_id = AccountId.from_string("0.0.3")
    response._transaction_node_ids = []

    mock_client.set_allow_receipt_node_failover(True)
    node_ids = response._resolve_node_account_ids(mock_client)

    assert node_ids == mock_client.get_node_account_ids()


def test_default_receipt_query_is_pinned_to_submitting_node(mock_client):
    """Test that receipt queries use only the submitting node by default."""
    node_id = AccountId.from_string("0.0.4")
    transaction_node_ids = [
        node_id,
        AccountId.from_string("0.0.5"),
    ]

    response = TransactionResponse()
    response.node_id = node_id
    response._transaction_node_ids = transaction_node_ids

    # Without a client, always pinned to the submitting node.
    query = response.get_receipt_query()
    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.node_account_ids == [node_id]

    # With failover disabled
    query = response.get_receipt_query(client=mock_client)
    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.node_account_ids == [node_id]


def test_default_record_query_is_pinned_to_submitting_node(mock_client):
    """Test that record queries use only the submitting node by default."""
    node_id = AccountId.from_string("0.0.4")
    transaction_node_ids = [
        node_id,
        AccountId.from_string("0.0.5"),
    ]

    response = TransactionResponse()
    response.node_id = node_id
    response._transaction_node_ids = transaction_node_ids

    # Without a client, always pinned to the submitting node.
    query = response.get_record_query()
    assert isinstance(query, TransactionRecordQuery)
    assert query.node_account_ids == [node_id]

    # With failover disabled
    query = response.get_record_query(mock_client)
    assert isinstance(query, TransactionRecordQuery)
    assert query.node_account_ids == [node_id]


def test_receipt_query_uses_transaction_nodes_when_failover_enabled(mock_client):
    """Test that receipt queries use transaction nodes when failover is enabled."""
    node_id = AccountId.from_string("0.0.4")
    transaction_node_ids = [
        node_id,
        AccountId.from_string("0.0.5"),
    ]

    response = TransactionResponse()
    response.node_id = node_id
    response._transaction_node_ids = transaction_node_ids

    mock_client.set_allow_receipt_node_failover(True)

    query = response.get_receipt_query(client=mock_client)

    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.node_account_ids == transaction_node_ids


def test_record_query_uses_transaction_nodes_when_failover_enabled(mock_client):
    """Test that record queries use transaction nodes when failover is enabled."""
    node_id = AccountId.from_string("0.0.4")
    transaction_node_ids = [
        node_id,
        AccountId.from_string("0.0.5"),
    ]

    response = TransactionResponse()
    response.node_id = node_id
    response._transaction_node_ids = transaction_node_ids

    mock_client.set_allow_receipt_node_failover(True)

    query = response.get_record_query(client=mock_client)

    assert isinstance(query, TransactionRecordQuery)
    assert query.node_account_ids == transaction_node_ids


def test_receipt_query_uses_client_nodes_when_transaction_nodes_not_set(mock_client):
    """Test that receipt queries use client nodes when transaction nodes are not set."""
    node_id = AccountId.from_string("0.0.4")

    response = TransactionResponse()
    response.node_id = node_id

    mock_client.set_allow_receipt_node_failover(True)
    query = response.get_receipt_query(client=mock_client)

    except_node_ids = [node_id]
    except_node_ids.extend(id for id in mock_client.get_node_account_ids() if id != node_id)

    assert isinstance(query, TransactionGetReceiptQuery)
    assert query.node_account_ids == except_node_ids


def test_record_query_uses_client_nodes_when_transaction_nodes_not_set(mock_client):
    """Test that record queries use client nodes when transaction nodes are not set."""
    node_id = AccountId.from_string("0.0.4")

    response = TransactionResponse()
    response.node_id = node_id

    mock_client.set_allow_receipt_node_failover(True)
    query = response.get_record_query(client=mock_client)

    except_node_ids = [node_id]
    except_node_ids.extend(id for id in mock_client.get_node_account_ids() if id != node_id)

    assert isinstance(query, TransactionRecordQuery)
    assert query.node_account_ids == except_node_ids
