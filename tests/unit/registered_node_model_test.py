from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.address_book.block_node_api import BlockNodeApi
from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.address_book.registered_node_address_book import RegisteredNodeAddressBook
from hiero_sdk_python.address_book.registered_node_address_book_query import (
    RegisteredNodeAddressBookQuery,
)
from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.state.addressbook.registered_node_pb2 import (
    RegisteredNode as RegisteredNodeProto,
)


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _make_key():
    """Return a fresh Ed25519 key pair for testing."""
    private = PrivateKey.generate()
    return private.public_key()


def _block_endpoint() -> BlockNodeServiceEndpoint:
    return BlockNodeServiceEndpoint(
        domain_name="block.example.com",
        port=443,
        requires_tls=True,
        endpoint_apis=[BlockNodeApi.PUBLISH, BlockNodeApi.SUBSCRIBE_STREAM],
    )


def _mirror_endpoint() -> MirrorNodeServiceEndpoint:
    return MirrorNodeServiceEndpoint(
        domain_name="mirror.example.com",
        port=5600,
        requires_tls=True,
    )


def _rpc_relay_endpoint() -> RpcRelayServiceEndpoint:
    return RpcRelayServiceEndpoint(
        domain_name="rpc.example.com",
        port=8545,
        requires_tls=False,
    )


def _general_endpoint() -> GeneralServiceEndpoint:
    return GeneralServiceEndpoint(
        domain_name="general.example.com",
        port=9000,
        requires_tls=False,
        description="general node",
    )


# ---------------------------------------------------------------------------
# RegisteredNode
# ---------------------------------------------------------------------------


class TestRegisteredNode:
    def test_from_proto_minimal(self):
        proto = RegisteredNodeProto(registered_node_id=42)
        node = RegisteredNode._from_proto(proto)
        assert node.registered_node_id == 42
        assert node.admin_key is None
        assert node.description is None
        assert node.service_endpoints == ()

    def test_from_proto_with_admin_key(self):
        pub = _make_key()
        proto = RegisteredNodeProto(
            registered_node_id=1,
            admin_key=pub._to_proto(),
        )
        node = RegisteredNode._from_proto(proto)
        assert node.admin_key is not None
        assert node.admin_key.to_bytes_raw() == pub.to_bytes_raw()

    def test_from_proto_with_description(self):
        proto = RegisteredNodeProto(
            registered_node_id=5,
            description="test node",
        )
        node = RegisteredNode._from_proto(proto)
        assert node.description == "test node"

    def test_from_proto_with_service_endpoints(self):
        block_ep = _block_endpoint()
        mirror_ep = _mirror_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[block_ep._to_proto(), mirror_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert len(node.service_endpoints) == 2

    def test_from_proto_block_node_endpoint_type(self):
        block_ep = _block_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[block_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], BlockNodeServiceEndpoint)

    def test_from_proto_mirror_node_endpoint_type(self):
        mirror_ep = _mirror_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[mirror_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], MirrorNodeServiceEndpoint)

    def test_from_proto_rpc_relay_endpoint_type(self):
        rpc_ep = _rpc_relay_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[rpc_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], RpcRelayServiceEndpoint)

    def test_from_proto_general_endpoint_type(self):
        gen_ep = _general_endpoint()
        proto = RegisteredNodeProto(
            registered_node_id=10,
            service_endpoint=[gen_ep._to_proto()],
        )
        node = RegisteredNode._from_proto(proto)
        assert isinstance(node.service_endpoints[0], GeneralServiceEndpoint)

    def test_to_proto_round_trip(self):
        pub = _make_key()
        mirror_ep = _mirror_endpoint()
        node = RegisteredNode(
            registered_node_id=7,
            admin_key=pub,
            description="round-trip",
            service_endpoints=(mirror_ep,),
        )
        proto = node._to_proto()
        restored = RegisteredNode._from_proto(proto)
        assert restored.registered_node_id == 7
        assert restored.admin_key.to_bytes_raw() == pub.to_bytes_raw()
        assert restored.description == "round-trip"
        assert len(restored.service_endpoints) == 1

    def test_rejects_zero_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=0)

    def test_rejects_negative_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=-3)

    def test_rejects_non_int_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id="abc")  # type: ignore[arg-type]

    def test_rejects_bool_id(self):
        with pytest.raises(ValueError, match="positive integer"):
            RegisteredNode(registered_node_id=True)

    def test_immutable_service_endpoints(self):
        node = RegisteredNode(registered_node_id=1, service_endpoints=[_mirror_endpoint()])
        assert isinstance(node.service_endpoints, tuple)

    def test_repr(self):
        node = RegisteredNode(registered_node_id=42, description="hello")
        r = repr(node)
        assert "42" in r
        assert "hello" in r

    def test_from_dict_minimal(self):
        data = {"registered_node_id": 42}
        node = RegisteredNode._from_dict(data)
        assert node.registered_node_id == 42
        assert node.admin_key is None
        assert node.description is None
        assert node.service_endpoints == ()

    def test_from_dict_with_admin_key_ed25519(self):
        pub = _make_key()
        data = {
            "registered_node_id": 1,
            "admin_key": {"_type": "ED25519", "key": pub.to_string_raw()},
        }
        node = RegisteredNode._from_dict(data)
        assert node.admin_key is not None

    def test_from_dict_with_description(self):
        data = {"registered_node_id": 5, "description": "test node"}
        node = RegisteredNode._from_dict(data)
        assert node.description == "test node"

    def test_from_dict_with_mirror_endpoint(self):
        data = {
            "registered_node_id": 10,
            "service_endpoints": [
                {
                    "domain_name": "mirror.example.com",
                    "port": 5600,
                    "requires_tls": True,
                    "type": "MIRROR_NODE",
                }
            ],
        }
        node = RegisteredNode._from_dict(data)
        assert len(node.service_endpoints) == 1
        assert isinstance(node.service_endpoints[0], MirrorNodeServiceEndpoint)

    def test_from_dict_with_block_endpoint(self):
        data = {
            "registered_node_id": 10,
            "service_endpoints": [
                {
                    "domain_name": "block.example.com",
                    "port": 443,
                    "requires_tls": True,
                    "type": "BLOCK_NODE",
                    "block_node": {"endpoint_apis": ["PUBLISH", "SUBSCRIBE_STREAM"]},
                }
            ],
        }
        node = RegisteredNode._from_dict(data)
        ep = node.service_endpoints[0]
        assert isinstance(ep, BlockNodeServiceEndpoint)
        assert BlockNodeApi.PUBLISH in ep.endpoint_apis

    def test_from_dict_with_general_endpoint(self):
        data = {
            "registered_node_id": 10,
            "service_endpoints": [
                {
                    "domain_name": "general.example.com",
                    "port": 9000,
                    "requires_tls": False,
                    "type": "GENERAL_SERVICE",
                    "general_service": {"description": "my service"},
                }
            ],
        }
        node = RegisteredNode._from_dict(data)
        ep = node.service_endpoints[0]
        assert isinstance(ep, GeneralServiceEndpoint)
        assert ep.description == "my service"

    def test_from_dict_with_rpc_relay_endpoint(self):
        data = {
            "registered_node_id": 10,
            "service_endpoints": [
                {
                    "domain_name": "rpc.example.com",
                    "port": 8545,
                    "requires_tls": False,
                    "type": "RPC_RELAY",
                }
            ],
        }
        node = RegisteredNode._from_dict(data)
        assert isinstance(node.service_endpoints[0], RpcRelayServiceEndpoint)


# ---------------------------------------------------------------------------
# RegisteredNodeAddressBook
# ---------------------------------------------------------------------------


class TestRegisteredNodeAddressBook:
    def test_empty(self):
        book = RegisteredNodeAddressBook()
        assert len(book) == 0
        assert list(book) == []

    def test_multiple_nodes(self):
        nodes = (
            RegisteredNode(registered_node_id=1),
            RegisteredNode(registered_node_id=2),
            RegisteredNode(registered_node_id=3),
        )
        book = RegisteredNodeAddressBook(nodes=nodes)
        assert len(book) == 3
        assert book[0].registered_node_id == 1
        assert book[2].registered_node_id == 3

    def test_iteration(self):
        nodes = (
            RegisteredNode(registered_node_id=10),
            RegisteredNode(registered_node_id=20),
        )
        book = RegisteredNodeAddressBook(nodes=nodes)
        ids = [n.registered_node_id for n in book]
        assert ids == [10, 20]

    def test_len(self):
        book = RegisteredNodeAddressBook(nodes=(RegisteredNode(registered_node_id=1),))
        assert len(book) == 1

    def test_repr(self):
        book = RegisteredNodeAddressBook(
            nodes=(RegisteredNode(registered_node_id=1), RegisteredNode(registered_node_id=2))
        )
        assert "2" in repr(book)

    def test_nodes_property_is_tuple(self):
        book = RegisteredNodeAddressBook(nodes=[RegisteredNode(registered_node_id=1)])
        assert isinstance(book.nodes, tuple)


# ---------------------------------------------------------------------------
# RegisteredNodeAddressBookQuery
# ---------------------------------------------------------------------------


class TestRegisteredNodeAddressBookQuery:
    def test_importable(self):
        q = RegisteredNodeAddressBookQuery()
        assert q is not None

    def test_execute_rejects_none_client(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="client must not be None"):
            q.execute(None)

    def test_set_max_registered_node_count(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_max_registered_node_count(10)
        assert result is q  # chaining

    def test_set_max_registered_node_count_rejects_zero(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(0)

    def test_set_max_registered_node_count_rejects_negative(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(-1)

    def test_set_max_registered_node_count_rejects_bool(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(True)

    def test_set_max_registered_node_count_rejects_float(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count(1.0)

    def test_set_max_registered_node_count_rejects_string(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_registered_node_count("10")

    def test_set_registered_node_id(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_registered_node_id(5)
        assert result is q

    def test_set_registered_node_id_rejects_negative(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="non-negative integer"):
            q.set_registered_node_id(-1)

    def test_set_registered_node_id_rejects_bool(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="non-negative integer"):
            q.set_registered_node_id(True)

    def test_set_limit(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_limit(50)
        assert result is q

    def test_set_limit_rejects_zero(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_limit(0)

    def test_set_max_attempts(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_max_attempts(5)
        assert result is q

    def test_set_max_attempts_rejects_zero(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive integer"):
            q.set_max_attempts(0)

    def test_set_max_backoff(self):
        q = RegisteredNodeAddressBookQuery()
        result = q.set_max_backoff(10.0)
        assert result is q

    def test_set_max_backoff_rejects_zero(self):
        q = RegisteredNodeAddressBookQuery()
        with pytest.raises(ValueError, match="positive number"):
            q.set_max_backoff(0)

    def test_build_initial_path_default(self):
        q = RegisteredNodeAddressBookQuery()
        path = q._build_initial_path()
        assert "/api/v1/network/registered-nodes" in path
        assert "limit=25" in path

    def test_build_initial_path_with_node_id(self):
        q = RegisteredNodeAddressBookQuery()
        q.set_registered_node_id(7)
        path = q._build_initial_path()
        assert "registerednode.id=7" in path

    def test_next_page_path_with_link(self):
        data = {"links": {"next": "/api/v1/network/registered-nodes?limit=25&registerednode.id=gt:10"}}
        assert RegisteredNodeAddressBookQuery._next_page_path(data) is not None

    def test_next_page_path_without_link(self):
        data = {"links": {"next": None}}
        assert RegisteredNodeAddressBookQuery._next_page_path(data) is None

    def test_next_page_path_no_links_key(self):
        data = {}
        assert RegisteredNodeAddressBookQuery._next_page_path(data) is None


# ---------------------------------------------------------------------------
# RegisteredNode._from_dict edge cases
# ---------------------------------------------------------------------------


class TestRegisteredNodeFromDictEdgeCases:
    """Tests for RegisteredNode._from_dict with different key types."""

    def test_from_dict_with_ecdsa_admin_key(self):
        """Verify _from_dict handles ECDSA_SECP256K1 keys."""
        pub = PrivateKey.generate_ecdsa().public_key()
        data = {
            "registered_node_id": 1,
            "admin_key": {"_type": "ECDSA_SECP256K1", "key": pub.to_string_raw()},
        }
        node = RegisteredNode._from_dict(data)
        assert node.admin_key is not None

    def test_from_dict_with_generic_key_hex(self):
        """Verify _from_dict handles a generic key hex without explicit _type."""
        pub = PrivateKey.generate().public_key()
        data = {
            "registered_node_id": 2,
            "admin_key": {"key": pub.to_string()},
        }
        node = RegisteredNode._from_dict(data)
        assert node.admin_key is not None

    def test_from_dict_empty_description_is_none(self):
        """Verify _from_dict treats empty description as None."""
        data = {"registered_node_id": 3, "description": ""}
        node = RegisteredNode._from_dict(data)
        assert node.description is None

    def test_from_dict_with_ip_endpoint(self):
        """Verify _from_dict handles endpoints with ip_address."""
        data = {
            "registered_node_id": 4,
            "service_endpoints": [
                {
                    "ip_address": "127.0.0.1",
                    "port": 443,
                    "requires_tls": True,
                    "type": "MIRROR_NODE",
                }
            ],
        }
        node = RegisteredNode._from_dict(data)
        assert len(node.service_endpoints) == 1
        assert node.service_endpoints[0].ip_address == b"\x7f\x00\x00\x01"


# ---------------------------------------------------------------------------
# RegisteredNodeAddressBookQuery execution with mocking
# ---------------------------------------------------------------------------


class TestRegisteredNodeAddressBookQueryExecution:
    """Tests for query execution, URL building, and retry logic using mocks."""

    def _make_client(self, rest_url="http://testnet.example.com/api/v1"):
        """Create a mock client with a configurable mirror REST URL."""
        client = MagicMock()
        client.network.get_mirror_rest_url.return_value = rest_url
        return client

    def test_build_base_url_strips_api_v1(self):
        """Verify _build_base_url strips /api/v1 suffix."""
        q = RegisteredNodeAddressBookQuery()
        client = self._make_client("http://mirror.example.com/api/v1")
        assert q._build_base_url(client) == "http://mirror.example.com"

    def test_build_base_url_localhost_port_replacement(self):
        """Verify localhost:38081 is replaced with :8084."""
        q = RegisteredNodeAddressBookQuery()
        client = self._make_client("http://localhost:38081/api/v1")
        assert ":8084" in q._build_base_url(client)
        assert ":38081" not in q._build_base_url(client)

    def test_build_base_url_127_port_replacement(self):
        """Verify 127.0.0.1:38081 is replaced with :8084."""
        q = RegisteredNodeAddressBookQuery()
        client = self._make_client("http://127.0.0.1:38081/api/v1")
        assert ":8084" in q._build_base_url(client)

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_execute_single_page(self, mock_get):
        """Verify execute returns nodes from a single-page response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "registered_nodes": [
                {"registered_node_id": 1, "service_endpoints": []},
                {"registered_node_id": 2, "service_endpoints": []},
            ],
            "links": {"next": None},
        }
        mock_get.return_value = mock_resp

        q = RegisteredNodeAddressBookQuery()
        client = self._make_client()
        result = q.execute(client)

        assert isinstance(result, RegisteredNodeAddressBook)
        assert len(result) == 2
        assert result[0].registered_node_id == 1

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_execute_with_pagination(self, mock_get):
        """Verify execute follows pagination links."""
        page1 = MagicMock()
        page1.status_code = 200
        page1.json.return_value = {
            "registered_nodes": [{"registered_node_id": 1, "service_endpoints": []}],
            "links": {"next": "/api/v1/network/registered-nodes?limit=1&registerednode.id=gt:1"},
        }
        page2 = MagicMock()
        page2.status_code = 200
        page2.json.return_value = {
            "registered_nodes": [{"registered_node_id": 2, "service_endpoints": []}],
            "links": {"next": None},
        }
        mock_get.side_effect = [page1, page2]

        q = RegisteredNodeAddressBookQuery().set_limit(1)
        result = q.execute(self._make_client())

        assert len(result) == 2
        assert mock_get.call_count == 2

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_execute_respects_max_count(self, mock_get):
        """Verify execute stops when max_registered_node_count is reached."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "registered_nodes": [
                {"registered_node_id": 1, "service_endpoints": []},
                {"registered_node_id": 2, "service_endpoints": []},
                {"registered_node_id": 3, "service_endpoints": []},
            ],
            "links": {"next": "/api/v1/network/registered-nodes?limit=25&registerednode.id=gt:3"},
        }
        mock_get.return_value = mock_resp

        q = RegisteredNodeAddressBookQuery().set_max_registered_node_count(2)
        result = q.execute(self._make_client())

        assert len(result) == 2

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_fetch_page_non_retryable_error(self, mock_get):
        """Verify non-retryable HTTP errors raise immediately."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "Not Found"
        mock_get.return_value = mock_resp

        q = RegisteredNodeAddressBookQuery().set_max_attempts(3)
        with pytest.raises(RuntimeError, match="HTTP 404"):
            q._fetch_page("http://example.com/api/v1/network/registered-nodes")
        assert mock_get.call_count == 1

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.time.sleep")
    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_fetch_page_retries_on_503(self, mock_get, mock_sleep):
        """Verify retryable HTTP errors are retried."""
        fail_resp = MagicMock()
        fail_resp.status_code = 503
        fail_resp.text = "Service Unavailable"

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"registered_nodes": []}

        mock_get.side_effect = [fail_resp, ok_resp]

        q = RegisteredNodeAddressBookQuery().set_max_attempts(3)
        result = q._fetch_page("http://example.com/test")

        assert result == {"registered_nodes": []}
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1

    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.time.sleep")
    @patch("hiero_sdk_python.address_book.registered_node_address_book_query.requests.get")
    def test_fetch_page_exhausts_retries(self, mock_get, _mock_sleep):
        """Verify exhausting retries raises RuntimeError."""
        import requests as req

        mock_get.side_effect = req.ConnectionError("refused")

        q = RegisteredNodeAddressBookQuery().set_max_attempts(2).set_max_backoff(0.1)
        with pytest.raises(RuntimeError, match="Failed to fetch"):
            q._fetch_page("http://example.com/test")
        assert mock_get.call_count == 2
