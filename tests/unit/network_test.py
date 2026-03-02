import time
import pytest
from unittest.mock import Mock, patch

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.node import _Node

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def mock_network_nodes(monkeypatch):
    """Helper to mock fetch_node_from_mirror_nodes apply to all instead of making mirror rest call"""
    fake_nodes = [
        _Node(AccountId(0, 0, 3), "127.0.0.1:50211", NodeAddress()),
        _Node(AccountId(0, 0, 4), "127.0.0.1:50212", NodeAddress()),
        _Node(AccountId(0, 0, 5), "127.0.0.1:50212", NodeAddress()),
    ]

    def fake_fetch_nodes(self):
        return fake_nodes

    monkeypatch.setattr(Network, "_fetch_nodes_from_mirror_node", fake_fetch_nodes)

    return fake_nodes


# Tests  _readmit_nodes
def test_readmit_nodes_returns_early(monkeypatch):
    """
    Test _readmit_nodes returns immediately if _earliest_readmit_time has not passed yet.
    """
    network = Network("testnet")
    now = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: now)

    network._earliest_readmit_time = now + 10
    network._healthy_nodes = []
    network._readmit_nodes()

    assert network._healthy_nodes == []


def test_readmit_nodes_adds_expired_node(monkeypatch):
    """
    Test readmit_nodes adds a node whose backoff period has expired to the healthy nodes list.
    """
    network = Network("testnet")

    now = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: now)

    # Node ready to be readmitted
    node = Mock(spec=_Node)
    node._readmit_time = now - 1

    network.nodes = [node]
    network._healthy_nodes = []

    network._earliest_readmit_time = 0

    network._readmit_nodes()

    assert node in network._healthy_nodes
    assert network._earliest_readmit_time >= now


def test_readmit_nodes_skips_unexpired_node(monkeypatch):
    """
    Test _readmit_nodes does not add nodes whose backoff period has not yet expired.
    """
    network = Network("testnet")

    now = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: now)

    # Node not ready to be readmitted
    node = Mock(spec=_Node)
    node._readmit_time = now + 50

    network.nodes = [node]
    network._healthy_nodes = []
    network._earliest_readmit_time = 0

    network._readmit_nodes()

    assert node not in network._healthy_nodes

    expected_delay = max(network._node_min_readmit_period, node._readmit_time - now)
    expected_delay = min(expected_delay, network._node_max_readmit_period)

    assert network._earliest_readmit_time == now + expected_delay


def test_readmit_nodes_updates_earliest_readmit_time(monkeypatch):
    """
    Test _readmit_nodes correctly calculates _earliest_readmit_time  based
    on multiple nodes with different _readmit_time values and the configured
    min/max readmit periods.
    """
    network = Network("testnet")

    now = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: now)

    node_ready = Mock(spec=_Node)
    node_ready._readmit_time = now - 5  # ready to be readmitted

    node_not_ready = Mock(spec=_Node)
    node_not_ready._readmit_time = now + 20  # not ready yet

    network.nodes = [node_ready, node_not_ready]
    network._healthy_nodes = []
    network._earliest_readmit_time = 0
    network._node_min_readmit_period = 8
    network._node_max_readmit_period = 60

    network._readmit_nodes()

    # Only ready node is added
    assert node_ready in network._healthy_nodes
    assert node_not_ready not in network._healthy_nodes

    # _earliest_readmit_time should reflect the next node's readmit time with min/max applied
    expected_delay = min(
        network._node_max_readmit_period,
        max(network._node_min_readmit_period, node_not_ready._readmit_time - now),
    )
    assert network._earliest_readmit_time == now + expected_delay


def test_readmit_nodes_does_not_duplicate_healthy_nodes(monkeypatch):
    """Test that the _readmit_nodes method does not add duplicate nodes."""
    network = Network("testnet")

    now = 1000.0
    monkeypatch.setattr(time, "monotonic", lambda: now)

    node = Mock(spec=_Node)
    node._readmit_time = now - 10

    network.nodes = [node]
    network._healthy_nodes = [node]
    network._earliest_readmit_time = 0

    network._readmit_nodes()

    assert network._healthy_nodes.count(node) == 1


# Tests _increase_backoff
def test_increase_backoff_removes_node_from_healthy():
    """
    Test _increase_backoff calls _increase_backoff on the node and removes it from the healthy nodes list.
    """
    network = Network("testnet")

    # Mock node
    node = Mock(spec=_Node)
    network.nodes = [node]
    network._healthy_nodes = [node]

    # Call the method
    network._increase_backoff(node)

    # Assert node's _increase_backoff was called
    node._increase_backoff.assert_called_once()

    # Node should be removed from healthy nodes
    assert node not in network._healthy_nodes


def test_increase_backoff_type_error_for_invalid_input():
    """
    Test _increase_backoff raises TypeError if the argument is not of type _Node.
    """
    network = Network("testnet")

    invalid_values = [None, True, object, 123, "node", [], {}]

    for invalid in invalid_values:
        with pytest.raises(TypeError, match="node must be of type _Node"):
            network._increase_backoff(invalid)


def test_increase_backoff_does_not_affect_other_nodes():
    """
    Test _increase_backoff only affects the target node and does not remove other nodes from healthy_nodes.
    """
    network = Network("testnet")

    node1 = Mock(spec=_Node)
    node2 = Mock(spec=_Node)
    network.nodes = [node1, node2]
    network._healthy_nodes = [node1, node2]

    network._increase_backoff(node1)

    # node1 removed
    assert node1 not in network._healthy_nodes
    # node2 still in healthy_nodes
    assert node2 in network._healthy_nodes
    # node1's _increase_backoff called
    node1._increase_backoff.assert_called_once()
    # node2's _increase_backoff not called
    node2._increase_backoff.assert_not_called()


# Tests _decrease_backoff
def test_decrease_backoff_calls_node_method():
    """
    Test _decrease_backoff calls _decrease_backoff on the target node.
    """
    network = Network("testnet")

    node = Mock(spec=_Node)
    network.nodes = [node]
    network._healthy_nodes = [node]

    # Call the method
    network._decrease_backoff(node)

    # Assert node's _decrease_backoff was called
    node._decrease_backoff.assert_called_once()

    # Node should remain in healthy_nodes (unlike _increase_backoff)
    assert node in network._healthy_nodes


def test_decrease_backoff_type_error_for_invalid_input():
    """
    Test _decrease_backoff raises TypeError if the argument is not of type _Node.
    """
    network = Network("testnet")

    invalid_values = [None, 123, True, object, "node", [], {}]

    for invalid in invalid_values:
        with pytest.raises(TypeError, match="node must be of type _Node"):
            network._decrease_backoff(invalid)


def test_decrease_backoff_does_not_affect_other_nodes():
    """
    Test _decrease_backoff only affects the target node and does not call _decrease_backoff on other nodes.
    """
    network = Network("testnet")

    node1 = Mock(spec=_Node)
    node2 = Mock(spec=_Node)
    network.nodes = [node1, node2]
    network._healthy_nodes = [node1, node2]

    network._decrease_backoff(node1)

    # node1's _decrease_backoff called
    node1._decrease_backoff.assert_called_once()
    # node2's _decrease_backoff not called
    node2._decrease_backoff.assert_not_called()

    # Both nodes remain in healthy_nodes
    assert node1 in network._healthy_nodes
    assert node2 in network._healthy_nodes


# Test set_network_nodes
def test_set_network_nodes_with_explicit_nodes():
    """
    Test _set_network_nodes uses explicitly provided nodes and marks healthy ones.
    """
    network = Network("testnet")

    # mock nodes
    node1 = Mock(spec=_Node)
    node2 = Mock(spec=_Node)

    node1.is_healthy.return_value = True
    node2.is_healthy.return_value = False

    network._set_network_nodes([node1, node2])

    assert network.nodes == [node1, node2]
    assert network._healthy_nodes == [node1]


def test_set_network_nodes_resets_healthy_nodes():
    """
    Test _set_network_nodes clears previously healthy nodes.
    """
    network = Network("testnet")

    old_node = Mock(spec=_Node)
    network._healthy_nodes = [old_node]

    new_node = Mock(spec=_Node)
    new_node.is_healthy.return_value = True

    network._set_network_nodes([new_node])

    assert old_node not in network._healthy_nodes
    assert network._healthy_nodes == [new_node]


# Test select_node
def test_select_node_round_robin():
    """Test that _select_node cycles through healthy nodes using round-robin selection."""
    network = Network("testnet")

    node1 = Mock(spec=_Node)
    node2 = Mock(spec=_Node)

    network._healthy_nodes = [node1, node2]
    network._node_index = 0

    assert network._select_node() is node2
    assert network._select_node() is node1


def test_select_node_raises_when_no_healthy_nodes():
    """
    Test _select_node raises ValueError if no healthy nodes exist.
    """
    network = Network("testnet")
    network._healthy_nodes = []

    with pytest.raises(ValueError, match="No healthy node available"):
        network._select_node()


# Test get_node
def test_get_node_by_account_id():
    """
    Test _get_node returns node matching account ID.
    """
    network = Network("testnet")

    node = _Node(AccountId(0, 0, 3), "127.0.0.1:8080", None)

    network._healthy_nodes = [node]

    with patch(
        "hiero_sdk_python.client.network.Network._readmit_nodes"
    ) as mock_readmit:
        result = network._get_node(AccountId(0, 0, 3))

    assert mock_readmit.call_count == 1
    assert result._account_id == node._account_id


def test_get_node_returns_none_when_not_found():
    """
    Test _get_node returns None if no matching node exists.
    """
    network = Network("testnet")

    node = Mock(spec=_Node)
    node._account_id = AccountId(0, 0, 3)
    network._healthy_nodes = [node]

    assert network._get_node("0.0.999") is None


# Tests parse_mirror_address
@pytest.mark.parametrize(
    "mirror_addr,expected_host,expected_port",
    [
        ("localhost:5551", "localhost", 5551),
        ("127.0.0.1:8080", "127.0.0.1", 8080),
        ("mirror.hedera.com:443", "mirror.hedera.com", 443),
        ("justhost", "justhost", 443),  # no port defaults to 443
        ("badport:abc", "badport", 443),  # invalid port defaults to 443
    ],
)
def test_parse_mirror_address(mirror_addr, expected_host, expected_port):
    """Test that _parse_mirror_address correctly splits mirror_address into host and port."""
    network = Network("testnet", mirror_address=mirror_addr)
    host, port = network._parse_mirror_address()
    assert host == expected_host
    assert port == expected_port


# Tests _determine_scheme_and_port
@pytest.mark.parametrize(
    "host,port,expected_scheme,expected_port",
    [
        ("localhost", 443, "http", 8080),
        ("127.0.0.1", 80, "http", 80),
        ("127.0.0.1", 5000, "http", 5000),
        ("hedera.com", 5600, "https", 443),
        ("hedera.com", 443, "https", 443),
        ("hedera.com", 8443, "https", 8443),
    ],
)
def test_determine_scheme_and_port(host, port, expected_scheme, expected_port):
    """Test that _determine_scheme_and_port correctly computes the scheme (http/https)."""
    network = Network("testnet")
    scheme, out_port = network._determine_scheme_and_port(host, port)
    assert out_port == expected_port
    assert scheme == expected_scheme


# Tests for _build_rest_url
@pytest.mark.parametrize(
    "scheme,host,port,expected_url",
    [
        ("https", "hedera.com", 443, "https://hedera.com/api/v1"),
        ("https", "hedera.com", 8443, "https://hedera.com:8443/api/v1"),
        ("http", "localhost", 80, "http://localhost/api/v1"),
        ("http", "localhost", 8080, "http://localhost:8080/api/v1"),
    ],
)
def test_build_rest_url(scheme, host, port, expected_url):
    """Test that _build_rest_url constructs the correct REST API URL."""
    network = Network("testnet")
    url = network._build_rest_url(scheme, host, port)
    assert url == expected_url


def test_get_mirror_rest_url_fallback():
    """Test get_mirror_rest_url fallback behavior when network is not in MIRROR_NODE_URLS."""
    # Custom network with no entry in MIRROR_NODE_URLS
    network = Network("customnet", mirror_address="localhost:1234")

    scheme, port = network._determine_scheme_and_port(*network._parse_mirror_address())
    expected_url = network._build_rest_url(scheme, "localhost", port)

    assert network.get_mirror_rest_url() == expected_url


@pytest.mark.unit
def test_resolve_nodes_fallback_to_default(monkeypatch):
    """Test that _resolve_nodes falls back to DEFAULT_NODES if no nodes are provided and mirror fetch returns empty."""
    network_name = "testnet"
    network = Network(network_name)

    # Patch _fetch_nodes_from_mirror_node to return empty list
    monkeypatch.setattr(network, "_fetch_nodes_from_mirror_node", lambda: [])

    # Call _resolve_nodes with nodes=None should fallback to DEFAULT_NODES
    resolved_nodes = network._resolve_nodes(None)

    # DEFAULT_NODES for testnet has 4 entries (0..3)
    expected_count = len(network.DEFAULT_NODES[network_name])
    assert isinstance(resolved_nodes, list)
    assert all(isinstance(n, _Node) for n in resolved_nodes)
    assert len(resolved_nodes) == expected_count
    assert resolved_nodes[0]._account_id == network.DEFAULT_NODES[network_name][0][1]
