"""
Test cases for the ContractDeleteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_delete_transaction import (
    ContractDeleteTransaction,
)
from hiero_sdk_python.contract.contract_id import ContractId

pytestmark = pytest.mark.unit


@pytest.fixture
def delete_params():
    """Fixture for contract delete parameters."""
    return {
        "contract_id": ContractId(0, 0, 123),
        "transfer_contract_id": ContractId(0, 0, 456),
        "transfer_account_id": AccountId(0, 0, 789),
        "permanent_removal": True,
    }


def test_constructor_with_parameters(delete_params):
    """Test creating a contract delete transaction with constructor parameters."""
    delete_tx = ContractDeleteTransaction(
        contract_id=delete_params["contract_id"],
        transfer_contract_id=delete_params["transfer_contract_id"],
        transfer_account_id=delete_params["transfer_account_id"],
        permanent_removal=delete_params["permanent_removal"],
    )

    assert delete_tx.contract_id == delete_params["contract_id"]
    assert delete_tx.transfer_contract_id == delete_params["transfer_contract_id"]
    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]
    assert delete_tx.permanent_removal == delete_params["permanent_removal"]


def test_constructor_with_contract_id_only(delete_params):
    """Test creating a contract delete transaction with only contract_id."""
    delete_tx = ContractDeleteTransaction(contract_id=delete_params["contract_id"])

    assert delete_tx.contract_id == delete_params["contract_id"]
    assert delete_tx.transfer_contract_id is None
    assert delete_tx.transfer_account_id is None
    assert delete_tx.permanent_removal is None


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    delete_tx = ContractDeleteTransaction()

    assert delete_tx.contract_id is None
    assert delete_tx.transfer_contract_id is None
    assert delete_tx.transfer_account_id is None
    assert delete_tx.permanent_removal is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, delete_params):
    """Test building a contract delete transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ContractDeleteTransaction(
        contract_id=delete_params["contract_id"],
        transfer_contract_id=delete_params["transfer_contract_id"],
        transfer_account_id=delete_params["transfer_account_id"],
        permanent_removal=delete_params["permanent_removal"],
    )

    # Set operator and node account IDs needed for building transaction body
    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    # When both transfer_account_id and transfer_contract_id are set,
    # the protobuf only will only set transferAccountID
    assert (
        transaction_body.contractDeleteInstance.contractID
        == delete_params["contract_id"]._to_proto()
    )
    assert (
        transaction_body.contractDeleteInstance.transferAccountID
        == delete_params["transfer_account_id"]._to_proto()
    )
    assert (
        transaction_body.contractDeleteInstance.permanent_removal
        == delete_params["permanent_removal"]
    )


def test_build_transaction_body_with_required_params_only(
    mock_account_ids, contract_id
):
    """Test building transaction body with only required parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ContractDeleteTransaction(contract_id=contract_id)

    # Set operator and node account IDs needed for building transaction body
    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert transaction_body.contractDeleteInstance.contractID == contract_id._to_proto()
    assert not transaction_body.contractDeleteInstance.HasField("transferContractID")
    assert not transaction_body.contractDeleteInstance.HasField("transferAccountID")
    assert transaction_body.contractDeleteInstance.permanent_removal is False


def test_build_transaction_body_with_transfer_contract_id_only(
    mock_account_ids, delete_params
):
    """Test building transaction body with transfer_contract_id only."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ContractDeleteTransaction(
        contract_id=delete_params["contract_id"],
        transfer_contract_id=delete_params["transfer_contract_id"],
    )

    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert (
        transaction_body.contractDeleteInstance.contractID
        == delete_params["contract_id"]._to_proto()
    )
    assert (
        transaction_body.contractDeleteInstance.transferContractID
        == delete_params["transfer_contract_id"]._to_proto()
    )
    assert not transaction_body.contractDeleteInstance.HasField("transferAccountID")
    assert transaction_body.contractDeleteInstance.permanent_removal is False


def test_build_transaction_body_with_transfer_account_id_only(
    mock_account_ids, delete_params
):
    """Test building transaction body with transfer_account_id only."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ContractDeleteTransaction(
        contract_id=delete_params["contract_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert (
        transaction_body.contractDeleteInstance.contractID
        == delete_params["contract_id"]._to_proto()
    )
    assert not transaction_body.contractDeleteInstance.HasField("transferContractID")
    assert (
        transaction_body.contractDeleteInstance.transferAccountID
        == delete_params["transfer_account_id"]._to_proto()
    )
    assert transaction_body.contractDeleteInstance.permanent_removal is False


def test_build_transaction_body_with_permanent_removal_only(
    mock_account_ids, delete_params
):
    """Test building transaction body with permanent_removal only."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = ContractDeleteTransaction(
        contract_id=delete_params["contract_id"],
        permanent_removal=delete_params["permanent_removal"],
    )

    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert (
        transaction_body.contractDeleteInstance.contractID
        == delete_params["contract_id"]._to_proto()
    )
    assert not transaction_body.contractDeleteInstance.HasField("transferContractID")
    assert not transaction_body.contractDeleteInstance.HasField("transferAccountID")
    assert (
        transaction_body.contractDeleteInstance.permanent_removal
        == delete_params["permanent_removal"]
    )


def test_build_transaction_body_missing_contract_id():
    """Test that build_transaction_body raises ValueError when contract_id is missing."""
    delete_tx = ContractDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required ContractID"):
        delete_tx.build_transaction_body()


def test_set_contract_id(delete_params):
    """Test setting contract_id using the setter method."""
    delete_tx = ContractDeleteTransaction()

    result = delete_tx.set_contract_id(delete_params["contract_id"])

    assert delete_tx.contract_id == delete_params["contract_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_set_transfer_contract_id(delete_params):
    """Test setting transfer_contract_id using the setter method."""
    delete_tx = ContractDeleteTransaction()

    result = delete_tx.set_transfer_contract_id(delete_params["transfer_contract_id"])

    assert delete_tx.transfer_contract_id == delete_params["transfer_contract_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_set_transfer_account_id(delete_params):
    """Test setting transfer_account_id using the setter method."""
    delete_tx = ContractDeleteTransaction()

    result = delete_tx.set_transfer_account_id(delete_params["transfer_account_id"])

    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_set_permanent_removal(delete_params):
    """Test setting permanent_removal using the setter method."""
    delete_tx = ContractDeleteTransaction()

    result = delete_tx.set_permanent_removal(delete_params["permanent_removal"])

    assert delete_tx.permanent_removal == delete_params["permanent_removal"]
    assert result is delete_tx  # Should return self for method chaining


def test_set_permanent_removal_boolean_values():
    """Test setting permanent_removal with both True and False values."""
    delete_tx = ContractDeleteTransaction()

    # Test setting to True
    result = delete_tx.set_permanent_removal(True)
    assert delete_tx.permanent_removal is True
    assert result is delete_tx

    # Test setting to False
    result = delete_tx.set_permanent_removal(False)
    assert delete_tx.permanent_removal is False
    assert result is delete_tx

    # Test setting to None
    result = delete_tx.set_permanent_removal(None)
    assert delete_tx.permanent_removal is None
    assert result is delete_tx


def test_method_chaining_with_all_setters(delete_params):
    """Test that all setter methods support method chaining."""
    delete_tx = ContractDeleteTransaction()

    result = (
        delete_tx.set_contract_id(delete_params["contract_id"])
        .set_transfer_contract_id(delete_params["transfer_contract_id"])
        .set_transfer_account_id(delete_params["transfer_account_id"])
        .set_permanent_removal(delete_params["permanent_removal"])
    )

    assert result is delete_tx
    assert delete_tx.contract_id == delete_params["contract_id"]
    assert delete_tx.transfer_contract_id == delete_params["transfer_contract_id"]
    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]
    assert delete_tx.permanent_removal == delete_params["permanent_removal"]


def test_method_chaining_partial_setters(delete_params):
    """Test method chaining with only some setters."""
    delete_tx = ContractDeleteTransaction()

    result = delete_tx.set_contract_id(
        delete_params["contract_id"]
    ).set_permanent_removal(True)

    assert result is delete_tx
    assert delete_tx.contract_id == delete_params["contract_id"]
    assert delete_tx.transfer_contract_id is None
    assert delete_tx.transfer_account_id is None
    assert delete_tx.permanent_removal is True


def test_set_methods_require_not_frozen(mock_client, delete_params):
    """Test that setter methods raise exception when transaction is frozen."""
    delete_tx = ContractDeleteTransaction(contract_id=delete_params["contract_id"])
    delete_tx.freeze_with(mock_client)

    test_cases = [
        ("set_contract_id", delete_params["contract_id"]),
        ("set_transfer_contract_id", delete_params["transfer_contract_id"]),
        ("set_transfer_account_id", delete_params["transfer_account_id"]),
        ("set_permanent_removal", delete_params["permanent_removal"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(delete_tx, method_name)(value)


def test_sign_transaction(mock_client, delete_params):
    """Test signing the contract delete transaction with a private key."""
    delete_tx = ContractDeleteTransaction(contract_id=delete_params["contract_id"])

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)
    delete_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = delete_tx._transaction_body_bytes[node_id]

    assert len(delete_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = delete_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, delete_params):
    """Test converting the contract delete transaction to protobuf format after signing."""
    delete_tx = ContractDeleteTransaction(contract_id=delete_params["contract_id"])

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    delete_tx.freeze_with(mock_client)
    delete_tx.sign(private_key)
    proto = delete_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    delete_tx = ContractDeleteTransaction()

    mock_channel = MagicMock()
    mock_smart_contract_stub = MagicMock()
    mock_channel.smart_contract = mock_smart_contract_stub

    method = delete_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_smart_contract_stub.deleteContract


def test_parameter_validation_types(delete_params):
    """Test that parameters accept the correct types."""
    delete_tx = ContractDeleteTransaction()

    # Test with valid types
    delete_tx.set_contract_id(delete_params["contract_id"])
    assert isinstance(delete_tx.contract_id, ContractId)

    delete_tx.set_transfer_contract_id(delete_params["transfer_contract_id"])
    assert isinstance(delete_tx.transfer_contract_id, ContractId)

    delete_tx.set_transfer_account_id(delete_params["transfer_account_id"])
    assert isinstance(delete_tx.transfer_account_id, AccountId)

    delete_tx.set_permanent_removal(delete_params["permanent_removal"])
    assert isinstance(delete_tx.permanent_removal, bool)


def test_parameter_validation_none_values():
    """Test that parameters can be set to None."""
    delete_tx = ContractDeleteTransaction(
        contract_id=ContractId(0, 0, 123),
        transfer_contract_id=ContractId(0, 0, 456),
        transfer_account_id=AccountId(0, 0, 789),
        permanent_removal=True,
    )

    # All parameters except contract_id can be set to None
    delete_tx.set_transfer_contract_id(None)
    assert delete_tx.transfer_contract_id is None

    delete_tx.set_transfer_account_id(None)
    assert delete_tx.transfer_account_id is None

    delete_tx.set_permanent_removal(None)
    assert delete_tx.permanent_removal is None

    delete_tx.set_contract_id(None)
    assert delete_tx.contract_id is None


def test_constructor_parameter_combinations():
    """Test various constructor parameter combinations."""
    contract_id = ContractId(0, 0, 123)
    transfer_contract_id = ContractId(0, 0, 456)
    transfer_account_id = AccountId(0, 0, 789)

    # Test with transfer_contract_id only
    delete_tx = ContractDeleteTransaction(
        contract_id=contract_id,
        transfer_contract_id=transfer_contract_id,
    )
    assert delete_tx.contract_id == contract_id
    assert delete_tx.transfer_contract_id == transfer_contract_id
    assert delete_tx.transfer_account_id is None
    assert delete_tx.permanent_removal is None

    # Test with transfer_account_id only
    delete_tx = ContractDeleteTransaction(
        contract_id=contract_id,
        transfer_account_id=transfer_account_id,
    )
    assert delete_tx.contract_id == contract_id
    assert delete_tx.transfer_contract_id is None
    assert delete_tx.transfer_account_id == transfer_account_id
    assert delete_tx.permanent_removal is None

    # Test with permanent_removal only
    delete_tx = ContractDeleteTransaction(
        contract_id=contract_id,
        permanent_removal=True,
    )
    assert delete_tx.contract_id == contract_id
    assert delete_tx.transfer_contract_id is None
    assert delete_tx.transfer_account_id is None
    assert delete_tx.permanent_removal is True
