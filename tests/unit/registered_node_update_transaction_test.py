"""Unit tests for RegisteredNodeUpdateTransaction."""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateParams,
    RegisteredNodeUpdateTransaction,
)
from hiero_sdk_python.transaction.transaction import Transaction

pytestmark = pytest.mark.unit


@pytest.fixture
def registered_node_update_params():
    """Fixture for registered node update parameters."""
    return RegisteredNodeUpdateParams(
        registered_node_id=7,
        admin_key=PrivateKey.generate_ed25519().public_key(),
        description="updated block node",
        service_endpoints=[
            BlockNodeServiceEndpoint(
                domain_name="block.example.com",
                port=443,
                requires_tls=True,
                endpoint_api=BlockNodeApi.SUBSCRIBE_STREAM,
            )
        ],
    )


def test_constructor_with_parameters(registered_node_update_params):
    """The constructor should populate all fields."""
    transaction = RegisteredNodeUpdateTransaction(registered_node_update_params)

    assert transaction.registered_node_id == registered_node_update_params.registered_node_id
    assert transaction.admin_key == registered_node_update_params.admin_key
    assert transaction.description == registered_node_update_params.description
    assert transaction.service_endpoints == registered_node_update_params.service_endpoints


def test_constructor_default_values():
    """Default construction should produce empty optional fields."""
    transaction = RegisteredNodeUpdateTransaction()

    assert transaction.registered_node_id is None
    assert transaction.admin_key is None
    assert transaction.description is None
    assert transaction.service_endpoints == []


def test_build_transaction_body(mock_account_ids, registered_node_update_params):
    """Building a transaction body should populate the registered-node oneof."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeUpdateTransaction(registered_node_update_params)
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    transaction_body = transaction.build_transaction_body()

    assert transaction_body.HasField("registeredNodeUpdate")
    registered_node_update = transaction_body.registeredNodeUpdate
    assert registered_node_update.registered_node_id == registered_node_update_params.registered_node_id
    assert registered_node_update.admin_key == registered_node_update_params.admin_key._to_proto()
    assert registered_node_update.description.value == registered_node_update_params.description
    assert len(registered_node_update.service_endpoint) == 1
    assert registered_node_update.service_endpoint[0] == registered_node_update_params.service_endpoints[0]._to_proto()


def test_build_scheduled_body(registered_node_update_params):
    """Registered node update transactions should be schedulable."""
    transaction = RegisteredNodeUpdateTransaction(registered_node_update_params)

    scheduled_body = transaction.build_scheduled_body()

    assert isinstance(scheduled_body, SchedulableTransactionBody)
    assert scheduled_body.HasField("registeredNodeUpdate")


def test_add_service_endpoint():
    """Service endpoints should be appendable through the fluent helper."""
    transaction = RegisteredNodeUpdateTransaction()
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        endpoint_api=BlockNodeApi.STATUS,
    )

    result = transaction.add_service_endpoint(endpoint)

    assert result is transaction
    assert transaction.service_endpoints == [endpoint]


def test_build_transaction_body_requires_registered_node_id(mock_account_ids):
    """A registered node id must be provided for updates."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    transaction = RegisteredNodeUpdateTransaction()
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id

    with pytest.raises(ValueError, match="Missing required RegisteredNodeID"):
        transaction.build_transaction_body()


def test_build_transaction_body_rejects_more_than_50_service_endpoints(
    mock_account_ids,
):
    """Update transactions should reject oversized endpoint lists."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        endpoint_api=BlockNodeApi.STATUS,
    )
    transaction = RegisteredNodeUpdateTransaction().set_registered_node_id(7)
    transaction.operator_account_id = operator_id
    transaction.node_account_id = node_account_id
    transaction.set_service_endpoints([endpoint] * 51)

    with pytest.raises(ValueError, match="A maximum of 50 service endpoints is allowed."):
        transaction.build_transaction_body()


def test_get_method():
    """The transaction should use the registered-node update RPC."""
    transaction = RegisteredNodeUpdateTransaction()
    channel = MagicMock()
    channel.address_book = MagicMock()

    method = transaction._get_method(channel)

    assert method.query is None
    assert method.transaction == channel.address_book.updateRegisteredNode


def test_from_bytes_restores_registered_node_update_transaction(mock_client, registered_node_update_params):
    """Transaction.from_bytes should restore the registered-node update type."""
    transaction = RegisteredNodeUpdateTransaction(registered_node_update_params)
    transaction.freeze_with(mock_client)

    restored = Transaction.from_bytes(transaction.to_bytes())

    assert isinstance(restored, RegisteredNodeUpdateTransaction)
    assert restored.registered_node_id == registered_node_update_params.registered_node_id
    assert restored.description == registered_node_update_params.description
    assert restored.admin_key == registered_node_update_params.admin_key
    assert len(restored.service_endpoints) == 1
