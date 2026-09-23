"""Test cases for the TCK createContract handler."""

from __future__ import annotations

import pytest

from tck.errors import INVALID_PARAMS, JsonRpcError
from tck.handlers import contract as contract_handlers
from tck.param.contract import CreateContractParams


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
