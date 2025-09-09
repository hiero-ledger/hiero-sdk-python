"""
Unit tests for the ContractExecuteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.contract.contract_execute_transaction import (
    ContractExecuteTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def execute_params():
    """Fixture for contract execution parameters."""
    return {
        "contract_id": ContractId(0, 0, 123),
        "gas": 100000,
        "amount": 1000000,
        "function_parameters": b"test parameters",
    }


def test_constructor_with_parameters(execute_params):
    """Test creating a contract execute transaction with constructor parameters."""
    execute_tx = ContractExecuteTransaction(
        contract_id=execute_params["contract_id"],
        gas=execute_params["gas"],
        amount=execute_params["amount"],
        function_parameters=execute_params["function_parameters"],
    )

    assert execute_tx.contract_id == execute_params["contract_id"]
    assert execute_tx.gas == execute_params["gas"]
    assert execute_tx.amount == execute_params["amount"]
    assert execute_tx.function_parameters == execute_params["function_parameters"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    execute_tx = ContractExecuteTransaction()

    assert execute_tx.contract_id is None
    assert execute_tx.gas is None
    assert execute_tx.amount is None
    assert execute_tx.function_parameters is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, execute_params):
    """Test building a contract execute transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    execute_tx = ContractExecuteTransaction(
        contract_id=execute_params["contract_id"],
        gas=execute_params["gas"],
        amount=execute_params["amount"],
        function_parameters=execute_params["function_parameters"],
    )

    # Set operator and node account IDs needed for building transaction body
    execute_tx.operator_account_id = operator_id
    execute_tx.node_account_id = node_account_id

    transaction_body = execute_tx.build_transaction_body()

    assert (
        transaction_body.contractCall.contractID
        == execute_params["contract_id"]._to_proto()
    )
    assert transaction_body.contractCall.gas == execute_params["gas"]
    assert transaction_body.contractCall.amount == execute_params["amount"]
    assert (
        transaction_body.contractCall.functionParameters
        == execute_params["function_parameters"]
    )

def test_build_scheduled_body_with_valid_parameters(mock_account_ids, execute_params):
    """Test building a schedulable contract execute transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    execute_tx = ContractExecuteTransaction(
        contract_id=execute_params["contract_id"],
        gas=execute_params["gas"],
        amount=execute_params["amount"],
        function_parameters=execute_params["function_parameters"],
    )

    # Set operator and node account IDs needed for building transaction body
    execute_tx.operator_account_id = operator_id
    execute_tx.node_account_id = node_account_id

    schedulable_body = execute_tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with contract call type
    assert schedulable_body.HasField("contractCall")

    # Verify fields in the schedulable body
    assert (
        schedulable_body.contractCall.contractID
        == execute_params["contract_id"]._to_proto()
    )
    assert schedulable_body.contractCall.gas == execute_params["gas"]
    assert schedulable_body.contractCall.amount == execute_params["amount"]
    assert (
        schedulable_body.contractCall.functionParameters
        == execute_params["function_parameters"]
    )


def test_build_transaction_body_missing_contract_id():
    """Test that build_transaction_body raises ValueError when contract_id is missing."""
    execute_tx = ContractExecuteTransaction()

    with pytest.raises(ValueError, match="Missing required ContractID"):
        execute_tx.build_transaction_body()


def test_set_contract_id(execute_params):
    """Test setting contract_id using the setter method."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_contract_id(execute_params["contract_id"])

    assert execute_tx.contract_id == execute_params["contract_id"]
    assert result is execute_tx  # Should return self for method chaining


def test_set_gas(execute_params):
    """Test setting gas using the setter method."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_gas(execute_params["gas"])

    assert execute_tx.gas == execute_params["gas"]
    assert result is execute_tx


def test_set_payable_amount(execute_params):
    """Test setting amount using the setter method."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_payable_amount(execute_params["amount"])

    assert execute_tx.amount == execute_params["amount"]
    assert result is execute_tx


def test_set_payable_amount_with_hbar():
    """Test that amount is correctly set when using an Hbar object."""
    execute_tx = ContractExecuteTransaction(amount=Hbar(10))
    assert execute_tx.amount == 1000000000

    result = execute_tx.set_payable_amount(Hbar(1))
    assert result is execute_tx
    assert execute_tx.amount == 100000000


def test_set_function_parameters_with_bytes(execute_params):
    """Test setting function parameters with bytes."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_function_parameters(execute_params["function_parameters"])

    assert execute_tx.function_parameters == execute_params["function_parameters"]
    assert result is execute_tx


def test_set_function_parameters_with_contract_function_parameters():
    """Test setting function parameters with ContractFunctionParameters."""
    execute_tx = ContractExecuteTransaction()

    # Create real ContractFunctionParameters instance
    params = ContractFunctionParameters("testFunction")
    params.add_uint256(123)
    params.add_string("test")

    result = execute_tx.set_function_parameters(params)

    assert execute_tx.function_parameters == params.to_bytes()
    assert result is execute_tx


def test_set_function_parameters_with_none(execute_params):
    """Test setting function parameters to None."""
    execute_tx = ContractExecuteTransaction(
        function_parameters=execute_params["function_parameters"]
    )

    result = execute_tx.set_function_parameters(None)

    assert execute_tx.function_parameters is None
    assert result is execute_tx


def test_set_function_method():
    """Test setting function name and parameters using set_function method."""
    execute_tx = ContractExecuteTransaction()

    # Test with parameters
    params = ContractFunctionParameters()
    params.add_uint256(456)

    result = execute_tx.set_function("myFunction", params)

    assert result is execute_tx
    # Verify the function name was set and parameters were encoded
    assert execute_tx.function_parameters is not None
    assert execute_tx.function_parameters == params.to_bytes()


def test_set_function_method_without_params():
    """Test setting function name without parameters using set_function method."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_function("simpleFunction")
    func_parameters = ContractFunctionParameters("simpleFunction")

    assert result is execute_tx
    assert execute_tx.function_parameters == func_parameters.to_bytes()


def test_set_function_with_empty_function_name():
    """Test setting function with empty function name."""
    execute_tx = ContractExecuteTransaction()

    result = execute_tx.set_function("")

    assert result is execute_tx
    assert execute_tx.function_parameters == b""


def test_set_function_parameters_type_validation():
    """Test that set_function_parameters handles different input types correctly."""
    execute_tx = ContractExecuteTransaction()

    # Test with bytes
    byte_params = b"raw bytes"
    execute_tx.set_function_parameters(byte_params)
    assert execute_tx.function_parameters == byte_params

    # Test with ContractFunctionParameters
    func_params = ContractFunctionParameters("test")
    func_params.add_bool(True)
    execute_tx.set_function_parameters(func_params)
    assert execute_tx.function_parameters == func_params.to_bytes()

    # Test with None
    execute_tx.set_function_parameters(None)
    assert execute_tx.function_parameters is None


def test_set_methods_require_not_frozen(mock_client, execute_params):
    """Test that setter methods raise exception when transaction is frozen."""
    execute_tx = ContractExecuteTransaction(contract_id=execute_params["contract_id"])
    execute_tx.freeze_with(mock_client)

    test_cases = [
        ("set_contract_id", execute_params["contract_id"]),
        ("set_gas", execute_params["gas"]),
        ("set_payable_amount", execute_params["amount"]),
        ("set_function_parameters", execute_params["function_parameters"]),
        ("set_function", "testFunction"),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(execute_tx, method_name)(value)


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    execute_tx = ContractExecuteTransaction()

    mock_channel = MagicMock()
    mock_smart_contract_stub = MagicMock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = execute_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_smart_contract_stub.contractCallMethod


def test_build_transaction_body_with_required_params(mock_account_ids, contract_id):
    """Test building transaction body with only required parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    execute_tx = ContractExecuteTransaction(contract_id=contract_id)

    # Set operator and node account IDs needed for building transaction body
    execute_tx.operator_account_id = operator_id
    execute_tx.node_account_id = node_account_id

    transaction_body = execute_tx.build_transaction_body()

    assert transaction_body.contractCall.contractID == contract_id._to_proto()
    assert transaction_body.contractCall.gas == 0
    assert transaction_body.contractCall.amount == 0
    assert transaction_body.contractCall.functionParameters == b""


def test_sign_transaction(mock_client, execute_params):
    """Test signing the contract execute transaction with a private key."""
    execute_tx = ContractExecuteTransaction(
        contract_id=execute_params["contract_id"], gas=execute_params["gas"]
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    execute_tx.freeze_with(mock_client)
    execute_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = execute_tx._transaction_body_bytes[node_id]

    assert len(execute_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = execute_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, execute_params):
    """Test converting the contract execute transaction to protobuf format after signing."""
    execute_tx = ContractExecuteTransaction(
        contract_id=execute_params["contract_id"], gas=execute_params["gas"]
    )

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    execute_tx.freeze_with(mock_client)
    execute_tx.sign(private_key)
    proto = execute_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_contract_execute_transaction_can_execute():
    """Test that a contract execute transaction can be executed successfully."""
    ok_response = transaction_response_pb2.TransactionResponse()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    contract_id_proto = basic_types_pb2.ContractID(
        shardNum=0, realmNum=0, contractNum=1234
    )
    mock_receipt_proto = transaction_receipt_pb2.TransactionReceipt(
        status=ResponseCode.SUCCESS, contractID=contract_id_proto
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
        contract_id = ContractId(0, 0, 1234)
        transaction = (
            ContractExecuteTransaction()
            .set_contract_id(contract_id)
            .set_gas(1000000)
            .set_function(
                "setMessage", ContractFunctionParameters().add_bytes32(b"Test message")
            )
        )

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"
        assert str(receipt.contract_id) == str(contract_id)
