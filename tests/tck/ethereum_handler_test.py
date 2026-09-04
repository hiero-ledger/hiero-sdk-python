"""Test cases for the TCK createEthereumTransaction handler."""

from __future__ import annotations

import importlib
import sys

import pytest

from tck.errors import JsonRpcError
from tck.handlers import ethereum as ethereum_handlers
from tck.param.ethereum import CreateEthereumTransactionParams


pytestmark = pytest.mark.unit


class TestCreateEthereumTransactionParams:
    def test_parses_all_params(self):
        params = CreateEthereumTransactionParams.parse_json_params(
            {
                "sessionId": "session-1",
                "ethereumData": "0x02f8...abcd",
                "callDataFileId": "0.0.123",
                "maxGasAllowance": "100000000",
                "commonTransactionParams": {"memo": "tx memo"},
            }
        )

        assert params.sessionId == "session-1"
        assert params.ethereumData == "0x02f8...abcd"
        assert params.callDataFileId == "0.0.123"
        assert params.maxGasAllowance == "100000000"
        assert params.commonTransactionParams is not None
        assert params.commonTransactionParams.memo == "tx memo"

    def test_requires_session_id(self):
        with pytest.raises(ValueError):
            CreateEthereumTransactionParams.parse_json_params(
                {"ethereumData": "0x1234"}
            )

    def test_absent_params_stay_none(self):
        params = CreateEthereumTransactionParams.parse_json_params(
            {"sessionId": "session-1"}
        )

        assert params.ethereumData is None
        assert params.callDataFileId is None
        assert params.maxGasAllowance is None
        assert params.commonTransactionParams is None


class TestBuildCreateEthereumTransaction:
    def test_maps_all_params(self):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            ethereumData="0x1234abcd",
            callDataFileId="0.0.123",
            maxGasAllowance="100000000",
        )

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.ethereum_data == b"\x12\x34\xab\xcd"
        assert str(transaction.call_data) == "0.0.123"
        assert transaction.max_gas_allowed == 100000000

    def test_absent_params_left_unset_for_sdk_defaults(self):
        params = CreateEthereumTransactionParams(sessionId="session-1")

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.ethereum_data is None
        assert transaction.call_data is None
        assert transaction.max_gas_allowed is None

    def test_ethereum_data_accepts_0x_prefix(self):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            ethereumData="1234abcd",
        )

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.ethereum_data == b"\x12\x34\xab\xcd"

    def test_invalid_ethereum_data_hex_raises_sdk_error(self):
        """Malformed hex should raise an SDK error."""
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            ethereumData="0xZZ",
        )

        with pytest.raises(ValueError):
            ethereum_handlers._build_create_ethereum_transaction(params)

    def test_invalid_call_data_file_id_raises_sdk_error(self):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            callDataFileId="invalid",
        )

        with pytest.raises(ValueError):
            ethereum_handlers._build_create_ethereum_transaction(params)

    def test_zero_allowance_passes_through_to_the_sdk(self):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            maxGasAllowance="0",
        )

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.max_gas_allowed == 0

    @pytest.mark.parametrize(
        "allowance",
        [
            "9223372036854775807",
            "9223372036854775806",
        ],
    )
    def test_int64_max_values_pass_through_to_the_sdk(self, allowance):
        """Valid int64 maximum values pass through to the SDK."""
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            maxGasAllowance=allowance,
        )

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.max_gas_allowed == int(allowance)

    @pytest.mark.parametrize(
        "allowance",
        [
            "-1",
            "-9223372036854775808",
            "-9223372036854775807",
        ],
    )
    def test_negative_allowance_passes_through_to_the_network(self, allowance):
        """Negative allowances pass through to the SDK."""
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            maxGasAllowance=allowance,
        )

        transaction = ethereum_handlers._build_create_ethereum_transaction(params)

        assert transaction.max_gas_allowed == int(allowance)

    @pytest.mark.parametrize(
        "allowance",
        [
            "9223372036854775808",
            "-9223372036854775809",
        ],
    )
    def test_allowance_out_of_int64_range_raises_invalid_params(self, allowance):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            maxGasAllowance=allowance,
        )

        with pytest.raises(JsonRpcError):
            ethereum_handlers._build_create_ethereum_transaction(params)

    def test_invalid_allowance_raises_invalid_params(self):
        params = CreateEthereumTransactionParams(
            sessionId="session-1",
            maxGasAllowance="not-a-number",
        )

        with pytest.raises(JsonRpcError):
            ethereum_handlers._build_create_ethereum_transaction(params)


def test_create_ethereum_transaction_registered_via_package_import():
    """Importing tck.handlers registers createEthereumTransaction."""
    saved = {
        name: mod
        for name, mod in sys.modules.items()
        if name == "tck.handlers" or name.startswith("tck.handlers.")
    }

    try:
        for name in saved:
            del sys.modules[name]

        fresh_handlers = importlib.import_module("tck.handlers")

        assert fresh_handlers.get_handler("createEthereumTransaction") is not None
    finally:
        sys.modules.update(saved)
        sys.modules["tck"].handlers = saved["tck.handlers"]
