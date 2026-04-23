"""Integration tests for the registered node lifecycle."""

from __future__ import annotations

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import (
    BlockNodeServiceEndpoint,
)
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateTransaction,
)


@pytest.mark.skip(
    reason="HIP-1137 registered-node lifecycle E2E requires network support that is not available in CI yet."
)
def test_registered_node_lifecycle_requires_network_support():
    """Document the intended create-update-associate-delete lifecycle."""
    endpoint = BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_api=BlockNodeApi.PUBLISH,
    )

    create_transaction = RegisteredNodeCreateTransaction().add_service_endpoint(endpoint)
    update_transaction = RegisteredNodeUpdateTransaction().set_registered_node_id(1).set_description("updated")
    associate_transaction = NodeUpdateTransaction().set_node_id(3).add_associated_registered_node(1)
    delete_transaction = RegisteredNodeDeleteTransaction().set_registered_node_id(1)

    assert create_transaction is not None
    assert update_transaction is not None
    assert associate_transaction is not None
    assert delete_transaction is not None
