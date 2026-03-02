import time
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.node import _Node

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_address_book():
    """Create a mock address book with certificate hash."""
    cert_hash = b"test_cert_hash_12345"
    endpoint = Endpoint(
        address=b"node.example.com", port=50211, domain_name="node.example.com"
    )
    address_book = NodeAddress(
        account_id=AccountId(0, 0, 3), cert_hash=cert_hash, addresses=[endpoint]
    )
    return address_book


@pytest.fixture
def node(mock_address_book):
    """Create a node with deterministic value for unit tests."""
    node = _Node(AccountId(0, 0, 3), "127.0.0.1:50211", mock_address_book)
    return node


# Test is_healthy
def test_is_healthy_when_readmit_time_in_past(node):
    """Test that a node is healthy if readmit time is in the past."""
    node._readmit_time = time.monotonic() - 10
    assert node.is_healthy() is True


def test_is_healthy_when_readmit_time_in_future(node):
    """Test that a node is unhealthy if readmit time is in the future."""
    node._readmit_time = time.monotonic() + 10
    assert node.is_healthy() is False


# Test increase_backoff
def test_increase_backoff_doubles_value(node):
    """Test that _increase_backoff doubles the current backoff."""
    node._current_backoff = 10

    node._increase_backoff()
    assert node._current_backoff == 20
    assert node._readmit_time > time.monotonic()


def test_increase_backoff_caps_at_max(node):
    """Test that _increase_backoff does not exceed the maximum backoff."""
    node._current_backoff = node._max_backoff

    node._increase_backoff()
    assert node._current_backoff == node._max_backoff


def test_increase_backoff_updates_readmit_time(node):
    """Test that _increase_backoff updates the readmit time correctly."""
    node._current_backoff = 10

    before = time.monotonic()
    node._increase_backoff()
    assert node._readmit_time > before + 10


# Test decrease_backoff
def test_decrease_backoff_halves_value(node):
    """Test that _decrease_backoff halves the current backoff."""
    node._current_backoff = 20

    node._decrease_backoff()
    assert node._current_backoff == 10


def test_decrease_backoff_floors_at_min(node):
    """Test that _decrease_backoff does not go below the minimum backoff."""
    node._current_backoff = node._min_backoff

    node._decrease_backoff()
    assert node._current_backoff == node._min_backoff

