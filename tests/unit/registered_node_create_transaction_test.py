"""Unit tests for RegisteredNodeCreateTransaction."""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.threshold_key import ThresholdKey
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateParams,
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.transaction.transaction import Transaction

pytestmark = pytest.mark.unit


@pytest.fixture
def service_endpoint():
    """Fixture for a registered block node endpoint."""
    return BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.PUBLISH,
    )


@pytest.fixture
def registered_node_create_params(service_endpoint):
    """Fixture for registered node create parameters."""
    return RegisteredNodeCreateParams(
        admin_key=PrivateKey.generate_ed25519().public_key(),
        description="block node",
        service_endpoints=[service_endpoint],
    )


def test_constructor_with_parameters(registered_node_create_params):
    """The constructor should populate all fields."""
    transaction = RegisteredNodeCreateTransaction(registered_node_create_params)

    assert transaction.admin_key == registered_node_create_params.admin_key
    assert transaction.description == registered_node_create_params.description
    assert transaction.service_endpoints == registered_node_create_params.service_endpoints


def test_constructor_default_values():
    """Default construction should produce empty optional fields."""
    transaction = RegisteredNodeCreateTransaction()

    assert transaction.admin_key is None
    assert transaction.description is None
    assert transaction.service_endpoints == []


def test_build_transaction_body(mock_account_ids, registered_node_create_params):
    """Building a transaction body should populate the registered-node oneof."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeCreateTransaction(registered_node_create_params)
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    transaction_body = transaction.build_transaction_body()

    assert transaction_body.HasField("registeredNodeCreate")
    registered_node_create = transaction_body.registeredNodeCreate
    assert registered_node_create.admin_key == registered_node_create_params.admin_key._to_proto()
    assert registered_node_create.description == registered_node_create_params.description
    assert len(registered_node_create.service_endpoint) == 1
    assert registered_node_create.service_endpoint[0] == registered_node_create_params.service_endpoints[0]._to_proto()


def test_build_scheduled_body(registered_node_create_params):
    """Registered node create transactions should be schedulable."""
    transaction = RegisteredNodeCreateTransaction(registered_node_create_params)

    scheduled_body = transaction.build_scheduled_body()

    assert isinstance(scheduled_body, SchedulableTransactionBody)
    assert scheduled_body.HasField("registeredNodeCreate")


def test_add_service_endpoint(service_endpoint):
    """Service endpoints should be appendable through the fluent helper."""
    transaction = RegisteredNodeCreateTransaction()

    result = transaction.add_service_endpoint(service_endpoint)

    assert result is transaction
    assert transaction.service_endpoints == [service_endpoint]


def test_setters_require_not_frozen(mock_client, service_endpoint):
    """Mutating setters should fail once the transaction is frozen."""
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(PrivateKey.generate_ed25519().public_key())
        .add_service_endpoint(service_endpoint)
    )
    transaction.freeze_with(mock_client)

    with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
        transaction.set_description("updated")


def test_get_method():
    """The transaction should use the registered-node create RPC."""
    transaction = RegisteredNodeCreateTransaction()
    channel = MagicMock()
    channel.address_book = MagicMock()

    method = transaction._get_method(channel)

    assert method.query is None
    assert method.transaction == channel.address_book.createRegisteredNode


def test_build_transaction_body_requires_service_endpoint(mock_account_ids):
    """At least one service endpoint must be provided."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeCreateTransaction().set_admin_key(PrivateKey.generate_ed25519().public_key())
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="At least one service endpoint is required."):
        transaction.build_transaction_body()


def test_build_transaction_body_requires_admin_key(mock_account_ids, service_endpoint):
    """An admin key must be provided for registered node creation."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeCreateTransaction().add_service_endpoint(service_endpoint)
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required admin_key"):
        transaction.build_transaction_body()


def test_build_transaction_body_rejects_more_than_50_service_endpoints(mock_account_ids, service_endpoint):
    """Create transactions should reject oversized endpoint lists."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeCreateTransaction().set_admin_key(PrivateKey.generate_ed25519().public_key())
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id
    transaction.set_service_endpoints([service_endpoint] * 51)

    with pytest.raises(ValueError, match="A maximum of 50 service endpoints is allowed."):
        transaction.build_transaction_body()


def test_build_transaction_body_accepts_private_key_admin_key(mock_account_ids, service_endpoint):
    """Private keys should be accepted and serialized as public keys."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    admin_key = PrivateKey.generate_ed25519()
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key)
        .add_service_endpoint(service_endpoint)
    )
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    transaction_body = transaction.build_transaction_body()

    assert transaction_body.registeredNodeCreate.admin_key == admin_key.public_key()._to_proto()


def test_build_transaction_body_accepts_key_list_admin_key(mock_account_ids, service_endpoint):
    """Composite key lists should be accepted for admin_key."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    first_key = PrivateKey.generate_ed25519().public_key()
    second_key = PrivateKey.generate_ecdsa().public_key()
    admin_key = KeyList([first_key, second_key])
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key)
        .add_service_endpoint(service_endpoint)
    )
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    transaction_body = transaction.build_transaction_body()

    assert transaction_body.registeredNodeCreate.admin_key == admin_key._to_proto()


def test_build_transaction_body_rejects_descriptions_over_100_utf8_bytes(mock_account_ids, service_endpoint):
    """Descriptions must be capped at 100 UTF-8 bytes."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(PrivateKey.generate_ed25519().public_key())
        .set_description("é" * 51)
        .add_service_endpoint(service_endpoint)
    )
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Description must not exceed 100 UTF-8 bytes."):
        transaction.build_transaction_body()


def test_build_transaction_body_rejects_empty_key_list_admin_key(mock_account_ids, service_endpoint):
    """Empty key lists should be rejected for admin_key."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(KeyList())
        .add_service_endpoint(service_endpoint)
    )
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="admin_key must not contain an empty KeyList."):
        transaction.build_transaction_body()


def test_build_transaction_body_rejects_threshold_key_with_empty_child_key_list(
    mock_account_ids, service_endpoint
):
    """Composite admin keys should also reject empty child key lists."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(ThresholdKey(threshold=1, keys=KeyList()))
        .add_service_endpoint(service_endpoint)
    )
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="admin_key must not contain an empty KeyList."):
        transaction.build_transaction_body()


def test_from_bytes_restores_registered_node_create_transaction(mock_client, registered_node_create_params):
    """Transaction.from_bytes should restore the registered-node create type."""
    transaction = RegisteredNodeCreateTransaction(registered_node_create_params)
    transaction.freeze_with(mock_client)

    restored = Transaction.from_bytes(transaction.to_bytes())

    assert isinstance(restored, RegisteredNodeCreateTransaction)
    assert restored.description == registered_node_create_params.description
    assert restored.admin_key == registered_node_create_params.admin_key
    assert len(restored.service_endpoints) == 1
    assert isinstance(restored.service_endpoints[0], RegisteredServiceEndpoint)


def test_from_bytes_restores_registered_node_create_with_key_list_admin_key(mock_client, service_endpoint):
    """Composite admin keys should round-trip through registered node create bytes."""
    admin_key = KeyList(
        [
            PrivateKey.generate_ed25519().public_key(),
            PrivateKey.generate_ecdsa().public_key(),
        ]
    )
    transaction = (
        RegisteredNodeCreateTransaction()
        .set_admin_key(admin_key)
        .set_description("block node")
        .add_service_endpoint(service_endpoint)
    )
    transaction.freeze_with(mock_client)

    restored = Transaction.from_bytes(transaction.to_bytes())

    assert isinstance(restored, RegisteredNodeCreateTransaction)
    assert restored.admin_key == admin_key
