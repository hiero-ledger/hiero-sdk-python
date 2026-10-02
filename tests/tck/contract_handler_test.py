"""Test cases for the TCK Contract handlers."""

from __future__ import annotations

import pytest

from tck.errors import INVALID_PARAMS, JsonRpcError
from tck.handlers import contract as contract_handlers
from tck.param.contract import CreateContractParams, UpdateContractParams


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


class TestBuildUpdateContractTransaction:
    def test_only_supplied_fields_are_set(self):
        params = UpdateContractParams(
            sessionId="session-1",
            contractId="0.0.123",
            memo="updated memo",
        )

        transaction = contract_handlers._build_update_contract_transaction(params)

        assert str(transaction.contract_id) == "0.0.123"
        assert transaction.contract_memo == "updated memo"
        assert transaction.admin_key is None
        assert transaction.auto_renew_period is None
        assert transaction.expiration_time is None
        assert transaction.auto_renew_account_id is None
        assert transaction.max_automatic_token_associations is None
        assert transaction.staked_account_id is None
        assert transaction.staked_node_id is None
        assert transaction.decline_reward is None

    def test_missing_contract_id_builds_without_raising(self):
        params = UpdateContractParams(
            sessionId="session-1",
            memo="updated memo",
        )

        transaction = contract_handlers._build_update_contract_transaction(params)
        proto_body = transaction._build_proto_body()

        assert not proto_body.HasField("contractID")
        assert transaction.contract_memo == "updated memo"

    def test_staked_node_id_wins_when_both_targets_supplied(self):
        params = UpdateContractParams(
            sessionId="session-1",
            stakedAccountId="0.0.123",
            stakedNodeId="5",
        )

        transaction = contract_handlers._build_update_contract_transaction(params)

        assert transaction.staked_account_id is None
        assert transaction.staked_node_id == 5

    @pytest.mark.parametrize(
        "value",
        [
            True,
            2**31,
        ],
    )
    def test_invalid_max_automatic_token_associations_raises_invalid_params(self, value):
        params = UpdateContractParams(
            sessionId="session-1",
            maxAutomaticTokenAssociations=value,
        )

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_update_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("expirationTime", "9223372036854775808"),
            ("expirationTime", "-9223372036854775809"),
            ("stakedNodeId", "9223372036854775808"),
            ("stakedNodeId", "-9223372036854775809"),
        ],
    )
    def test_int64_field_out_of_range_raises_invalid_params(self, field_name, value):
        params = UpdateContractParams(
            sessionId="session-1",
            **{field_name: value},
        )

        with pytest.raises(JsonRpcError) as excinfo:
            contract_handlers._build_update_contract_transaction(params)

        assert excinfo.value.code == INVALID_PARAMS
