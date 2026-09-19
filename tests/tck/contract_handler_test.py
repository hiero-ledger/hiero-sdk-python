"""Test cases for the TCK contract handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.response_code import ResponseCode
from tck.errors import HIERO_ERROR, INTERNAL_ERROR, INVALID_PARAMS, JsonRpcError
from tck.handlers import contract as contract_handlers
from tck.handlers.registry import safe_dispatch
from tck.param.contract import ContractGetBytecodeParams, CreateContractParams
from tck.util.constants import DEFAULT_GRPC_TIMEOUT


pytestmark = pytest.mark.unit


class TestBuildCreateContractTransaction:
    def test_bytecode_file_id_wins_when_both_sources_supplied(self):
        params = CreateContractParams(
            sessionId="session-1",
            initcode="0x60006000",
            bytecodeFileId="0.0.123",
            gas="1000000",
        )

        transaction = contract_handlers._build_create_contract_transaction(params)

        assert str(transaction.bytecode_file_id) == "0.0.123"
        assert transaction.bytecode is None

    def test_invalid_gas_raises_invalid_params(self):
        params = CreateContractParams(sessionId="session-1", gas="not-a-number")

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_create_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS

    @pytest.mark.parametrize("gas", ["9223372036854775808", "-9223372036854775809"])
    def test_gas_out_of_int64_range_raises_invalid_params(self, gas):
        params = CreateContractParams(sessionId="session-1", gas=gas)

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_create_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS


class TestContractGetBytecode:
    """Covers the six cases in the ContractByteCodeQuery spec plus param handling."""

    BYTECODE = bytes.fromhex("006080ff")
    HEX_BYTECODE = "0x006080ff"

    @pytest.fixture
    def bytecode_query_mocks(self):
        with (
            patch("tck.handlers.contract.get_client", return_value=MagicMock(spec=Client)) as get_client,
            patch("tck.handlers.contract.ContractBytecodeQuery.execute", autospec=True) as execute,
        ):
            execute.return_value = self.BYTECODE
            yield get_client, execute

    def test_parse_bytecode_params(self):
        values = {
            "sessionId": "session-1",
            "contractId": "0.0.123",
            "queryPayment": "1",
            "maxQueryPayment": "1000000000000",
        }
        assert ContractGetBytecodeParams.parse_json_params(values) == ContractGetBytecodeParams(**values)
        assert ContractGetBytecodeParams.parse_json_params({"sessionId": "session-1"}) == ContractGetBytecodeParams(
            sessionId="session-1"
        )

    @pytest.mark.parametrize("params", [{}, {"sessionId": ""}, {"sessionId": None}])
    def test_invalid_session(self, params):
        result = safe_dispatch("contractGetBytecode", params, 1)
        assert result["error"]["code"] == INVALID_PARAMS

    @pytest.mark.parametrize("method", ["contractGetBytecode", "contractByteCodeQuery"])
    def test_dispatch_returns_hex_bytecode(self, method, bytecode_query_mocks):
        """Both the spec method name and the name the TCK driver calls are registered."""
        get_client, execute = bytecode_query_mocks

        result = safe_dispatch(method, {"sessionId": "session-1", "contractId": "0.0.123"}, 1)

        assert result == {"contractId": "0.0.123", "bytecode": self.HEX_BYTECODE}
        get_client.assert_called_once_with("session-1")
        execute.assert_called_once()
        query, client = execute.call_args.args
        assert client is get_client.return_value
        assert str(query.contract_id) == "0.0.123"
        assert query._grpc_deadline == DEFAULT_GRPC_TIMEOUT
        # Unset payments stay unset so the SDK keeps its own cost lookup and defaults.
        assert query.payment_amount is None
        assert query.max_query_payment is None

    def test_empty_bytecode_is_omitted(self, bytecode_query_mocks):
        """A contract with no bytecode drops the field, matching the JS TCK server."""
        _, execute = bytecode_query_mocks
        execute.return_value = b""

        result = safe_dispatch("contractGetBytecode", {"sessionId": "session-1", "contractId": "0.0.123"}, 1)

        assert result == {"contractId": "0.0.123"}

    @pytest.mark.parametrize("payment", ["0", "1", "100000000", "1000000000000"])
    @pytest.mark.parametrize(
        "field,attribute", [("queryPayment", "payment_amount"), ("maxQueryPayment", "max_query_payment")]
    )
    def test_payments_are_tinybars(self, field, attribute, payment, bytecode_query_mocks):
        _, execute = bytecode_query_mocks

        result = safe_dispatch(
            "contractGetBytecode", {"sessionId": "session-1", "contractId": "0.0.123", field: payment}, 1
        )

        assert result["bytecode"] == self.HEX_BYTECODE
        query = execute.call_args.args[0]
        assert getattr(query, attribute).to_tinybars() == int(payment)

    @pytest.mark.parametrize("method", ["contractGetBytecode", "contractByteCodeQuery"])
    def test_missing_contract_id(self, method, bytecode_query_mocks):
        _, execute = bytecode_query_mocks

        result = safe_dispatch(method, {"sessionId": "session-1"}, 1)

        assert result["error"]["code"] == HIERO_ERROR
        assert result["error"]["data"]["status"] == "INVALID_CONTRACT_ID"
        execute.assert_not_called()

    @pytest.mark.parametrize("contract_id", ["not-a-contract", ""])
    def test_malformed_contract_id(self, contract_id, bytecode_query_mocks):
        _, execute = bytecode_query_mocks

        result = safe_dispatch("contractGetBytecode", {"sessionId": "session-1", "contractId": contract_id}, 1)

        assert result["error"]["code"] == INTERNAL_ERROR
        execute.assert_not_called()

    def test_nonexistent_contract_id(self, bytecode_query_mocks):
        _, execute = bytecode_query_mocks
        execute.side_effect = PrecheckError(ResponseCode.INVALID_CONTRACT_ID)

        result = safe_dispatch("contractGetBytecode", {"sessionId": "session-1", "contractId": "123.456.789"}, 1)

        assert result["error"]["code"] == HIERO_ERROR
        assert result["error"]["data"]["status"] == "INVALID_CONTRACT_ID"
        assert str(execute.call_args.args[0].contract_id) == "123.456.789"
