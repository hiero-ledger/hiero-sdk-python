"""Test cases for the TCK createContract handler."""

from __future__ import annotations

import importlib

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from tck.errors import JsonRpcError
from tck.handlers import contract as contract_handlers
from tck.handlers.registry import get_handler
from tck.param.contract import CreateContractParams
from tck.util.param_utils import decode_hex


pytestmark = pytest.mark.unit


class TestDecodeHex:
    def test_decodes_plain_hex(self):
        assert decode_hex("60006000") == b"\x60\x00\x60\x00"

    def test_decodes_0x_prefixed_hex(self):
        assert decode_hex("0x60006000") == b"\x60\x00\x60\x00"

    def test_rejects_non_hex_characters(self):
        with pytest.raises(ValueError):
            decode_hex("0xZZ")

    def test_rejects_odd_length(self):
        with pytest.raises(ValueError):
            decode_hex("0x123")


class TestCreateContractParams:
    def test_parses_all_params(self):
        params = CreateContractParams.parse_json_params(
            {
                "sessionId": "session-1",
                "bytecodeFileId": "0.0.123",
                "initcode": "0x60006000",
                "adminKey": PrivateKey.generate_ed25519().public_key().to_string_der(),
                "gas": "1000000",
                "initialBalance": "1000",
                "constructorParameters": "0xabcd",
                "autoRenewPeriod": "7000000",
                "autoRenewAccountId": "0.0.5",
                "memo": "contract test",
                "stakedAccountId": "0.0.6",
                "stakedNodeId": "3",
                "declineStakingReward": True,
                "maxAutomaticTokenAssociations": 10,
                "commonTransactionParams": {"memo": "tx memo"},
            }
        )

        assert params.sessionId == "session-1"
        assert params.bytecodeFileId == "0.0.123"
        assert params.initcode == "0x60006000"
        assert params.gas == "1000000"
        assert params.initialBalance == "1000"
        assert params.constructorParameters == "0xabcd"
        assert params.autoRenewPeriod == "7000000"
        assert params.autoRenewAccountId == "0.0.5"
        assert params.memo == "contract test"
        assert params.stakedAccountId == "0.0.6"
        assert params.stakedNodeId == "3"
        assert params.declineStakingReward is True
        assert params.maxAutomaticTokenAssociations == 10
        assert params.commonTransactionParams is not None
        assert params.commonTransactionParams.memo == "tx memo"

    def test_requires_session_id(self):
        with pytest.raises(ValueError):
            CreateContractParams.parse_json_params({"gas": "1000000"})

    def test_absent_params_stay_none(self):
        params = CreateContractParams.parse_json_params({"sessionId": "session-1"})

        assert params.bytecodeFileId is None
        assert params.initcode is None
        assert params.adminKey is None
        assert params.gas is None
        assert params.declineStakingReward is None
        assert params.maxAutomaticTokenAssociations is None
        assert params.commonTransactionParams is None


class TestBuildCreateContractTransaction:
    def test_maps_all_params(self):
        admin_key = PrivateKey.generate_ed25519().public_key()
        params = CreateContractParams(
            sessionId="session-1",
            initcode="0x60006000",
            adminKey=admin_key.to_string_der(),
            gas="1000000",
            initialBalance="1000",
            constructorParameters="0xabcd",
            autoRenewPeriod="7000000",
            autoRenewAccountId="0.0.5",
            memo="contract test",
            stakedAccountId="0.0.6",
            stakedNodeId="3",
            declineStakingReward=True,
            maxAutomaticTokenAssociations=10,
        )

        transaction = contract_handlers._build_create_contract_transaction(params)

        assert transaction.bytecode == b"\x60\x00\x60\x00"
        assert transaction.bytecode_file_id is None
        assert transaction.gas == 1000000
        assert transaction.initial_balance == 1000
        assert transaction.parameters == b"\xab\xcd"
        assert transaction.auto_renew_period.seconds == 7000000
        assert str(transaction.auto_renew_account_id) == "0.0.5"
        assert transaction.contract_memo == "contract test"
        assert str(transaction.staked_account_id) == "0.0.6"
        assert transaction.staked_node_id == 3
        assert transaction.decline_reward is True
        assert transaction.max_automatic_token_associations == 10
        assert transaction.admin_key is not None
        assert transaction.admin_key.to_bytes() == admin_key.to_bytes()

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

    def test_neither_bytecode_source_left_unset_for_network(self):
        params = CreateContractParams(sessionId="session-1", gas="1000000")

        transaction = contract_handlers._build_create_contract_transaction(params)

        assert transaction.bytecode is None
        assert transaction.bytecode_file_id is None

    def test_default_auto_renew_period_preserved_when_absent(self):
        params = CreateContractParams(sessionId="session-1", gas="1000000")

        transaction = contract_handlers._build_create_contract_transaction(params)

        assert transaction.auto_renew_period.seconds == 90 * 24 * 60 * 60

    def test_invalid_gas_raises_invalid_params(self):
        params = CreateContractParams(sessionId="session-1", gas="not-a-number")

        with pytest.raises(JsonRpcError):
            contract_handlers._build_create_contract_transaction(params)

    def test_int64_boundaries_pass_through_to_the_network(self):
        params = CreateContractParams(
            sessionId="session-1",
            gas="9223372036854775807",
            initialBalance="-9223372036854775808",
        )

        transaction = contract_handlers._build_create_contract_transaction(params)

        assert transaction.gas == 9223372036854775807
        assert transaction.initial_balance == -9223372036854775808

    @pytest.mark.parametrize("gas", ["-1", "-9223372036854775808"])
    def test_negative_gas_raises_sdk_error(self, gas):
        """The TCK driver expects an internal SDK error for negative gas, matching the JS SDK."""
        params = CreateContractParams(sessionId="session-1", gas=gas)

        with pytest.raises(ValueError, match="Gas cannot be negative"):
            contract_handlers._build_create_contract_transaction(params)

    @pytest.mark.parametrize("gas", ["9223372036854775808", "-9223372036854775809"])
    def test_gas_out_of_int64_range_raises_invalid_params(self, gas):
        params = CreateContractParams(sessionId="session-1", gas=gas)

        with pytest.raises(JsonRpcError):
            contract_handlers._build_create_contract_transaction(params)

    def test_invalid_initcode_hex_raises_value_error(self):
        params = CreateContractParams(sessionId="session-1", initcode="0xZZ", gas="1000000")

        with pytest.raises(ValueError):
            contract_handlers._build_create_contract_transaction(params)


def test_create_contract_is_registered():
    importlib.reload(contract_handlers)
    assert get_handler("createContract") is not None
