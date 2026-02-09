"""
Unit tests for Client methods (eg. from_env, for_testnet, for_mainnet, for_previewnet).
"""

from decimal import Decimal
import os
import pytest
from unittest.mock import MagicMock, patch

from hiero_sdk_python.client import client as client_module

from hiero_sdk_python import Client, AccountId, PrivateKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.node import _Node
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "factory_method, expected_network",
    [
        (Client.for_testnet, "testnet"),
        (Client.for_mainnet, "mainnet"),
        (Client.for_previewnet, "previewnet"),
    ],
)
def test_factory_basic_setup(factory_method, expected_network):
    """Test that factory methods return a Client with correct network and no operator."""
    client = factory_method()

    assert isinstance(client, Client)
    assert client.network.network == expected_network
    assert client.operator_account_id is None
    assert client.operator_private_key is None

    client.close()


def test_for_testnet_then_set_operator():
    """Test that we can manually set the operator on a factory client."""
    client = Client.for_testnet()

    # Generate dummy credentials
    operator_id = AccountId(0, 0, 12345)
    operator_key = PrivateKey.generate_ed25519()

    client.set_operator(operator_id, operator_key)

    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()
    assert client.operator is not None

    client.close()


def test_for_mainnet_then_set_operator():
    """Test that we can manually set the operator on a mainnet client."""
    client = Client.for_mainnet()

    operator_id = AccountId(0, 0, 67890)
    operator_key = PrivateKey.generate_ecdsa()

    client.set_operator(operator_id, operator_key)

    assert client.operator_account_id == operator_id
    assert client.operator_private_key.to_string() == operator_key.to_string()

    client.close()


def test_from_env_missing_operator_id_raises_error():
    """Test that from_env raises ValueError when OPERATOR_ID is missing."""
    dummy_key = PrivateKey.generate_ed25519().to_string_der()

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, {"OPERATOR_KEY": dummy_key}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Client.from_env()
            assert "OPERATOR_ID" in str(exc_info.value)


def test_from_env_missing_operator_key_raises_error():
    """Test that from_env raises ValueError when OPERATOR_KEY is missing."""
    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, {"OPERATOR_ID": "0.0.1234"}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Client.from_env()
            assert "OPERATOR_KEY" in str(exc_info.value)


def test_from_env_with_valid_credentials():
    """Test that from_env creates client with valid environment variables."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key_str,
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert isinstance(client, Client)
            assert client.operator_account_id == AccountId.from_string("0.0.1234")
            client.close()


def test_from_env_with_explicit_network_parameter():
    """Test that from_env uses explicit network parameter over env var."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.5678",
        "OPERATOR_KEY": test_key_str,
        "NETWORK": "testnet",
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env(network="mainnet")
            assert client.network.network == "mainnet"
            client.close()


def test_from_env_defaults_to_testnet():
    """Test that from_env defaults to testnet when NETWORK not set."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1111",
        "OPERATOR_KEY": test_key_str,
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert client.network.network == "testnet"
            client.close()


def test_from_env_uses_network_env_var():
    """Test that from_env uses NETWORK env var when no argument is provided."""
    test_key = PrivateKey.generate_ed25519()
    test_key_str = test_key.to_string_der()

    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key_str,
        "NETWORK": "previewnet",
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            client = Client.from_env()
            assert client.network.network == "previewnet"
            client.close()


def test_from_env_with_invalid_network_name():
    """Test that from_env raises error for invalid network name."""
    test_key = PrivateKey.generate_ed25519()
    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": test_key.to_string_der(),
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid network name"):
                Client.from_env(network="mars_network")


def test_from_env_with_malformed_operator_id():
    """Test that from_env raises error for malformed OPERATOR_ID."""
    test_key = PrivateKey.generate_ed25519()
    env_vars = {
        "OPERATOR_ID": "not-an-account-id",
        "OPERATOR_KEY": test_key.to_string_der(),
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError, match="Invalid account ID"):
                Client.from_env()


def test_from_env_with_malformed_operator_key():
    """Test that from_env raises error for malformed OPERATOR_KEY."""
    env_vars = {
        "OPERATOR_ID": "0.0.1234",
        "OPERATOR_KEY": "not-a-valid-key",
    }

    with patch.object(client_module, "load_dotenv"):
        with patch.dict(os.environ, env_vars, clear=True):
            with pytest.raises(ValueError):
                Client.from_env()


@pytest.mark.parametrize(
    "valid_amount,expected",
    [
        (1, Hbar(1)),
        (0.1, Hbar(0.1)),
        (Decimal("0.1"), Hbar(Decimal("0.1"))),
        (Hbar(1), Hbar(1)),
        (Hbar(0), Hbar(0)),
    ],
)
def test_set_default_max_query_payment_valid_param(valid_amount, expected):
    """Test that set_default_max_query_payment correctly converts various input types to Hbar."""
    client = Client.for_testnet()
    # by default is 1 hbar before setting it
    assert client.default_max_query_payment == Hbar(1)
    client.set_default_max_query_payment(valid_amount)
    assert client.default_max_query_payment == expected


@pytest.mark.parametrize(
    "negative_amount", [-1, -0.1, Decimal("-0.1"), Decimal("-1"), Hbar(-1)]
)
def test_set_default_max_query_payment_negative_value(negative_amount):
    """Test set_default_max_query_payment for negative amount values."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="max_query_payment must be non-negative"):
        client.set_default_max_query_payment(negative_amount)


@pytest.mark.parametrize("invalid_amount", ["1", "abc", True, False, None, object()])
def test_set_default_max_query_payment_invalid_param(invalid_amount):
    """Test that set_default_max_query_payment raise error for invalid param."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=(
            "max_query_payment must be int, float, Decimal, or Hbar, "
            f"got {type(invalid_amount).__name__}"
        ),
    ):
        client.set_default_max_query_payment(invalid_amount)


@pytest.mark.parametrize("invalid_amount", [float("inf"), float("nan")])
def test_set_default_max_query_payment_non_finite_value(invalid_amount):
    """Test that set_default_max_query_payment raise error for non finite value."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="Hbar amount must be finite"):
        client.set_default_max_query_payment(invalid_amount)


# Set max_attempts
def test_set_max_attempts_with_valid_param():
    """Test that set_max_attempts updates default max_attempts value for client."""
    client = Client.for_testnet()
    assert client.max_attempts == 10  # default max_attempt 10

    returned = client.set_max_attempts(20)
    assert client.max_attempts == 20
    assert returned is client

    client.close()


@pytest.mark.parametrize("invalid_max_attempts", ["1", 0.2, True, False, object(), {}])
def test_set_max_attempts_with_invalid_type(invalid_max_attempts):
    """Test that set_max_attempts raises TypeError for non-int values."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=f"max_attempts must be of type int, got {type(invalid_max_attempts).__name__}",
    ):
        client.set_max_attempts(invalid_max_attempts)


@pytest.mark.parametrize("invalid_max_attempts", [0, -10])
def test_set_max_attempts_with_invalid_value(invalid_max_attempts):
    """Test that set_max_attempts raises ValueError for non-positive values."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="max_attempts must be greater than 0"):
        client.set_max_attempts(invalid_max_attempts)


# Set grpc_deadline
def test_set_grpc_deadline_with_valid_param():
    """Test that set_grpc_deadline updates default value of _grpc_deadline."""
    client = Client.for_testnet()
    assert client._grpc_deadline == 10  # default grpc_deadline 10 sec

    returned = client.set_grpc_deadline(20)
    assert client._grpc_deadline == 20
    assert returned is client

    client.close()


@pytest.mark.parametrize("invalid_grpc_deadline", ["1", True, False, object(), {}])
def test_set_grpc_deadline_with_invalid_type(invalid_grpc_deadline):
    """Test that set_grpc_deadline raises TypeError for invalid types."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=f"grpc_deadline must be of type Union\\[int, float\\], got {type(invalid_grpc_deadline).__name__}",
    ):
        client.set_grpc_deadline(invalid_grpc_deadline)


@pytest.mark.parametrize(
    "invalid_grpc_deadline", [0, -10, 0.0, -2.3, float("inf"), float("nan")]
)
def test_set_grpc_deadline_with_invalid_value(invalid_grpc_deadline):
    """Test that set_grpc_deadline raises ValueError for non-positive values."""
    client = Client.for_testnet()

    with pytest.raises(
        ValueError, match="grpc_deadline must be a finite value greater than 0"
    ):
        client.set_grpc_deadline(invalid_grpc_deadline)


# Set request_timeout
def test_set_request_timeout_with_valid_param():
    """Test that set_request_timeout updates default value of _request_timeout."""
    client = Client.for_testnet()
    assert client._request_timeout == 120  # default request_timeout 120 sec

    returned = client.set_request_timeout(200)
    assert client._request_timeout == 200
    assert returned is client

    client.close()


@pytest.mark.parametrize("invalid_request_timeout", ["1", True, False, object(), {}])
def test_set_request_timeout_with_invalid_type(invalid_request_timeout):
    """Test that set_request_timeout raises TypeError for invalid types."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=f"request_timeout must be of type Union\\[int, float\\], got {type(invalid_request_timeout).__name__}",
    ):
        client.set_request_timeout(invalid_request_timeout)


@pytest.mark.parametrize(
    "invalid_request_timeout", [0, -10, 0.0, -2.3, float("inf"), float("nan")]
)
def test_set_request_timeout_with_invalid_value(invalid_request_timeout):
    """Test that set_request_timeout raises ValueError for non-positive values."""
    client = Client.for_testnet()

    with pytest.raises(
        ValueError, match="request_timeout must be a finite value greater than 0"
    ):
        client.set_request_timeout(invalid_request_timeout)


# Set min_backoff
def test_set_min_backoff_with_valid_param():
    """Test that set_min_backoff updates default value of _min_backoff."""
    client = Client.for_testnet()
    assert client._min_backoff == 0.25  # default min_backoff = 0.25 sec

    returned = client.set_min_backoff(2)
    assert client._min_backoff == 2
    assert returned is client

    client.close()


@pytest.mark.parametrize("invalid_min_backoff", ["1", True, False, object(), {}])
def test_set_min_backoff_with_invalid_type(invalid_min_backoff):
    """Test that set_min_backoff raises TypeError for invalid types."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=f"min_backoff must be of type int or float, got {type(invalid_min_backoff).__name__}",
    ):
        client.set_min_backoff(invalid_min_backoff)


@pytest.mark.parametrize(
    "invalid_min_backoff", [-1, -10, float("inf"), float("-inf"), float("nan")]
)
def test_set_min_backoff_with_invalid_value(invalid_min_backoff):
    """Test that set_min_backoff raises ValueError for invalid values."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="min_backoff must be a finite value >= 0"):
        client.set_min_backoff(invalid_min_backoff)


def test_set_min_backoff_exceeds_max_backoff():
    """Test that set_min_backoff raises ValueError if it exceeds max_backoff."""
    client = Client.for_testnet()
    client.set_max_backoff(5)

    with pytest.raises(ValueError, match="min_backoff cannot exceed max_backoff"):
        client.set_min_backoff(10)


# Set max_backoff
def test_set_max_backoff_with_valid_param():
    """Test that set_max_backoff updates default value of _max_backoff."""
    client = Client.for_testnet()
    assert client._max_backoff == 8  # default max_backoff = 8 sec

    returned = client.set_max_backoff(20)
    assert client._max_backoff == 20
    assert returned is client

    client.close()


@pytest.mark.parametrize("invalid_max_backoff", ["1", True, False, object(), {}])
def test_set_max_backoff_with_invalid_type(invalid_max_backoff):
    """Test that set_max_backoff raises TypeError for invalid types."""
    client = Client.for_testnet()

    with pytest.raises(
        TypeError,
        match=f"max_backoff must be of type int or float, got {type(invalid_max_backoff).__name__}",
    ):
        client.set_max_backoff(invalid_max_backoff)


@pytest.mark.parametrize(
    "invalid_max_backoff", [-1, -10, float("inf"), float("-inf"), float("nan")]
)
def test_set_max_backoff_with_invalid_value(invalid_max_backoff):
    """Test that set_max_backoff raises ValueError for invalid values."""
    client = Client.for_testnet()

    with pytest.raises(ValueError, match="max_backoff must be a finite value >= 0"):
        client.set_max_backoff(invalid_max_backoff)


def test_set_max_backoff_less_than_min_backoff():
    """Test that set_max_backoff raises ValueError if it is less than min_backoff."""
    client = Client.for_testnet()
    client.set_min_backoff(5)

    with pytest.raises(ValueError, match="max_backoff cannot be less than min_backoff"):
        returned = client.set_max_backoff(2)
        assert returned is client


# Test update_network
def test_update_network_refreshes_nodes_and_returns_self():
    """Test that update_network refreshes network nodes and returns the client."""
    client = Client.for_testnet()

    with patch.object(client.network, "_set_network_nodes") as mock_set_nodes:
        returned = client.update_network()

        mock_set_nodes.assert_called_once()
        assert returned is client

    client.close()

def test_warning_when_grpc_deadline_exceeds_request_timeout():
    """Warn when grpc_deadline is greater than request_timeout."""
    client = Client.for_testnet()
    client.set_request_timeout(2)

    with pytest.warns(UserWarning):
        client.set_grpc_deadline(7)


def test_warning_when_request_timeout_less_than_grpc_deadline():
    """Warn when request_timeout is less than grpc_deadline."""
    client = Client.for_testnet()
    client.set_grpc_deadline(7)

    with pytest.warns(UserWarning):
        client.set_request_timeout(2)


def test_generate_transaction_id_requires_operator_set():
    """Test that generate_transaction_id raises ValueError if operator_account_id is not set."""
    client = Client.for_testnet()
    client.operator_account_id = None  # ensure not set

    with pytest.raises(ValueError, match="Operator account ID must be set"):
        client.generate_transaction_id()

    client.close()


def test_generate_transaction_id_returns_transaction_id(monkeypatch):
    """Test that generate_transaction_id returns a TransactionId object when operator is set."""
    client = Client.for_testnet()
    client.operator_account_id = AccountId(0, 0, 1234)

    txid = client.generate_transaction_id()
    assert isinstance(txid, TransactionId)
    assert txid.account_id == client.operator_account_id

    client.close()


def test_get_node_account_ids_returns_correct_list():
    """Test that get_node_account_ids returns a list of node AccountIds."""
    client = Client.for_testnet()

    # Some nodes with _account_id attributes
    node1 = _Node(AccountId(0, 0, 101), "127.0.0.1:50211", None)
    node2 = _Node(AccountId(0, 0, 102), "127.0.0.1:50212", None)
    client.network.nodes = [node1, node2]

    node_ids = client.get_node_account_ids()
    assert node_ids == [node1._account_id, node2._account_id]

    client.close()


def test_get_node_account_ids_raises_when_no_nodes():
    """Test that get_node_account_ids raises ValueError if no nodes are configured."""
    client = Client.for_testnet()
    client.network.nodes = []

    with pytest.raises(ValueError, match="No nodes available"):
        client.get_node_account_ids()

    client.close()
