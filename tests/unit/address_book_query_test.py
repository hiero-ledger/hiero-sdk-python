"""
Test cases for the AddressBookQuery class.
"""

from __future__ import annotations

from unittest.mock import patch

import grpc
import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.address_book_query import AddressBookQuery
from hiero_sdk_python.address_book.endpoint import Endpoint
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.address_book.node_address_book import NodeAddressBook
from hiero_sdk_python.exceptions import MaxAttemptsError
from tests.unit.mock_server import RealRpcError


# Helper
def _assert_node_address(node1: NodeAddress, node2: NodeAddress):
    """ "Assert that two NodeAddress instances have same values."""
    assert node1._account_id == node2._account_id
    assert node1._description == node2._description
    assert node1._public_key == node2._public_key
    assert node1._node_id == node2._node_id
    assert node1._cert_hash == node2._cert_hash

    assert len(node1._addresses) == len(node2._addresses)


# __init__()


def test_constructor_without_params():
    """Test AddressBookQuery constructor without parameters."""
    query = AddressBookQuery()
    assert query is not None
    assert query.file_id is None
    assert query.limit is None
    assert query.max_attempts == 10
    assert query.max_backoff == 8


def test_constuctor_with_params(file_id):
    """Test AddressBookQuery consturctor with parameters."""
    query = AddressBookQuery(file_id=file_id, limit=1)
    assert query is not None
    assert query.file_id is file_id
    assert query.limit == 1
    assert query.max_attempts == 10
    assert query.max_backoff == 8


@pytest.mark.parametrize("file_id", ("0.0.1", 0, 0.2, True, {}, []))
def test_constructor_with_invalid_file_id(file_id):
    """Test AddressBookQuery consturctor with invalid file_id."""
    with pytest.raises(TypeError, match="file_id must be of type FileId"):
        AddressBookQuery(file_id=file_id)


@pytest.mark.parametrize("limit", ("1", 0.2, True, {}, []))
def test_constructor_with_invalid_limit(limit):
    """Test AddressBookQuery consturctor with invalid limit."""
    with pytest.raises(TypeError, match="limit must be of type int"):
        AddressBookQuery(limit=limit)


def test_constructor_with_negative_limit():
    """Test AddressBookQuery consturctor with negative limit."""
    with pytest.raises(ValueError, match="limit must be greater than -1"):
        AddressBookQuery(limit=-1)


# set_file_id()


def test_set_file_id(file_id):
    """Test setting file id using setter."""
    query = AddressBookQuery()
    retrun_obj = query.set_file_id(file_id)

    assert query.file_id == file_id
    assert retrun_obj is not None
    assert retrun_obj is query


@pytest.mark.parametrize("file_id", ("0.0.1", 0, 0.2, True, {}, []))
def test_set_invalid_file_id(file_id):
    """Test setting invalid file id raise error."""
    with pytest.raises(TypeError, match="file_id must be of type FileId"):
        AddressBookQuery().set_file_id(file_id)


# set_limit()


def test_set_limit():
    """Test setting limit using the setter function."""
    limit = 10

    query = AddressBookQuery()
    retrun_obj = query.set_limit(limit)

    assert query.limit == limit
    assert retrun_obj is not None
    assert retrun_obj is query


@pytest.mark.parametrize("limit", ("1", 0.2, True, {}, []))
def test_set_invalid_limit(limit):
    """Test setting invalid limit raise error."""
    with pytest.raises(TypeError, match="limit must be of type int"):
        AddressBookQuery().set_limit(limit)


def test_set_negative_limit():
    """Test setting negative limit raise error."""
    with pytest.raises(ValueError, match="limit must be greater than -1"):
        AddressBookQuery().set_limit(-1)


# set_max_attempts()


def test_set_max_attempts():
    """Test setting max_attempts using setter."""
    attempts = 10

    query = AddressBookQuery()
    retrun_obj = query.set_max_attempts(attempts)

    assert query.max_attempts == attempts
    assert retrun_obj is not None
    assert retrun_obj is query


@pytest.mark.parametrize("max_attempts", ("1", 0.2, True, {}, []))
def test_set_invalid_max_attempts(max_attempts):
    """Test setting invalid max_attempts raise error."""
    with pytest.raises(TypeError, match="max_attempts must be of type int"):
        AddressBookQuery().set_max_attempts(max_attempts)


@pytest.mark.parametrize("max_attempts", (0, -1))
def test_set_max_attempt_less_than_1(max_attempts):
    """Test setting max_attempt less than 1 raise error."""
    with pytest.raises(ValueError, match="max_attempt must be greater than or equal to 1"):
        AddressBookQuery().set_max_attempts(max_attempts)


# set_max_backoff()


@pytest.mark.parametrize("max_backoff", (1, 0.9))
def test_set_max_backoff(max_backoff):
    """Test setting max_backoff using setter."""
    query = AddressBookQuery()
    retrun_obj = query.set_max_backoff(max_backoff)
    assert query.max_backoff == max_backoff
    assert retrun_obj is not None
    assert retrun_obj is query


@pytest.mark.parametrize("max_backoff", ("1", True, {}, []))
def test_set_invalid_max_backoff(max_backoff):
    """Test setting invalid max_backoff raise error."""
    with pytest.raises(TypeError, match="max_backoff must be of type int or float"):
        AddressBookQuery().set_max_backoff(max_backoff)


@pytest.mark.parametrize("max_backoff", (0.4, 0, -1))
def test_set_max_backoff_less_than_minimum(max_backoff):
    """Test setting max_backoff less than 0.5s raise error."""
    with pytest.raises(ValueError, match="max_backoff must be at least 0.5s"):
        AddressBookQuery().set_max_backoff(max_backoff)


# _make_request()


def test_make_request(file_id):
    """Test build protobuf request for addressBook query."""
    query = AddressBookQuery().set_file_id(file_id).set_limit(1)
    request = query._make_request()

    assert request is not None
    assert request.HasField("file_id")
    assert request.file_id == query.file_id._to_proto()
    assert request.limit == query.limit


def test_make_request_missing_file_id():
    """Test build protobuf request for addressBook query missing file_id."""
    query = AddressBookQuery().set_limit(1)
    request = query._make_request()

    assert request is not None
    assert not request.HasField("file_id")
    assert request.limit == query.limit


def test_make_request_no_limit_set(file_id):
    """Test build protobuf request for addressBook query with no limit set."""
    query = AddressBookQuery().set_file_id(file_id)
    request = query._make_request()

    assert request is not None
    assert request.HasField("file_id")
    assert request.file_id == query.file_id._to_proto()
    assert request.limit == 0


# _should_retry()


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
    ],
)
def test_should_retry(error):
    """Test should_retry returns true for retryable error."""
    result = AddressBookQuery()._should_retry(error)
    assert result is not None
    assert result is True


def test_should_retry_for_internal_error_with_rst_stream():
    """Test should_retry returns true for internal error containing rst stream."""
    error = RealRpcError(grpc.StatusCode.INTERNAL, "received rst stream")

    result = AddressBookQuery()._should_retry(error)
    assert result is not None
    assert result is True


# execute()


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.ALREADY_EXISTS, "already exists"),
        RealRpcError(grpc.StatusCode.ABORTED, "aborted"),
        RealRpcError(grpc.StatusCode.UNAUTHENTICATED, "unauthenticated"),
        RuntimeError("non-grpc error"),
    ],
)
def test_should_retry_with_non_retryable_error(error):
    """Test should_retry returns false for non-retryable error."""
    result = AddressBookQuery()._should_retry(error)
    assert result is not None
    assert result is False


def test_execute_quey(file_id, mock_client):
    """Test successful address book query execution."""
    node1 = NodeAddress(
        public_key="0" * 32,
        account_id=AccountId.from_string("0.0.2"),
        node_id=1,
        cert_hash=("0" * 32).encode("utf-8"),
        addresses=[Endpoint(domain_name="test1.net.in", port=50211)],
        description="Test Node1",
    )
    node2 = NodeAddress(
        public_key="0" * 32,
        account_id=AccountId.from_string("0.0.4"),
        node_id=2,
        cert_hash=("0" * 32).encode("utf-8"),
        addresses=[],
        description="Test Node2",
    )

    query = AddressBookQuery().set_file_id(file_id).set_limit(1)

    with patch("hiero_sdk_python.address_book.address_book_query.NetworkServiceStub") as mock_stub:
        mock_stub.return_value.getNodes.return_value = [node1._to_proto(), node2._to_proto()]
        result = query.execute(mock_client)

        assert result is not None
        assert isinstance(result, NodeAddressBook)
        assert len(result.node_addresses) == 2

        _assert_node_address(result.node_addresses[0], node1)
        _assert_node_address(result.node_addresses[1], node2)


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.ALREADY_EXISTS, "already exists"),
        RealRpcError(grpc.StatusCode.ABORTED, "aborted"),
        RealRpcError(grpc.StatusCode.UNAUTHENTICATED, "unauthenticated"),
        RuntimeError("non-grpc error"),
    ],
)
def test_execute_non_retryable_error(mock_client, error):
    """Test execute raises immediately for a non-retryable error."""
    query = AddressBookQuery()

    with patch("hiero_sdk_python.address_book.address_book_query.NetworkServiceStub") as mock_stub:
        mock_stub.return_value.getNodes.side_effect = error
        with pytest.raises(type(error)):
            query.execute(mock_client)

        mock_stub.return_value.getNodes.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
        RealRpcError(grpc.StatusCode.INTERNAL, "received rst stream"),
    ],
)
def test_execute_retryable_error(mock_client, error):
    """Test execute for a retryable error."""
    query = AddressBookQuery()
    node = NodeAddress(
        public_key="0" * 32,
        account_id=AccountId.from_string("0.0.4"),
        node_id=1,
        cert_hash=("0" * 32).encode("utf-8"),
        addresses=[],
        description="Test Node",
    )

    with patch("hiero_sdk_python.address_book.address_book_query.NetworkServiceStub") as mock_stub:
        mock_stub.return_value.getNodes.side_effect = [error, [node._to_proto()]]

        result = query.execute(mock_client)

    assert mock_stub.return_value.getNodes.call_count == 2
    assert result is not None
    assert isinstance(result, NodeAddressBook)
    assert len(result.node_addresses) == 1

    _assert_node_address(result.node_addresses[0], node)


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
        RealRpcError(grpc.StatusCode.INTERNAL, "received rst stream"),
    ],
)
def test_execute_retry_fails_when_reach_max_attempt(mock_client, error):
    """Test execute for a retryable error fails when reach max_attempts."""
    query = AddressBookQuery()
    node = NodeAddress(
        public_key="0" * 32,
        account_id=AccountId.from_string("0.0.4"),
        node_id=1,
        cert_hash=("0" * 32).encode("utf-8"),
        addresses=[],
        description="Test Node",
    )

    with patch("hiero_sdk_python.address_book.address_book_query.NetworkServiceStub") as mock_stub:
        mock_stub.return_value.getNodes.side_effect = [
            error,
            error,
            [node._to_proto()],  # possible response if max_attempt not reach
        ]

        with pytest.raises(MaxAttemptsError, match="Exceeded maximum attempts"):
            query.set_max_attempts(2).execute(mock_client)

    assert mock_stub.return_value.getNodes.call_count == 2


@pytest.mark.parametrize("client", (None, "client", True, 1, 0.1, {}, []))
def test_execute_with_none_client(file_id, client):
    """Test execute with invalid client parameter."""
    with pytest.raises(TypeError, match="client must be an instance of Client"):
        AddressBookQuery().set_file_id(file_id).set_limit(1).execute(client)


@pytest.mark.parametrize("timeout", ("1", True, {}, []))
def test_execute_with_invalid_timeout(mock_client, file_id, timeout):
    """Test execute with invalid timeout parameter."""
    with pytest.raises(TypeError, match="timeout must be a int or float"):
        AddressBookQuery().set_file_id(file_id).set_limit(1).execute(mock_client, timeout)


# _delay_for_attempt()


@pytest.mark.parametrize(
    ("attempt", "expected_delay"),
    [
        (1, 1),  # 0.5*2
        (2, 2),  # 0.5*4
        (3, 4),  # 0.5*8
        (4, 8),  # 0.5*16
    ],
)
def test_delay_for_attempt(attempt, expected_delay):
    """Test retry delay is properly calculated."""
    query = AddressBookQuery()

    with patch("hiero_sdk_python.address_book.address_book_query.time.sleep") as sleep:
        query._delay_for_attempt(attempt)
        sleep.assert_called_once_with(expected_delay)


def test_delay_for_attempt_cap_to_max_backoff():
    """Test retry delay is capped by max_backoff."""
    query = AddressBookQuery()

    attempt = 5  # calculated backoff = 0.5 * 2^5 = 0.5 * 32 = 16
    expected = query.max_backoff  # 8 default
    with patch("hiero_sdk_python.address_book.address_book_query.time.sleep") as sleep:
        query._delay_for_attempt(attempt)
        sleep.assert_called_once_with(expected)
