"""
Unit tests for the ContractCreateTransaction class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_create_transaction import (
    DEFAULT_AUTO_RENEW_PERIOD,
    ContractCreateParams,
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


@pytest.fixture
def contract_params():
    """Fixture for contract parameters."""
    return {
        "bytecode_file_id": FileId(0, 0, 123),
        "proxy_account_id": AccountId(0, 0, 456),
        "admin_key": PrivateKey.generate().public_key(),
        "gas": 100000,
        "initial_balance": 1000000,
        "auto_renew_period": Duration(7776000),  # 90 days
        "parameters": b"test parameters",
        "contract_memo": "Test contract",
        "bytecode": b"test bytecode",
        "auto_renew_account_id": AccountId(0, 0, 789),
        "max_automatic_token_associations": 10,
        "staked_account_id": AccountId(0, 0, 999),
        "staked_node_id": 1,
        "decline_reward": False,
    }


def test_constructor_with_parameters(contract_params):
    """Test creating a contract create transaction with constructor parameters."""
    params = ContractCreateParams(
        bytecode_file_id=contract_params["bytecode_file_id"],
        proxy_account_id=contract_params["proxy_account_id"],
        admin_key=contract_params["admin_key"],
        gas=contract_params["gas"],
        initial_balance=contract_params["initial_balance"],
        auto_renew_period=contract_params["auto_renew_period"],
        parameters=contract_params["parameters"],
        contract_memo=contract_params["contract_memo"],
        bytecode=contract_params["bytecode"],
        auto_renew_account_id=contract_params["auto_renew_account_id"],
        max_automatic_token_associations=contract_params[
            "max_automatic_token_associations"
        ],
        staked_account_id=contract_params["staked_account_id"],
        staked_node_id=contract_params["staked_node_id"],
        decline_reward=contract_params["decline_reward"],
    )

    contract_tx = ContractCreateTransaction(contract_params=params)

    assert contract_tx.bytecode_file_id == contract_params["bytecode_file_id"]
    assert contract_tx.proxy_account_id == contract_params["proxy_account_id"]
    assert contract_tx.admin_key == contract_params["admin_key"]
    assert contract_tx.gas == contract_params["gas"]
    assert contract_tx.initial_balance == contract_params["initial_balance"]
    assert contract_tx.auto_renew_period == contract_params["auto_renew_period"]
    assert contract_tx.parameters == contract_params["parameters"]
    assert contract_tx.contract_memo == contract_params["contract_memo"]
    assert contract_tx.bytecode == contract_params["bytecode"]
    assert contract_tx.auto_renew_account_id == contract_params["auto_renew_account_id"]
    assert (
        contract_tx.max_automatic_token_associations
        == contract_params["max_automatic_token_associations"]
    )
    assert contract_tx.staked_account_id == contract_params["staked_account_id"]
    assert contract_tx.staked_node_id == contract_params["staked_node_id"]
    assert contract_tx.decline_reward == contract_params["decline_reward"]
    assert contract_tx._default_transaction_fee == Hbar(20).to_tinybars()


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    contract_tx = ContractCreateTransaction()

    assert contract_tx.bytecode_file_id is None
    assert contract_tx.proxy_account_id is None
    assert contract_tx.admin_key is None
    assert contract_tx.gas is None
    assert contract_tx.initial_balance is None
    assert contract_tx.auto_renew_period == Duration(DEFAULT_AUTO_RENEW_PERIOD)
    assert contract_tx.parameters is None
    assert contract_tx.contract_memo is None
    assert contract_tx.bytecode is None
    assert contract_tx.auto_renew_account_id is None
    assert contract_tx.max_automatic_token_associations is None
    assert contract_tx.staked_account_id is None
    assert contract_tx.staked_node_id is None
    assert contract_tx.decline_reward is None


def test_build_transaction_body_with_bytecode_file_id(
    mock_account_ids, contract_params
):
    """Test building a contract create transaction body with bytecode file ID."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(
            bytecode_file_id=contract_params["bytecode_file_id"],
            gas=contract_params["gas"],
            initial_balance=contract_params["initial_balance"],
            admin_key=contract_params["admin_key"],
            contract_memo=contract_params["contract_memo"],
            parameters=contract_params["parameters"],
        )
    )

    # Set operator and node account IDs needed for building transaction body
    contract_tx.operator_account_id = operator_id
    contract_tx.node_account_id = node_account_id

    transaction_body = contract_tx.build_transaction_body()

    assert (
        transaction_body.contractCreateInstance.fileID
        == contract_params["bytecode_file_id"]._to_proto()
    )
    assert transaction_body.contractCreateInstance.gas == contract_params["gas"]
    assert (
        transaction_body.contractCreateInstance.initialBalance
        == contract_params["initial_balance"]
    )
    assert (
        transaction_body.contractCreateInstance.adminKey
        == contract_params["admin_key"]._to_proto()
    )
    assert (
        transaction_body.contractCreateInstance.memo == contract_params["contract_memo"]
    )
    assert (
        transaction_body.contractCreateInstance.constructorParameters
        == contract_params["parameters"]
    )
    assert transaction_body.contractCreateInstance.initcode == b""


def test_build_transaction_body_with_bytecode(mock_account_ids, contract_params):
    """Test building a contract create transaction body with direct bytecode."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(
            bytecode=contract_params["bytecode"],
            gas=contract_params["gas"],
            initial_balance=contract_params["initial_balance"],
        )
    )

    # Set operator and node account IDs needed for building transaction body
    contract_tx.operator_account_id = operator_id
    contract_tx.node_account_id = node_account_id

    transaction_body = contract_tx.build_transaction_body()

    assert (
        transaction_body.contractCreateInstance.initcode == contract_params["bytecode"]
    )
    assert transaction_body.contractCreateInstance.gas == contract_params["gas"]
    assert (
        transaction_body.contractCreateInstance.initialBalance
        == contract_params["initial_balance"]
    )
    assert not transaction_body.contractCreateInstance.HasField("fileID")


def test_build_scheduled_body(mock_account_ids, contract_params):
    """Test building a schedulable contract create transaction body."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(
            bytecode_file_id=contract_params["bytecode_file_id"],
            gas=contract_params["gas"],
            initial_balance=contract_params["initial_balance"],
            admin_key=contract_params["admin_key"],
            contract_memo=contract_params["contract_memo"],
            parameters=contract_params["parameters"],
        )
    )

    # Set operator and node account IDs needed for building transaction body
    contract_tx.operator_account_id = operator_id
    contract_tx.node_account_id = node_account_id

    # Build the scheduled body
    schedulable_body = contract_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify fields in the schedulable body
    assert (
        schedulable_body.contractCreateInstance.fileID
        == contract_params["bytecode_file_id"]._to_proto()
    )
    assert schedulable_body.contractCreateInstance.gas == contract_params["gas"]
    assert (
        schedulable_body.contractCreateInstance.initialBalance
        == contract_params["initial_balance"]
    )
    assert (
        schedulable_body.contractCreateInstance.adminKey
        == contract_params["admin_key"]._to_proto()
    )
    assert (
        schedulable_body.contractCreateInstance.memo == contract_params["contract_memo"]
    )
    assert (
        schedulable_body.contractCreateInstance.constructorParameters
        == contract_params["parameters"]
    )
    assert schedulable_body.contractCreateInstance.initcode == b""

def test_build_transaction_body_validation_errors():
    """Test that build_transaction_body raises appropriate validation errors."""
    # Test missing bytecode_file_id and bytecode
    contract_tx = ContractCreateTransaction()

    with pytest.raises(
        ValueError, match="Either bytecode_file_id or bytecode must be provided"
    ):
        contract_tx.build_transaction_body()

    # Test missing gas
    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(bytecode=b"test bytecode")
    )

    with pytest.raises(ValueError, match="Gas limit must be provided"):
        contract_tx.build_transaction_body()


def test_set_methods(contract_params):
    """Test the set methods of ContractCreateTransaction."""
    contract_tx = ContractCreateTransaction()

    test_cases = [
        (
            "set_bytecode_file_id",
            contract_params["bytecode_file_id"],
            "bytecode_file_id",
        ),
        ("set_bytecode", contract_params["bytecode"], "bytecode"),
        (
            "set_proxy_account_id",
            contract_params["proxy_account_id"],
            "proxy_account_id",
        ),
        ("set_admin_key", contract_params["admin_key"], "admin_key"),
        ("set_gas", contract_params["gas"], "gas"),
        ("set_initial_balance", contract_params["initial_balance"], "initial_balance"),
        (
            "set_auto_renew_period",
            contract_params["auto_renew_period"],
            "auto_renew_period",
        ),
        ("set_constructor_parameters", contract_params["parameters"], "parameters"),
        ("set_contract_memo", contract_params["contract_memo"], "contract_memo"),
        (
            "set_auto_renew_account_id",
            contract_params["auto_renew_account_id"],
            "auto_renew_account_id",
        ),
        (
            "set_max_automatic_token_associations",
            contract_params["max_automatic_token_associations"],
            "max_automatic_token_associations",
        ),
        (
            "set_staked_account_id",
            contract_params["staked_account_id"],
            "staked_account_id",
        ),
        ("set_staked_node_id", contract_params["staked_node_id"], "staked_node_id"),
        ("set_decline_reward", contract_params["decline_reward"], "decline_reward"),
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(contract_tx, method_name)(value)
        assert tx_after_set is contract_tx
        assert getattr(contract_tx, attr_name) == value


def test_set_bytecode_clears_file_id(contract_params):
    """Test that setting bytecode clears the bytecode_file_id."""
    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(
            bytecode_file_id=contract_params["bytecode_file_id"]
        )
    )

    assert contract_tx.bytecode_file_id is not None

    contract_tx.set_bytecode(contract_params["bytecode"])

    assert contract_tx.bytecode == contract_params["bytecode"]
    assert contract_tx.bytecode_file_id is None


def test_set_constructor_parameters_with_contract_function_parameters():
    """Test setting constructor parameters with ContractFunctionParameters."""
    contract_tx = ContractCreateTransaction()

    # Mock ContractFunctionParameters
    mock_params = ContractFunctionParameters()
    mock_params.to_bytes = lambda: b"mocked parameters"

    contract_tx.set_constructor_parameters(mock_params)

    assert contract_tx.parameters == b"mocked parameters"


def test_set_constructor_parameters_with_bytes():
    """Test setting constructor parameters with bytes."""
    contract_tx = ContractCreateTransaction()
    test_params = b"test parameters"

    contract_tx.set_constructor_parameters(test_params)

    assert contract_tx.parameters == test_params


def test_set_methods_require_not_frozen(mock_client, contract_params):
    """Test that set methods raise exception when transaction is frozen."""
    contract_tx = ContractCreateTransaction(
        contract_params=ContractCreateParams(
            bytecode_file_id=contract_params["bytecode_file_id"],
            gas=contract_params["gas"],
        )
    )
    contract_tx.freeze_with(mock_client)

    test_cases = [
        ("set_bytecode_file_id", contract_params["bytecode_file_id"]),
        ("set_bytecode", contract_params["bytecode"]),
        ("set_proxy_account_id", contract_params["proxy_account_id"]),
        ("set_admin_key", contract_params["admin_key"]),
        ("set_gas", contract_params["gas"]),
        ("set_initial_balance", contract_params["initial_balance"]),
        ("set_auto_renew_period", contract_params["auto_renew_period"]),
        ("set_constructor_parameters", contract_params["parameters"]),
        ("set_contract_memo", contract_params["contract_memo"]),
        ("set_auto_renew_account_id", contract_params["auto_renew_account_id"]),
        (
            "set_max_automatic_token_associations",
            contract_params["max_automatic_token_associations"],
        ),
        ("set_staked_account_id", contract_params["staked_account_id"]),
        ("set_staked_node_id", contract_params["staked_node_id"]),
        ("set_decline_reward", contract_params["decline_reward"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(contract_tx, method_name)(value)


def test_contract_create_transaction_can_execute():
    """Test that a contract create transaction can be executed successfully."""
    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for successful contract creation
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS,
        contractID=basic_types_pb2.ContractID(shardNum=0, realmNum=0, contractNum=1234),
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
        file_id = FileId(0, 0, 123)

        transaction = (
            ContractCreateTransaction()
            .set_bytecode_file_id(file_id)
            .set_gas(100000)
            .set_initial_balance(1000000)
            .set_contract_memo("Integration test contract")
        )

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"
        assert receipt.contract_id.contract == 1234


def test_contract_create_params_dataclass():
    """Test that ContractCreateParams dataclass works correctly."""
    file_id = FileId(0, 0, 123)
    account_id = AccountId(0, 0, 456)
    admin_key = PrivateKey.generate().public_key()

    # Test with all parameters
    params = ContractCreateParams(
        bytecode_file_id=file_id,
        proxy_account_id=account_id,
        admin_key=admin_key,
        gas=100000,
        initial_balance=1000000,
        contract_memo="Test contract",
    )

    assert params.bytecode_file_id == file_id
    assert params.proxy_account_id == account_id
    assert params.admin_key == admin_key
    assert params.gas == 100000
    assert params.initial_balance == 1000000
    assert params.contract_memo == "Test contract"

    # Test with defaults
    params_default = ContractCreateParams()
    assert params_default.bytecode_file_id is None
    assert params_default.proxy_account_id is None
    assert params_default.admin_key is None
    assert params_default.gas is None
    assert params_default.initial_balance is None
    assert params_default.auto_renew_period == Duration(DEFAULT_AUTO_RENEW_PERIOD)
    assert params_default.parameters is None
    assert params_default.contract_memo is None
    assert params_default.bytecode is None
    assert params_default.auto_renew_account_id is None
    assert params_default.max_automatic_token_associations is None
    assert params_default.staked_account_id is None
    assert params_default.staked_node_id is None
    assert params_default.decline_reward is None
