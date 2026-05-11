"""Tests for registered node transactions."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import transaction_receipt_pb2
from hiero_sdk_python.nodes.registered_node_create_transaction import RegisteredNodeCreateTransaction
from hiero_sdk_python.nodes.registered_node_delete_transaction import RegisteredNodeDeleteTransaction
from hiero_sdk_python.nodes.registered_node_update_transaction import RegisteredNodeUpdateTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt


pytestmark = pytest.mark.unit


def _make_block_endpoint():
    return BlockNodeServiceEndpoint(
        ip_address=b"\x7f\x00\x00\x01",
        port=8080,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.PUBLISH],
    )


def _make_mirror_endpoint():
    return MirrorNodeServiceEndpoint(
        domain_name="mirror.example.com",
        port=443,
        requires_tls=True,
    )


def _freeze(tx):
    """Freeze a transaction with minimal required fields."""
    tx.transaction_id = TransactionId.generate(AccountId(0, 0, 100))
    tx.node_account_id = AccountId(0, 0, 3)
    tx.freeze()
    return tx


# ---------------------------------------------------------------------------
# RegisteredNodeCreateTransaction
# ---------------------------------------------------------------------------


class TestRegisteredNodeCreateTransaction:
    def test_builds_proto_with_all_fields(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        key = PrivateKey.generate_ed25519().public_key()

        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(key)
        tx.set_description("test node")
        tx.set_service_endpoints([_make_block_endpoint()])

        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()

        assert body.HasField("registeredNodeCreate")
        pb = body.registeredNodeCreate
        assert pb.admin_key == key._to_proto()
        assert pb.description == "test node"
        assert len(pb.service_endpoint) == 1

    def test_multiple_service_endpoints(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids

        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.set_service_endpoints([_make_block_endpoint(), _make_mirror_endpoint()])

        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeCreate.service_endpoint) == 2

    def test_block_endpoint_with_multiple_apis(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        ep = BlockNodeServiceEndpoint(
            ip_address=b"\x7f\x00\x00\x01",
            port=9090,
            endpoint_apis=[BlockNodeApi.PUBLISH, BlockNodeApi.SUBSCRIBE_STREAM, BlockNodeApi.STATE_PROOF],
        )
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.set_service_endpoints([ep])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        block_node = body.registeredNodeCreate.service_endpoint[0].block_node
        assert len(block_node.endpoint_api) == 3

    def test_builds_schedulable_body(self):
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.set_service_endpoints([_make_block_endpoint()])
        scheduled = tx.build_scheduled_body()
        assert scheduled.HasField("registeredNodeCreate")

    def test_from_bytes_round_trip(self):
        key = PrivateKey.generate_ed25519().public_key()
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(key)
        tx.set_description("round trip")
        tx.set_service_endpoints([_make_block_endpoint(), _make_mirror_endpoint()])

        _freeze(tx)
        restored = Transaction.from_bytes(tx.to_bytes())

        assert isinstance(restored, RegisteredNodeCreateTransaction)
        assert restored.admin_key.to_bytes_raw() == key.to_bytes_raw()
        assert restored.description == "round trip"
        assert len(restored.service_endpoints) == 2
        assert isinstance(restored.service_endpoints[0], BlockNodeServiceEndpoint)
        assert isinstance(restored.service_endpoints[1], MirrorNodeServiceEndpoint)

    def test_builds_without_endpoints(self, mock_account_ids):
        """Building without endpoints succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeCreate.service_endpoint) == 0

    def test_builds_with_many_endpoints(self, mock_account_ids):
        """Building with many endpoints succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        endpoints = [_make_mirror_endpoint() for _ in range(51)]
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.set_service_endpoints(endpoints)
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeCreate.service_endpoint) == 51

    def test_builds_with_long_description(self, mock_account_ids):
        """Building with long description succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeCreateTransaction()
        tx.set_admin_key(PrivateKey.generate_ed25519().public_key())
        tx.set_description("x" * 101)
        tx.set_service_endpoints([_make_block_endpoint()])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.registeredNodeCreate.description == "x" * 101

    def test_add_service_endpoint(self):
        tx = RegisteredNodeCreateTransaction()
        tx.add_service_endpoint(_make_block_endpoint())
        tx.add_service_endpoint(_make_mirror_endpoint())
        assert len(tx.service_endpoints) == 2


# ---------------------------------------------------------------------------
# RegisteredNodeUpdateTransaction
# ---------------------------------------------------------------------------


class TestRegisteredNodeUpdateTransaction:
    def test_builds_proto_with_registered_node_id(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(42)
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.HasField("registeredNodeUpdate")
        assert body.registeredNodeUpdate.registered_node_id == 42

    def test_updates_admin_key(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        key = PrivateKey.generate_ed25519().public_key()
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.set_admin_key(key)
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.registeredNodeUpdate.admin_key == key._to_proto()

    def test_updates_description(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.set_description("updated desc")
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.registeredNodeUpdate.description.value == "updated desc"

    def test_replaces_endpoints_when_provided(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.set_service_endpoints([_make_block_endpoint(), _make_mirror_endpoint()])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeUpdate.service_endpoint) == 2

    def test_does_not_serialize_endpoints_when_unset(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeUpdate.service_endpoint) == 0

    def test_builds_schedulable_body(self):
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        scheduled = tx.build_scheduled_body()
        assert scheduled.HasField("registeredNodeUpdate")

    def test_from_bytes_round_trip(self):
        key = PrivateKey.generate_ed25519().public_key()
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(99)
        tx.set_admin_key(key)
        tx.set_description("updated")
        tx.set_service_endpoints([_make_mirror_endpoint()])

        _freeze(tx)
        restored = Transaction.from_bytes(tx.to_bytes())

        assert isinstance(restored, RegisteredNodeUpdateTransaction)
        assert restored.registered_node_id == 99
        assert restored.admin_key.to_bytes_raw() == key.to_bytes_raw()
        assert restored.description == "updated"
        assert len(restored.service_endpoints) == 1
        assert isinstance(restored.service_endpoints[0], MirrorNodeServiceEndpoint)

    def test_builds_without_registered_node_id(self, mock_account_ids):
        """Building without registered_node_id succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.registeredNodeUpdate.registered_node_id == 0

    def test_builds_with_empty_endpoints(self, mock_account_ids):
        """Building with empty endpoints succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.set_service_endpoints([])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeUpdate.service_endpoint) == 0

    def test_builds_with_many_endpoints(self, mock_account_ids):
        """Building with many endpoints succeeds; validation is delegated to consensus node."""
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeUpdateTransaction()
        tx.set_registered_node_id(1)
        tx.set_service_endpoints([_make_mirror_endpoint() for _ in range(51)])
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert len(body.registeredNodeUpdate.service_endpoint) == 51


# ---------------------------------------------------------------------------
# RegisteredNodeDeleteTransaction
# ---------------------------------------------------------------------------


class TestRegisteredNodeDeleteTransaction:
    def test_builds_proto_with_registered_node_id(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(7)
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id
        body = tx.build_transaction_body()
        assert body.HasField("registeredNodeDelete")
        assert body.registeredNodeDelete.registered_node_id == 7

    def test_builds_schedulable_body(self):
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(7)
        scheduled = tx.build_scheduled_body()
        assert scheduled.HasField("registeredNodeDelete")
        assert scheduled.registeredNodeDelete.registered_node_id == 7

    def test_from_bytes_round_trip(self):
        tx = RegisteredNodeDeleteTransaction()
        tx.set_registered_node_id(42)

        _freeze(tx)
        restored = Transaction.from_bytes(tx.to_bytes())

        assert isinstance(restored, RegisteredNodeDeleteTransaction)
        assert restored.registered_node_id == 42

    def test_fails_when_registered_node_id_missing(self, mock_account_ids):
        operator_id, _, node_account_id, _, _ = mock_account_ids
        tx = RegisteredNodeDeleteTransaction()
        tx.operator_account_id = operator_id
        tx.node_account_id = node_account_id

        with pytest.raises(ValueError, match="registered_node_id"):
            tx.build_transaction_body()


# ---------------------------------------------------------------------------
# TransactionReceipt.registered_node_id
# ---------------------------------------------------------------------------


class TestTransactionReceiptRegisteredNodeId:
    def test_parses_when_present(self):
        proto = transaction_receipt_pb2.TransactionReceipt(registered_node_id=123)
        receipt = TransactionReceipt(proto)
        assert receipt.registered_node_id == 123

    def test_none_when_absent(self):
        proto = transaction_receipt_pb2.TransactionReceipt()
        receipt = TransactionReceipt(proto)
        assert receipt.registered_node_id is None


# ---------------------------------------------------------------------------
# Transaction deserialization mapping
# ---------------------------------------------------------------------------


class TestTransactionDeserialization:
    def test_resolves_registered_node_create(self):
        cls = Transaction._get_transaction_class("registeredNodeCreate")
        assert cls is RegisteredNodeCreateTransaction

    def test_resolves_registered_node_update(self):
        cls = Transaction._get_transaction_class("registeredNodeUpdate")
        assert cls is RegisteredNodeUpdateTransaction

    def test_resolves_registered_node_delete(self):
        cls = Transaction._get_transaction_class("registeredNodeDelete")
        assert cls is RegisteredNodeDeleteTransaction
