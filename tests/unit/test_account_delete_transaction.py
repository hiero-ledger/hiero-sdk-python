"""
Test cases for the AccountDeleteTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def delete_params():
    """Fixture for account delete parameters."""
    return {
        "account_id": AccountId(0, 0, 123),
        "transfer_account_id": AccountId(0, 0, 456),
    }


def test_constructor_with_parameters(delete_params):
    """Test creating an account delete transaction with constructor parameters."""
    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

    assert delete_tx.account_id == delete_params["account_id"]
    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]


def test_constructor_with_account_id_only(delete_params):
    """Test creating an account delete transaction with only account_id."""
    delete_tx = AccountDeleteTransaction(account_id=delete_params["account_id"])

    assert delete_tx.account_id == delete_params["account_id"]
    assert delete_tx.transfer_account_id is None


def test_constructor_with_transfer_account_id_only(delete_params):
    """Test creating an account delete transaction with only transfer_account_id."""
    delete_tx = AccountDeleteTransaction(
        transfer_account_id=delete_params["transfer_account_id"]
    )

    assert delete_tx.account_id is None
    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    delete_tx = AccountDeleteTransaction()

    assert delete_tx.account_id is None
    assert delete_tx.transfer_account_id is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, delete_params):
    """Test building an account delete transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

    # Set operator and node account IDs needed for building transaction body
    delete_tx.operator_account_id = operator_id
    delete_tx.node_account_id = node_account_id

    transaction_body = delete_tx.build_transaction_body()

    assert (
        transaction_body.cryptoDelete.deleteAccountID
        == delete_params["account_id"]._to_proto()
    )
    assert (
        transaction_body.cryptoDelete.transferAccountID
        == delete_params["transfer_account_id"]._to_proto()
    )


def test_build_transaction_body_missing_account_id():
    """Test that build_transaction_body raises ValueError when account_id is missing."""
    delete_tx = AccountDeleteTransaction()

    with pytest.raises(ValueError, match="Missing required AccountID"):
        delete_tx.build_transaction_body()


def test_build_transaction_body_missing_transfer_account_id():
    """Test that build_transaction_body raises ValueError when transfer_account_id is missing."""
    delete_tx = AccountDeleteTransaction(account_id=AccountId(0, 0, 123))

    with pytest.raises(ValueError, match="Missing AccountID for transfer"):
        delete_tx.build_transaction_body()


def test_set_account_id(delete_params):
    """Test setting account_id using the setter method."""
    delete_tx = AccountDeleteTransaction()

    result = delete_tx.set_account_id(delete_params["account_id"])

    assert delete_tx.account_id == delete_params["account_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_set_transfer_account_id(delete_params):
    """Test setting transfer_account_id using the setter method."""
    delete_tx = AccountDeleteTransaction()

    result = delete_tx.set_transfer_account_id(delete_params["transfer_account_id"])

    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]
    assert result is delete_tx  # Should return self for method chaining


def test_method_chaining_with_all_setters(delete_params):
    """Test that all setter methods support method chaining."""
    delete_tx = AccountDeleteTransaction()

    result = delete_tx.set_account_id(
        delete_params["account_id"]
    ).set_transfer_account_id(delete_params["transfer_account_id"])

    assert result is delete_tx
    assert delete_tx.account_id == delete_params["account_id"]
    assert delete_tx.transfer_account_id == delete_params["transfer_account_id"]


def test_method_chaining_partial_setters(delete_params):
    """Test method chaining with only some setters."""
    delete_tx = AccountDeleteTransaction()

    result = delete_tx.set_account_id(delete_params["account_id"])

    assert result is delete_tx
    assert delete_tx.account_id == delete_params["account_id"]
    assert delete_tx.transfer_account_id is None


def test_set_methods_require_not_frozen(mock_client, delete_params):
    """Test that setter methods raise exception when transaction is frozen."""
    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )
    delete_tx.freeze_with(mock_client)

    test_cases = [
        ("set_account_id", delete_params["account_id"]),
        ("set_transfer_account_id", delete_params["transfer_account_id"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(delete_tx, method_name)(value)


def test_sign_transaction(mock_client, delete_params):
    """Test signing the account delete transaction with a private key."""
    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

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
    """Test converting the account delete transaction to protobuf format after signing."""
    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

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
    delete_tx = AccountDeleteTransaction()

    mock_channel = MagicMock()
    mock_crypto_stub = MagicMock()
    mock_channel.crypto = mock_crypto_stub

    method = delete_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_crypto_stub.cryptoDelete


def test_parameter_validation_types(delete_params):
    """Test that parameters accept the correct types."""
    delete_tx = AccountDeleteTransaction()

    # Test with valid types
    delete_tx.set_account_id(delete_params["account_id"])
    assert isinstance(delete_tx.account_id, AccountId)

    delete_tx.set_transfer_account_id(delete_params["transfer_account_id"])
    assert isinstance(delete_tx.transfer_account_id, AccountId)


def test_build_scheduled_body(delete_params):
    """Test building a schedulable account delete transaction body."""
    delete_tx = AccountDeleteTransaction(
        account_id=delete_params["account_id"],
        transfer_account_id=delete_params["transfer_account_id"],
    )

    schedulable_body = delete_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with account delete type
    assert schedulable_body.HasField("cryptoDelete")

    # Verify fields in the schedulable body
    assert (
        schedulable_body.cryptoDelete.deleteAccountID
        == delete_params["account_id"]._to_proto()
    )
    assert (
        schedulable_body.cryptoDelete.transferAccountID
        == delete_params["transfer_account_id"]._to_proto()
    )


def test_parameter_validation_none_values():
    """Test that parameters can be set to None."""
    delete_tx = AccountDeleteTransaction(
        account_id=AccountId(0, 0, 123),
        transfer_account_id=AccountId(0, 0, 456),
    )

    # All parameters can be set to None
    delete_tx.set_account_id(None)
    assert delete_tx.account_id is None

    delete_tx.set_transfer_account_id(None)
    assert delete_tx.transfer_account_id is None


def test_constructor_parameter_combinations():
    """Test various constructor parameter combinations."""
    account_id = AccountId(0, 0, 123)
    transfer_account_id = AccountId(0, 0, 456)

    # Test with account_id only
    delete_tx = AccountDeleteTransaction(account_id=account_id)
    assert delete_tx.account_id == account_id
    assert delete_tx.transfer_account_id is None

    # Test with transfer_account_id only
    delete_tx = AccountDeleteTransaction(transfer_account_id=transfer_account_id)
    assert delete_tx.account_id is None
    assert delete_tx.transfer_account_id == transfer_account_id

    # Test with both parameters
    delete_tx = AccountDeleteTransaction(
        account_id=account_id,
        transfer_account_id=transfer_account_id,
    )
    assert delete_tx.account_id == account_id
    assert delete_tx.transfer_account_id == transfer_account_id

    # Test with no parameters
    delete_tx = AccountDeleteTransaction()
    assert delete_tx.account_id is None
    assert delete_tx.transfer_account_id is None
