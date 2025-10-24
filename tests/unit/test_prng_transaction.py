"""
Test cases for the PrngTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.prng_transaction import PrngTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def prng_params():
    """Fixture for PRNG transaction parameters."""
    return {
        "range": 1000,
    }


def test_constructor_with_parameters(prng_params):
    """Test creating a PRNG transaction with constructor parameters."""
    prng_tx = PrngTransaction(range=prng_params["range"])

    assert prng_tx.range == prng_params["range"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    prng_tx = PrngTransaction()

    assert prng_tx.range is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, prng_params):
    """Test building a PRNG transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    prng_tx = PrngTransaction(range=prng_params["range"])

    # Set operator and node account IDs needed for building transaction body
    prng_tx.operator_account_id = operator_id
    prng_tx.node_account_id = node_account_id

    transaction_body = prng_tx.build_transaction_body()

    assert transaction_body.HasField("util_prng")
    assert transaction_body.util_prng.range == prng_params["range"]


def test_build_transaction_body_without_range(mock_account_ids):
    """Test building a PRNG transaction body without range parameter."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    # Build a PRNG transaction with no range parameter (defaults to 0)
    prng_tx = PrngTransaction()

    # Set operator and node account IDs needed for building transaction body
    prng_tx.operator_account_id = operator_id
    prng_tx.node_account_id = node_account_id

    transaction_body = prng_tx.build_transaction_body()

    assert transaction_body.HasField("util_prng")
    assert transaction_body.util_prng.range == 0


def test_set_range(prng_params):
    """Test setting range using the setter method."""
    prng_tx = PrngTransaction()

    result = prng_tx.set_range(prng_params["range"])

    assert prng_tx.range == prng_params["range"]
    assert result is prng_tx  # Should return self for method chaining


def test_set_range_requires_not_frozen(mock_client, prng_params):
    """Test that set_range raises exception when transaction is frozen."""
    prng_tx = PrngTransaction()
    prng_tx.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        prng_tx.set_range(prng_params["range"])


def test_sign_transaction(mock_client, prng_params):
    """Test signing the PRNG transaction with a private key."""
    prng_tx = PrngTransaction(range=prng_params["range"])

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    prng_tx.freeze_with(mock_client)
    prng_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = prng_tx._transaction_body_bytes[node_id]

    assert len(prng_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = prng_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    prng_tx = PrngTransaction()

    mock_channel = MagicMock()
    mock_util_stub = MagicMock()
    mock_channel.util = mock_util_stub

    method = prng_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_util_stub.prng


def test_build_proto_body_with_negative_range_raises_error():
    """Test building the protobuf body with a negative range raises an error"""
    with pytest.raises(ValueError, match="Range can't be negative."):
        PrngTransaction().set_range(-1).build_transaction_body()


def test_prng_transaction_can_execute():
    """Test that a PRNG transaction can be executed successfully."""
    ok_response = transaction_response_pb2.TransactionResponse()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    mock_receipt_proto = transaction_receipt_pb2.TransactionReceipt(
        status=ResponseCode.SUCCESS
    )

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = PrngTransaction().set_range(1000)

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"
