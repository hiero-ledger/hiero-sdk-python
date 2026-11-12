from __future__ import annotations

import itertools
import json
from unittest.mock import Mock, patch

import pytest
import requests

from hiero_sdk_python import (
    MirrorNodeContractCallQuery as ExportedCallQuery,
    MirrorNodeContractEstimateGasQuery as ExportedEstimateGasQuery,
    MirrorNodeError as ExportedMirrorNodeError,
)
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.exceptions import MirrorNodeError
from hiero_sdk_python.query.mirror_node_contract_call_query import (
    MirrorNodeContractCallQuery,
)
from hiero_sdk_python.query.mirror_node_contract_estimate_gas_query import (
    MirrorNodeContractEstimateGasQuery,
)
from hiero_sdk_python.query.mirror_node_contract_query import MirrorNodeContractQuery


pytestmark = pytest.mark.unit

REQUEST = "hiero_sdk_python.query._mirror_node_rest.requests.request"
SLEEP = "hiero_sdk_python.query._mirror_node_rest.time.sleep"

QUERY_CLASSES = [MirrorNodeContractCallQuery, MirrorNodeContractEstimateGasQuery]

CONTRACT_ID = ContractId(0, 0, 1234)
CONTRACT_ADDRESS = "00000000000000000000000000000000000004d2"
SENDER_ID = AccountId(0, 0, 5678)
SENDER_ADDRESS = "000000000000000000000000000000000000162e"
OTHER_ADDRESS = "1234567890abcdef1234567890abcdef12345678"
CALL_DATA = bytes.fromhex("ce6d41de")  # getMessage()


def response(status_code: int, body: object = None) -> Mock:
    """Return a mock requests.Response."""
    resp = Mock()
    resp.status_code = status_code
    if isinstance(body, Exception):
        resp.json.side_effect = body
    else:
        resp.json.return_value = body
    return resp


def ok(result: str = "0x" + "00" * 31 + "2a") -> Mock:
    return response(200, {"result": result})


def mock_client(rest_url: str = "https://testnet.mirrornode.hedera.com/api/v1") -> Mock:
    client = Mock()
    client.network.get_mirror_rest_url.return_value = rest_url
    client._request_timeout = 10
    return client


@pytest.fixture(autouse=True)
def client_isinstance():
    """Let the Mock client pass the isinstance(client, Client) check."""
    with patch(
        "hiero_sdk_python.query.mirror_node_contract_query.Client",
        Mock,
    ):
        yield


# Construction and setters


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_constructor_defaults(query_class):
    query = query_class()

    assert query.contract_id is None
    assert query.contract_evm_address is None
    assert query.sender is None
    assert query.sender_evm_address is None
    assert query.function_parameters is None
    assert query.value is None
    assert query.gas_limit is None
    assert query.gas_price is None
    assert query.block_number is None
    assert query.max_attempts == 10
    assert query.max_backoff == 8


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_constructor_with_contract_id(query_class):
    assert query_class(CONTRACT_ID).contract_id == CONTRACT_ID


def test_base_class_is_abstract():
    with pytest.raises(TypeError):
        MirrorNodeContractQuery()


def test_classes_are_exported_from_package():
    assert ExportedCallQuery is MirrorNodeContractCallQuery
    assert ExportedEstimateGasQuery is MirrorNodeContractEstimateGasQuery
    assert ExportedMirrorNodeError is MirrorNodeError


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_setters_return_self(query_class):
    query = query_class()

    assert query.set_contract_id(CONTRACT_ID) is query
    assert query.set_contract_evm_address(OTHER_ADDRESS) is query
    assert query.set_sender(SENDER_ID) is query
    assert query.set_sender_evm_address(OTHER_ADDRESS) is query
    assert query.set_function("getMessage") is query
    assert query.set_function_parameters(CALL_DATA) is query
    assert query.set_value(1) is query
    assert query.set_gas_limit(1) is query
    assert query.set_gas_price(1) is query
    assert query.set_block_number(1) is query
    assert query.set_max_attempts(1) is query
    assert query.set_max_backoff(1) is query


@pytest.mark.parametrize(
    "address",
    [OTHER_ADDRESS, "0x" + OTHER_ADDRESS, "0X" + OTHER_ADDRESS.upper(), f"  0x{OTHER_ADDRESS}  "],
)
def test_evm_address_is_normalized(address):
    query = MirrorNodeContractCallQuery().set_contract_evm_address(address).set_sender_evm_address(address)

    assert query.contract_evm_address == OTHER_ADDRESS
    assert query.sender_evm_address == OTHER_ADDRESS


@pytest.mark.parametrize("address", ["", "0x", "0x1234", OTHER_ADDRESS + "00", "zz" + OTHER_ADDRESS[2:]])
def test_invalid_evm_address_raises_value_error(address):
    with pytest.raises(ValueError, match="contract_evm_address"):
        MirrorNodeContractCallQuery().set_contract_evm_address(address)

    with pytest.raises(ValueError, match="sender_evm_address"):
        MirrorNodeContractCallQuery().set_sender_evm_address(address)


@pytest.mark.parametrize(
    ("setter", "bad_value", "error"),
    [
        ("set_contract_id", "0.0.1234", TypeError),
        ("set_contract_id", None, TypeError),
        ("set_contract_evm_address", b"\x00" * 20, TypeError),
        ("set_sender", "0.0.2", TypeError),
        ("set_sender_evm_address", 123, TypeError),
        ("set_function_parameters", "ce6d41de", TypeError),
        ("set_function_parameters", None, TypeError),
        ("set_value", 1.5, TypeError),
        ("set_value", True, TypeError),
        ("set_value", -1, ValueError),
        ("set_gas_limit", "100", TypeError),
        ("set_gas_limit", -1, ValueError),
        ("set_gas_price", None, TypeError),
        ("set_gas_price", -1, ValueError),
        ("set_block_number", "latest", TypeError),
        ("set_block_number", -1, ValueError),
        ("set_max_attempts", 0, ValueError),
        ("set_max_attempts", 1.0, TypeError),
        ("set_max_backoff", 0.1, ValueError),
        ("set_max_backoff", "8", TypeError),
    ],
)
def test_setter_validation(setter, bad_value, error):
    with pytest.raises(error):
        getattr(MirrorNodeContractCallQuery(), setter)(bad_value)


def test_set_function_validation():
    with pytest.raises(TypeError):
        MirrorNodeContractCallQuery().set_function(None)

    with pytest.raises(ValueError):
        MirrorNodeContractCallQuery().set_function("")

    with pytest.raises(TypeError):
        MirrorNodeContractCallQuery().set_function("getMessage", b"\x00")


def test_set_function_matches_contract_function_parameters():
    params = ContractFunctionParameters().add_bytes32(b"x" * 32)
    query = MirrorNodeContractCallQuery().set_function("setMessage", params)

    expected = ContractFunctionParameters("setMessage").add_bytes32(b"x" * 32).to_bytes()
    assert query.function_parameters == expected


def test_set_function_without_params_is_selector_only():
    query = MirrorNodeContractCallQuery().set_function("getMessage")

    assert query.function_parameters == CALL_DATA


def test_set_function_parameters_accepts_contract_function_parameters():
    query = MirrorNodeContractCallQuery().set_function_parameters(ContractFunctionParameters("getMessage"))

    assert query.function_parameters == CALL_DATA


def test_set_function_parameters_accepts_bytearray():
    query = MirrorNodeContractCallQuery().set_function_parameters(bytearray(CALL_DATA))

    assert query.function_parameters == CALL_DATA
    assert isinstance(query.function_parameters, bytes)


# JSON body


OPTIONAL_FIELDS = {
    "data": (lambda q: q.set_function_parameters(CALL_DATA), "0x" + CALL_DATA.hex()),
    "from": (lambda q: q.set_sender(SENDER_ID), "0x" + SENDER_ADDRESS),
    "gas": (lambda q: q.set_gas_limit(100_000), 100_000),
    "gasPrice": (lambda q: q.set_gas_price(0), 0),
    "value": (lambda q: q.set_value(25), 25),
    "block": (lambda q: q.set_block_number(255), "0xff"),
}

FIELD_COMBINATIONS = [
    combination
    for size in range(len(OPTIONAL_FIELDS) + 1)
    for combination in itertools.combinations(OPTIONAL_FIELDS, size)
]


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
@pytest.mark.parametrize("fields", FIELD_COMBINATIONS, ids=lambda f: "+".join(f) or "none")
def test_payload_for_every_setter_combination(query_class, fields):
    query = query_class().set_contract_id(CONTRACT_ID)
    expected = {"to": "0x" + CONTRACT_ADDRESS, "block": "latest"}

    for field in fields:
        apply, value = OPTIONAL_FIELDS[field]
        apply(query)
        expected[field] = value

    expected["estimate"] = query_class is MirrorNodeContractEstimateGasQuery

    assert query._build_payload() == expected


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_block_defaults_to_latest(query_class):
    payload = query_class().set_contract_id(CONTRACT_ID)._build_payload()

    assert payload["block"] == "latest"


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_block_zero_is_sent_as_block_number(query_class):
    payload = query_class().set_contract_id(CONTRACT_ID).set_block_number(0)._build_payload()

    assert payload["block"] == "0x0"


def test_empty_call_data_is_omitted():
    """The mirror node rejects "data": "0x", so empty call data is left out."""
    payload = MirrorNodeContractCallQuery(CONTRACT_ID).set_function_parameters(b"")._build_payload()

    assert "data" not in payload


def test_estimate_flag_per_subclass():
    assert MirrorNodeContractCallQuery(CONTRACT_ID)._build_payload()["estimate"] is False
    assert MirrorNodeContractEstimateGasQuery(CONTRACT_ID)._build_payload()["estimate"] is True


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_contract_evm_address_takes_precedence_over_contract_id(query_class):
    query = query_class().set_contract_evm_address("0x" + OTHER_ADDRESS).set_contract_id(CONTRACT_ID)

    assert query._build_payload()["to"] == "0x" + OTHER_ADDRESS


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_contract_evm_address_without_contract_id(query_class):
    query = query_class().set_contract_evm_address(OTHER_ADDRESS)

    assert query._build_payload()["to"] == "0x" + OTHER_ADDRESS


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_sender_evm_address_takes_precedence_over_sender(query_class):
    query = query_class(CONTRACT_ID).set_sender_evm_address(OTHER_ADDRESS).set_sender(SENDER_ID)

    assert query._build_payload()["from"] == "0x" + OTHER_ADDRESS


def test_contract_id_with_evm_address_uses_that_address():
    contract_id = ContractId(0, 0, 0, evm_address=bytes.fromhex(OTHER_ADDRESS))

    payload = MirrorNodeContractCallQuery(contract_id)._build_payload()

    assert payload["to"] == "0x" + OTHER_ADDRESS


def test_payload_reflects_contract_id_changed_after_first_build():
    query = MirrorNodeContractCallQuery(CONTRACT_ID)
    query._build_payload()

    query.set_contract_id(ContractId(0, 0, 1))

    assert query._build_payload()["to"] == "0x" + "00" * 19 + "01"


# URL


def test_build_url():
    url = MirrorNodeContractCallQuery()._build_url(mock_client("https://testnet.mirrornode.hedera.com/api/v1/"))

    assert url == "https://testnet.mirrornode.hedera.com/api/v1/contracts/call"


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1"])
def test_build_url_uses_web3_port_for_local_mirror_node(host):
    url = MirrorNodeContractCallQuery()._build_url(mock_client(f"http://{host}:38081/api/v1"))

    assert url == f"http://{host}:8545/api/v1/contracts/call"


# execute


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_execute_without_contract_raises_before_network_call(query_class):
    with patch(REQUEST) as mock_request, pytest.raises(ValueError, match="contract_id or contract_evm_address"):
        query_class().set_function("getMessage").execute(mock_client())

    mock_request.assert_not_called()


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_execute_validates_client_and_timeout(query_class):
    query = query_class(CONTRACT_ID)

    with patch(REQUEST) as mock_request:
        with pytest.raises(ValueError, match="client"):
            query.execute(None)
        with pytest.raises(TypeError, match="timeout"):
            query.execute(mock_client(), timeout="10")
        with pytest.raises(ValueError, match="timeout"):
            query.execute(mock_client(), timeout=0)

    mock_request.assert_not_called()


def test_execute_rejects_non_client():
    with (
        patch("hiero_sdk_python.query.mirror_node_contract_query.Client", type("NotClient", (), {})),
        pytest.raises(TypeError, match="client"),
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).execute(Mock())


def test_call_query_returns_hex_result_and_posts_json():
    result_hex = "0x" + "11" * 32
    query = MirrorNodeContractCallQuery(CONTRACT_ID).set_sender(SENDER_ID).set_function("getMessage")

    with patch(REQUEST, return_value=ok(result_hex)) as mock_request:
        result = query.execute(mock_client(), timeout=5)

    assert result == result_hex
    mock_request.assert_called_once()
    method, url = mock_request.call_args.args
    kwargs = mock_request.call_args.kwargs
    assert method == "POST"
    assert url == "https://testnet.mirrornode.hedera.com/api/v1/contracts/call"
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert 0 < kwargs["timeout"] <= 5
    assert json.loads(kwargs["data"]) == {
        "data": "0x" + CALL_DATA.hex(),
        "to": "0x" + CONTRACT_ADDRESS,
        "from": "0x" + SENDER_ADDRESS,
        "block": "latest",
        "estimate": False,
    }


def test_estimate_gas_query_returns_int():
    query = MirrorNodeContractEstimateGasQuery(CONTRACT_ID).set_function("getMessage")

    with patch(REQUEST, return_value=ok("0x5ac0")) as mock_request:
        gas = query.execute(mock_client())

    assert gas == 0x5AC0
    assert isinstance(gas, int)
    assert json.loads(mock_request.call_args.kwargs["data"])["estimate"] is True


def test_execute_uses_client_request_timeout_by_default():
    client = mock_client()
    client._request_timeout = 3

    with patch(REQUEST, return_value=ok()) as mock_request:
        MirrorNodeContractCallQuery(CONTRACT_ID).execute(client)

    assert 0 < mock_request.call_args.kwargs["timeout"] <= 3


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_transient_503_is_retried(query_class):
    with (
        patch(REQUEST, side_effect=[response(503), ok("0x2a")]) as mock_request,
        patch(SLEEP) as mock_sleep,
    ):
        result = query_class(CONTRACT_ID).execute(mock_client())

    assert result == ("0x2a" if query_class is MirrorNodeContractCallQuery else 42)
    assert mock_request.call_count == 2
    mock_sleep.assert_called_once()


@pytest.mark.parametrize("status_code", [500, 502, 503, 504])
def test_retryable_statuses_are_retried(status_code):
    with (
        patch(REQUEST, side_effect=[response(status_code), ok()]) as mock_request,
        patch(SLEEP),
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).execute(mock_client())

    assert mock_request.call_count == 2


@pytest.mark.parametrize(
    "error",
    [requests.ConnectionError("connection refused"), requests.Timeout("read timed out")],
)
def test_network_failures_are_retried(error):
    with (
        patch(REQUEST, side_effect=[error, ok()]) as mock_request,
        patch(SLEEP),
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).execute(mock_client())

    assert mock_request.call_count == 2


def test_retryable_status_after_max_attempts_raises_mirror_node_error():
    with (
        patch(REQUEST, return_value=response(503)) as mock_request,
        patch(SLEEP),
        pytest.raises(MirrorNodeError) as exc_info,
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).set_max_attempts(3).execute(mock_client())

    assert mock_request.call_count == 3
    assert exc_info.value.status_code == 503


def test_network_failure_after_max_attempts_raises_runtime_error():
    with (
        patch(REQUEST, side_effect=requests.ConnectionError("down")) as mock_request,
        patch(SLEEP),
        pytest.raises(RuntimeError, match="after 3 attempts") as exc_info,
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).set_max_attempts(3).execute(mock_client())

    assert mock_request.call_count == 3
    assert not isinstance(exc_info.value, MirrorNodeError)
    assert isinstance(exc_info.value.__cause__, requests.ConnectionError)


@pytest.mark.parametrize("query_class", QUERY_CLASSES)
def test_revert_raises_with_mirror_node_messages_and_is_not_retried(query_class):
    body = {
        "_status": {
            "messages": [
                {
                    "message": "CONTRACT_REVERT_EXECUTED",
                    "detail": "Only the owner can update the message.",
                    "data": "0x08c379a0",
                }
            ]
        }
    }

    with (
        patch(REQUEST, return_value=response(400, body)) as mock_request,
        patch(SLEEP) as mock_sleep,
        pytest.raises(MirrorNodeError) as exc_info,
    ):
        query_class(CONTRACT_ID).set_max_attempts(5).execute(mock_client())

    error = exc_info.value
    assert error.status_code == 400
    assert error.messages == ["CONTRACT_REVERT_EXECUTED: Only the owner can update the message."]
    assert error.data == ["0x08c379a0"]
    assert "Only the owner can update the message." in str(error)
    assert mock_request.call_count == 1
    mock_sleep.assert_not_called()


@pytest.mark.parametrize(
    ("status_code", "phrase"),
    [(404, "Not Found"), (415, "Unsupported Media Type"), (429, "Too Many Requests")],
)
def test_non_retryable_statuses_raise_clear_error(status_code, phrase):
    with (
        patch(REQUEST, return_value=response(status_code, ValueError("no json"))) as mock_request,
        patch(SLEEP) as mock_sleep,
        pytest.raises(MirrorNodeError, match=f"HTTP {status_code}: {phrase}") as exc_info,
    ):
        MirrorNodeContractCallQuery(CONTRACT_ID).set_max_attempts(5).execute(mock_client())

    assert exc_info.value.status_code == status_code
    assert mock_request.call_count == 1
    mock_sleep.assert_not_called()


def test_mirror_node_error_is_runtime_error():
    assert issubclass(MirrorNodeError, RuntimeError)


@pytest.mark.parametrize(
    "body",
    [ValueError("not json"), [], {}, {"result": None}, {"result": 42}, {"result": "2a"}],
)
def test_malformed_success_response_raises_value_error(body):
    with patch(REQUEST, return_value=response(200, body)), pytest.raises(ValueError, match="malformed"):
        MirrorNodeContractCallQuery(CONTRACT_ID).execute(mock_client())


@pytest.mark.parametrize("result", ["0x", "0xnothex"])
def test_malformed_gas_estimate_raises_value_error(result):
    with patch(REQUEST, return_value=ok(result)), pytest.raises(ValueError, match="malformed gas estimate"):
        MirrorNodeContractEstimateGasQuery(CONTRACT_ID).execute(mock_client())


def test_str_and_repr():
    query = MirrorNodeContractEstimateGasQuery(CONTRACT_ID).set_function("getMessage").set_gas_limit(1)

    text = str(query)
    assert text == repr(query)
    assert text.startswith("MirrorNodeContractEstimateGasQuery(")
    assert "contract_id=0.0.1234" in text
    assert "function_parameters=ce6d41de" in text
    assert "gas_limit=1" in text
