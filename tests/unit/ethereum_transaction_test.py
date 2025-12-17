"""
Unit tests for the EthereumTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def ethereum_params():
    """Fixture for ethereum transaction parameters."""
    return {
        "ethereum_data": b"ethereum transaction data",
        "call_data": FileId(0, 0, 123),
        "max_gas_allowed": 100000,
    }


def test_constructor_with_parameters(ethereum_params):
    """Test creating an ethereum transaction with constructor parameters."""
    ethereum_tx = EthereumTransaction(
        ethereum_data=ethereum_params["ethereum_data"],
        call_data_file_id=ethereum_params["call_data"],
        max_gas_allowed=ethereum_params["max_gas_allowed"],
    )

    assert ethereum_tx.ethereum_data == ethereum_params["ethereum_data"]
    assert ethereum_tx.call_data == ethereum_params["call_data"]
    assert ethereum_tx.max_gas_allowed == ethereum_params["max_gas_allowed"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    ethereum_tx = EthereumTransaction()

    assert ethereum_tx.ethereum_data is None
    assert ethereum_tx.call_data is None
    assert ethereum_tx.max_gas_allowed is None


def test_build_transaction_body_with_valid_parameters(
    mock_account_ids, ethereum_params
):
    """Test building an ethereum transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    ethereum_tx = EthereumTransaction(
        ethereum_data=ethereum_params["ethereum_data"],
        call_data_file_id=ethereum_params["call_data"],
        max_gas_allowed=ethereum_params["max_gas_allowed"],
    )

    # Set operator and node account IDs needed for building transaction body
    ethereum_tx.operator_account_id = operator_id
    ethereum_tx.node_account_id = node_account_id

    transaction_body = ethereum_tx.build_transaction_body()

    assert (
        transaction_body.ethereumTransaction.ethereum_data
        == ethereum_params["ethereum_data"]
    )
    assert (
        transaction_body.ethereumTransaction.call_data
        == ethereum_params["call_data"]._to_proto()
    )
    assert (
        transaction_body.ethereumTransaction.max_gas_allowance
        == ethereum_params["max_gas_allowed"]
    )


def test_build_transaction_body_with_minimal_parameters(mock_account_ids):
    """Test building an ethereum transaction body with minimal parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    ethereum_data = b"minimal ethereum data"

    ethereum_tx = EthereumTransaction(ethereum_data=ethereum_data)

    # Set operator and node account IDs needed for building transaction body
    ethereum_tx.operator_account_id = operator_id
    ethereum_tx.node_account_id = node_account_id

    transaction_body = ethereum_tx.build_transaction_body()

    assert transaction_body.ethereumTransaction.ethereum_data == ethereum_data
    assert not transaction_body.ethereumTransaction.HasField("call_data")
    assert transaction_body.ethereumTransaction.max_gas_allowance == 0


def test_set_ethereum_data(ethereum_params):
    """Test setting ethereum_data using the setter method."""
    ethereum_tx = EthereumTransaction()

    result = ethereum_tx.set_ethereum_data(ethereum_params["ethereum_data"])

    assert ethereum_tx.ethereum_data == ethereum_params["ethereum_data"]
    assert result is ethereum_tx  # Should return self for method chaining


def test_set_call_data_file_id(ethereum_params):
    """Test setting call_data using the setter method."""
    ethereum_tx = EthereumTransaction()

    result = ethereum_tx.set_call_data_file_id(ethereum_params["call_data"])

    assert ethereum_tx.call_data == ethereum_params["call_data"]
    assert result is ethereum_tx


def test_set_max_gas_allowed(ethereum_params):
    """Test setting max_gas_allowed using the setter method."""
    ethereum_tx = EthereumTransaction()

    result = ethereum_tx.set_max_gas_allowed(ethereum_params["max_gas_allowed"])

    assert ethereum_tx.max_gas_allowed == ethereum_params["max_gas_allowed"]
    assert result is ethereum_tx


def test_set_methods_require_not_frozen(mock_client, ethereum_params):
    """Test that setter methods raise exception when transaction is frozen."""
    ethereum_tx = EthereumTransaction(ethereum_data=b"test data")
    ethereum_tx.freeze_with(mock_client)

    test_cases = [
        ("set_ethereum_data", ethereum_params["ethereum_data"]),
        ("set_call_data_file_id", ethereum_params["call_data"]),
        ("set_max_gas_allowed", ethereum_params["max_gas_allowed"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(ethereum_tx, method_name)(value)


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    ethereum_tx = EthereumTransaction()

    mock_channel = MagicMock()
    mock_smart_contract_stub = MagicMock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = ethereum_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_smart_contract_stub.callEthereum


def test_sign_transaction(mock_client, ethereum_params):
    """Test signing the ethereum transaction with a private key."""
    ethereum_tx = EthereumTransaction(
        ethereum_data=ethereum_params["ethereum_data"],
        max_gas_allowed=ethereum_params["max_gas_allowed"],
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    ethereum_tx.freeze_with(mock_client)
    ethereum_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = ethereum_tx._transaction_body_bytes[node_id]

    assert len(ethereum_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = ethereum_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, ethereum_params):
    """Test converting the ethereum transaction to protobuf format after signing."""
    ethereum_tx = EthereumTransaction(
        ethereum_data=ethereum_params["ethereum_data"],
        max_gas_allowed=ethereum_params["max_gas_allowed"],
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    ethereum_tx.freeze_with(mock_client)
    ethereum_tx.sign(private_key)
    proto = ethereum_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0

def test_build_scheduled_body_raises_exception():
    """Test that build_scheduled_body raises ValueError."""
    schedule_tx = EthereumTransaction()

    with pytest.raises(ValueError, match="Cannot schedule an EthereumTransaction"):
        schedule_tx.build_scheduled_body()

def test_ethereum_transaction_can_execute():
    """Test that an ethereum transaction can be executed successfully."""
    ok_response = transaction_response_pb2.TransactionResponse()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    mock_receipt_proto = transaction_receipt_pb2.TransactionReceipt(
        status=ResponseCode.SUCCESS,
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
        ethereum_data = b"test ethereum transaction data"
        transaction = (
            EthereumTransaction()
            .set_ethereum_data(ethereum_data)
            .set_max_gas_allowed(1000000)
        )

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"
