from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from tck.param.common import CommonTransactionParams


pytestmark = pytest.mark.unit


@pytest.fixture
def json_params_dict():
    return {
        "transactionId": "0.0.90@1773846665.518000566",
        "maxTransactionFee": "100000000",
        "validTransactionDuration": "120",
        "memo": "Test Memo",
        "regenerateTransactionId": "False",
        "signers": [
            "30540201010420d0b3d3c266ad9aa414f41e3050d64f4012765abc94a745cbd0607bf41da51a96a00706052b8104000aa124032200037aa11171d538daf5c624f313bc106fff289e4a24768880d0fa71dd302a1fa9e7"
        ],
    }


def test_parse_common_params(json_params_dict):
    """Test the commonTransaction params can be parse form dict"""
    params = CommonTransactionParams.parse_json_params(json_params_dict)

    assert isinstance(params.transactionId, str)
    assert params.transactionId == "0.0.90@1773846665.518000566"

    assert isinstance(params.maxTransactionFee, int)
    assert params.maxTransactionFee == 100000000

    assert isinstance(params.memo, str)
    assert params.memo == "Test Memo"

    assert isinstance(params.validTransactionDuration, int)
    assert params.validTransactionDuration == 120

    assert isinstance(params.regenerateTransactionId, bool)
    assert params.regenerateTransactionId == False

    assert isinstance(params.signers, list)
    assert len(params.signers) == 1
    assert (
        params.signers[0]
        == "30540201010420d0b3d3c266ad9aa414f41e3050d64f4012765abc94a745cbd0607bf41da51a96a00706052b8104000aa124032200037aa11171d538daf5c624f313bc106fff289e4a24768880d0fa71dd302a1fa9e7"
    )


def test_apply_common_params(json_params_dict):
    """Test commonTransactionParams can be apply to transaction"""
    params = CommonTransactionParams.parse_json_params(json_params_dict)
    tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate())

    client = MagicMock(spec=Client)

    tx.freeze_with = MagicMock()
    tx.sign = MagicMock()

    params.apply_common_params(tx, client)

    assert tx.memo == "Test Memo"
    assert tx.transaction_valid_duration == 120
    assert str(tx.transaction_id) == "0.0.90@1773846665.518000566"

    tx.freeze_with.assert_called_once_with(client)
    assert tx.sign.call_count == 1
