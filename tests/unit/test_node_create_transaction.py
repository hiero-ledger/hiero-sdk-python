"""
Test cases for the NodeCreateTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.nodes.node_create_transaction import (
    NodeCreateParams,
    NodeCreateTransaction,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def node_params():
    """Fixture for node create parameters."""
    return {
        "account_id": AccountId(0, 0, 123),
        "description": "test node",
        "gossip_endpoints": [Endpoint(domain_name="test.com", port=50211)],
        "service_endpoints": [Endpoint(domain_name="test1.com", port=50212)],
        "gossip_ca_certificate": b"test-ca-cert",
        "grpc_certificate_hash": b"test-cert-hash",
        "decline_reward": True,
        "admin_key": PrivateKey.generate_ed25519().public_key(),
        "grpc_web_proxy_endpoint": Endpoint(domain_name="test2.com", port=50213),
    }


def test_constructor_with_parameters(node_params):
    """Test creating a node create transaction with constructor parameters."""
    node_create_params = NodeCreateParams(
        account_id=node_params["account_id"],
        description=node_params["description"],
        gossip_endpoints=node_params["gossip_endpoints"],
        service_endpoints=node_params["service_endpoints"],
        gossip_ca_certificate=node_params["gossip_ca_certificate"],
        grpc_certificate_hash=node_params["grpc_certificate_hash"],
        admin_key=node_params["admin_key"],
        decline_reward=node_params["decline_reward"],
        grpc_web_proxy_endpoint=node_params["grpc_web_proxy_endpoint"],
    )

    node_tx = NodeCreateTransaction(node_create_params=node_create_params)

    assert node_tx.account_id == node_params["account_id"]
    assert node_tx.description == node_params["description"]
    assert node_tx.gossip_endpoints == node_params["gossip_endpoints"]
    assert node_tx.service_endpoints == node_params["service_endpoints"]
    assert node_tx.gossip_ca_certificate == node_params["gossip_ca_certificate"]
    assert node_tx.grpc_certificate_hash == node_params["grpc_certificate_hash"]
    assert node_tx.admin_key == node_params["admin_key"]
    assert node_tx.decline_reward == node_params["decline_reward"]
    assert node_tx.grpc_web_proxy_endpoint == node_params["grpc_web_proxy_endpoint"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    node_tx = NodeCreateTransaction()

    assert node_tx.account_id is None
    assert node_tx.description is None
    assert node_tx.gossip_endpoints == []
    assert node_tx.service_endpoints == []
    assert node_tx.gossip_ca_certificate is None
    assert node_tx.grpc_certificate_hash is None
    assert node_tx.admin_key is None
    assert node_tx.decline_reward is None
    assert node_tx.grpc_web_proxy_endpoint is None


def test_build_transaction_body_with_valid_parameters(mock_account_ids, node_params):
    """Test building a node create transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    node_create_params = NodeCreateParams(**node_params)
    node_tx = NodeCreateTransaction(node_create_params=node_create_params)

    # Set operator and node account IDs needed for building transaction body
    node_tx.operator_account_id = operator_id
    node_tx.node_account_id = node_account_id

    transaction_body = node_tx.build_transaction_body()

    # Verify the transaction body contains nodeCreate field
    assert transaction_body.HasField("nodeCreate")

    # Verify all fields are correctly set
    node_create = transaction_body.nodeCreate
    assert node_create.account_id == node_params["account_id"]._to_proto()
    assert node_create.description == node_params["description"]
    assert len(node_create.gossip_endpoint) == 1
    assert (
        node_create.gossip_endpoint[0] == node_params["gossip_endpoints"][0]._to_proto()
    )
    assert len(node_create.service_endpoint) == 1
    assert (
        node_create.service_endpoint[0] == node_params["service_endpoints"][0]._to_proto()
    )
    assert node_create.gossip_ca_certificate == node_params["gossip_ca_certificate"]
    assert node_create.grpc_certificate_hash == node_params["grpc_certificate_hash"]
    assert node_create.admin_key == node_params["admin_key"]._to_proto()
    assert node_create.decline_reward == node_params["decline_reward"]
    assert (
        node_create.grpc_proxy_endpoint
        == node_params["grpc_web_proxy_endpoint"]._to_proto()
    )


def test_build_scheduled_body(node_params):
    """Test building a schedulable node create transaction body."""
    node_create_params = NodeCreateParams(**node_params)
    node_tx = NodeCreateTransaction(node_create_params=node_create_params)

    schedulable_body = node_tx.build_scheduled_body()

    # Verify the correct type is returned
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with node create type
    assert schedulable_body.HasField("nodeCreate")

    # Verify fields in the schedulable body
    node_create = schedulable_body.nodeCreate
    assert node_create.account_id == node_params["account_id"]._to_proto()
    assert node_create.description == node_params["description"]
    assert len(node_create.gossip_endpoint) == 1
    assert (
        node_create.gossip_endpoint[0] == node_params["gossip_endpoints"][0]._to_proto()
    )
    assert len(node_create.service_endpoint) == 1
    assert (
        node_create.service_endpoint[0] == node_params["service_endpoints"][0]._to_proto()
    )
    assert node_create.gossip_ca_certificate == node_params["gossip_ca_certificate"]
    assert node_create.grpc_certificate_hash == node_params["grpc_certificate_hash"]
    assert node_create.admin_key == node_params["admin_key"]._to_proto()
    assert node_create.decline_reward == node_params["decline_reward"]
    assert (
        node_create.grpc_proxy_endpoint
        == node_params["grpc_web_proxy_endpoint"]._to_proto()
    )


def test_set_account_id(node_params):
    """Test setting account_id using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_account_id(node_params["account_id"])

    assert node_tx.account_id == node_params["account_id"]
    assert result is node_tx  # Should return self for method chaining


def test_set_description(node_params):
    """Test setting description using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_description(node_params["description"])

    assert node_tx.description == node_params["description"]
    assert result is node_tx  # Should return self for method chaining


def test_set_gossip_endpoints(node_params):
    """Test setting gossip_endpoints using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_gossip_endpoints(node_params["gossip_endpoints"])

    assert node_tx.gossip_endpoints == node_params["gossip_endpoints"]
    assert result is node_tx  # Should return self for method chaining


def test_set_service_endpoints(node_params):
    """Test setting service_endpoints using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_service_endpoints(node_params["service_endpoints"])

    assert node_tx.service_endpoints == node_params["service_endpoints"]
    assert result is node_tx  # Should return self for method chaining


def test_set_gossip_ca_certificate(node_params):
    """Test setting gossip_ca_certificate using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_gossip_ca_certificate(node_params["gossip_ca_certificate"])

    assert node_tx.gossip_ca_certificate == node_params["gossip_ca_certificate"]
    assert result is node_tx  # Should return self for method chaining


def test_set_grpc_certificate_hash(node_params):
    """Test setting grpc_certificate_hash using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_grpc_certificate_hash(node_params["grpc_certificate_hash"])

    assert node_tx.grpc_certificate_hash == node_params["grpc_certificate_hash"]
    assert result is node_tx  # Should return self for method chaining


def test_set_admin_key(node_params):
    """Test setting admin_key using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_admin_key(node_params["admin_key"])

    assert node_tx.admin_key == node_params["admin_key"]
    assert result is node_tx  # Should return self for method chaining


def test_set_decline_reward(node_params):
    """Test setting decline_reward using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_decline_reward(node_params["decline_reward"])

    assert node_tx.decline_reward == node_params["decline_reward"]
    assert result is node_tx  # Should return self for method chaining


def test_set_grpc_web_proxy_endpoint(node_params):
    """Test setting grpc_web_proxy_endpoint using the setter method."""
    node_tx = NodeCreateTransaction()

    result = node_tx.set_grpc_web_proxy_endpoint(node_params["grpc_web_proxy_endpoint"])

    assert node_tx.grpc_web_proxy_endpoint == node_params["grpc_web_proxy_endpoint"]
    assert result is node_tx  # Should return self for method chaining


def test_method_chaining_with_all_setters(node_params):
    """Test that all setter methods support method chaining."""
    node_tx = NodeCreateTransaction()

    result = (
        node_tx.set_account_id(node_params["account_id"])
        .set_description(node_params["description"])
        .set_gossip_endpoints(node_params["gossip_endpoints"])
        .set_service_endpoints(node_params["service_endpoints"])
        .set_gossip_ca_certificate(node_params["gossip_ca_certificate"])
        .set_grpc_certificate_hash(node_params["grpc_certificate_hash"])
        .set_admin_key(node_params["admin_key"])
        .set_decline_reward(node_params["decline_reward"])
        .set_grpc_web_proxy_endpoint(node_params["grpc_web_proxy_endpoint"])
    )

    assert result is node_tx
    assert node_tx.account_id == node_params["account_id"]
    assert node_tx.description == node_params["description"]
    assert node_tx.gossip_endpoints == node_params["gossip_endpoints"]
    assert node_tx.service_endpoints == node_params["service_endpoints"]
    assert node_tx.gossip_ca_certificate == node_params["gossip_ca_certificate"]
    assert node_tx.grpc_certificate_hash == node_params["grpc_certificate_hash"]
    assert node_tx.admin_key == node_params["admin_key"]
    assert node_tx.decline_reward == node_params["decline_reward"]
    assert node_tx.grpc_web_proxy_endpoint == node_params["grpc_web_proxy_endpoint"]


def test_set_methods_require_not_frozen(mock_client, node_params):
    """Test that setter methods raise exception when transaction is frozen."""
    node_tx = NodeCreateTransaction()
    node_tx.freeze_with(mock_client)

    test_cases = [
        ("set_account_id", node_params["account_id"]),
        ("set_description", node_params["description"]),
        ("set_gossip_endpoints", node_params["gossip_endpoints"]),
        ("set_service_endpoints", node_params["service_endpoints"]),
        ("set_gossip_ca_certificate", node_params["gossip_ca_certificate"]),
        ("set_grpc_certificate_hash", node_params["grpc_certificate_hash"]),
        ("set_admin_key", node_params["admin_key"]),
        ("set_decline_reward", node_params["decline_reward"]),
        ("set_grpc_web_proxy_endpoint", node_params["grpc_web_proxy_endpoint"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(node_tx, method_name)(value)


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    node_tx = NodeCreateTransaction()

    mock_channel = MagicMock()
    mock_address_book_stub = MagicMock()
    mock_channel.address_book = mock_address_book_stub

    method = node_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_address_book_stub.createNode


def test_sign_transaction(mock_client):
    """Test signing the node create transaction with a private key."""
    node_tx = NodeCreateTransaction()
    node_tx.set_account_id(AccountId(0, 0, 123))

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    node_tx.freeze_with(mock_client)
    node_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = node_tx._transaction_body_bytes[node_id]

    assert len(node_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = node_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client):
    """Test converting the node create transaction to protobuf format after signing."""
    node_tx = NodeCreateTransaction()
    node_tx.set_account_id(AccountId(0, 0, 123))

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    node_tx.freeze_with(mock_client)
    node_tx.sign(private_key)
    proto = node_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
