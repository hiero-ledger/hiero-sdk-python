"""Test cases for the TCK createContract handler."""

from __future__ import annotations

import pytest

from tck.errors import INVALID_PARAMS, JsonRpcError
from tck.handlers import contract as contract_handlers
from tck.param.contract import CreateContractParams, DeleteContractParams


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


class TestBuildDeleteContractTransaction:
    def test_single_transfer_contract_id(self):
        params = DeleteContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            transferContractId="0.0.456",
            permanentRemoval=False,
        )
        transaction = contract_handlers._build_delete_contract_transaction(params)

        assert str(transaction.contract_id) == "0.0.123"
        assert str(transaction.transfer_contract_id) == "0.0.456"
        assert transaction.transfer_account_id is None
        assert transaction.permanent_removal is False

    def test_single_transfer_account_id(self):
        params = DeleteContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            transferAccountId="0.0.789",
            permanentRemoval=True,
        )
        transaction = contract_handlers._build_delete_contract_transaction(params)

        assert str(transaction.contract_id) == "0.0.123"
        assert transaction.transfer_contract_id is None
        assert str(transaction.transfer_account_id) == "0.0.789"
        assert transaction.permanent_removal is True

    def test_transfer_contract_id_wins_when_both_supplied(self):
        params = DeleteContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            transferContractId="0.0.456",
            transferAccountId="0.0.789",
        )
        transaction = contract_handlers._build_delete_contract_transaction(params)

        assert str(transaction.contract_id) == "0.0.123"
        assert str(transaction.transfer_contract_id) == "0.0.456"
        assert transaction.transfer_account_id is None

    def test_missing_contract_id_raises_invalid_params(self):
        params = DeleteContractParams(sessionId="session-1", contractId=None)

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_delete_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS

    @pytest.mark.parametrize("contract_id", ["invalid-id", "", "0.0.abc"])
    def test_malformed_contract_id_raises_invalid_params(self, contract_id):
        params = DeleteContractParams(sessionId="session-1", contractId=contract_id)

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_delete_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS

    @pytest.mark.parametrize("bad_id", ["invalid-id", "0.0.abc"])
    def test_malformed_transfer_contract_id_raises_invalid_params(self, bad_id):
        params = DeleteContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            transferContractId=bad_id,
        )

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_delete_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS

    @pytest.mark.parametrize("bad_id", ["invalid-id", "0.0.abc"])
    def test_malformed_transfer_account_id_raises_invalid_params(self, bad_id):
        params = DeleteContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            transferAccountId=bad_id,
        )

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_delete_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS
