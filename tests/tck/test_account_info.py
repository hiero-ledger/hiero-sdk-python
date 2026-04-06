"""Unit tests for the GetAccountInfo TCK endpoint."""

from unittest.mock import MagicMock, patch

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_info import AccountInfo
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.staking_info import StakingInfo
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_freeze_status import TokenFreezeStatus
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_kyc_status import TokenKycStatus
from hiero_sdk_python.tokens.token_relationship import TokenRelationship
from tck.errors import HIERO_ERROR, JsonRpcError
from tck.handlers import registry
from tck.handlers.account import get_account_info
from tck.handlers.registry import dispatch
from tck.param.account import GetAccountInfoParams
from tck.util import client_utils

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def setup_registry_and_clients():
    """Reset handler and client registries for isolated test execution."""
    registry._HANDLERS.clear()
    client_utils._CLIENTS.clear()

    registry.rpc_method("getAccountInfo")(get_account_info)

    yield

    registry._HANDLERS.clear()
    client_utils._CLIENTS.clear()


@pytest.fixture
def params_dict():
    """Provide a valid getAccountInfo request payload."""
    return {"accountId": "0.0.123", "sessionId": "sess1"}


def test_parse_json_params_success(params_dict):
    """parse_json_params should parse both accountId and sessionId."""
    params = GetAccountInfoParams.parse_json_params(params_dict)

    assert params.accountId == "0.0.123"
    assert params.sessionId == "sess1"


def test_parse_json_params_missing_account_id_defaults_to_none():
    """parse_json_params should allow missing accountId and keep it None."""
    params = GetAccountInfoParams.parse_json_params({"sessionId": "sess1"})

    assert params.accountId is None
    assert params.sessionId == "sess1"


@patch("tck.handlers.account.get_client")
@patch("hiero_sdk_python.query.account_info_query.AccountInfoQuery.execute")
def test_get_account_info_success_mapping(mock_execute, mock_get_client, params_dict):
    """Endpoint should map AccountInfo response fields to TCK response shape."""
    mock_get_client.return_value = MagicMock()

    key = PrivateKey.generate_ed25519().public_key()
    expected_key = key.to_string_der()

    mock_execute.return_value = AccountInfo(
        account_id=AccountId.from_string("0.0.123"),
        contract_account_id="000000000000000000000000000000000000007b",
        is_deleted=False,
        proxy_received=Hbar.from_tinybars(10),
        key=key,
        balance=Hbar.from_tinybars(1000),
        receiver_signature_required=True,
        expiration_time=Timestamp(1700000000, 123),
        auto_renew_period=Duration(7776000),
        token_relationships=[
            TokenRelationship(
                token_id=TokenId(0, 0, 456),
                symbol="TOK",
                balance=12,
                kyc_status=TokenKycStatus.GRANTED,
                freeze_status=TokenFreezeStatus.UNFROZEN,
                decimals=2,
                automatic_association=True,
            )
        ],
        account_memo="memo",
        owned_nfts=2,
        max_automatic_token_associations=11,
        staking_info=StakingInfo(
            decline_reward=False,
            stake_period_start=Timestamp(1700000001, 0),
            pending_reward=Hbar.from_tinybars(3),
            staked_to_me=Hbar.from_tinybars(4),
            staked_account_id=AccountId.from_string("0.0.7"),
        ),
    )

    response = dispatch("getAccountInfo", params_dict)

    assert response["accountId"] == "0.0.123"
    assert response["contractAccountId"] == "000000000000000000000000000000000000007b"
    assert response["isDeleted"] is False
    assert response["proxyReceived"] == "10"
    assert response["key"] == expected_key
    assert response["balance"] == "1000"
    assert response["sendRecordThreshold"] == "0"
    assert response["receiveRecordThreshold"] == "0"
    assert response["isReceiverSignatureRequired"] is True
    assert response["expirationTime"] == "1700000000.000000123"
    assert response["autoRenewPeriod"] == "7776000"
    assert response["tokenRelationships"]["0.0.456"] == {
        "tokenId": "0.0.456",
        "symbol": "TOK",
        "balance": "12",
        "kycStatus": "GRANTED",
        "freezeStatus": "UNFROZEN",
        "decimals": "2",
        "automaticAssociation": True,
    }
    assert response["accountMemo"] == "memo"
    assert response["ownedNfts"] == "2"
    assert response["maxAutomaticTokenAssociations"] == "11"
    assert response["aliasKey"] == ""
    assert response["ledgerId"] == ""
    assert response["ethereumNonce"] == "0"
    assert response["liveHashes"] == []
    assert response["hbarAllowances"] == []
    assert response["tokenAllowances"] == []
    assert response["nftAllowances"] == []
    assert response["stakingInfo"] == {
        "declineStakingReward": False,
        "stakePeriodStart": "1700000001.000000000",
        "pendingReward": "3",
        "stakedToMe": "4",
        "stakedAccountId": "0.0.7",
        "stakedNodeId": None,
    }


def test_get_account_info_missing_account_id_maps_to_hiero_error():
    """Missing accountId should map to HIERO_ERROR with INVALID_ACCOUNT_ID."""
    with pytest.raises(JsonRpcError) as exception:
        dispatch("getAccountInfo", {"sessionId": "sess1"})

    assert exception.value.code == HIERO_ERROR
    assert exception.value.data == {"status": ResponseCode.INVALID_ACCOUNT_ID.name}


def test_get_account_info_invalid_account_id_maps_to_hiero_error():
    """Malformed accountId should map to HIERO_ERROR with INVALID_ACCOUNT_ID."""
    with pytest.raises(JsonRpcError) as exception:
        dispatch("getAccountInfo", {"sessionId": "sess1", "accountId": "invalid-id"})

    assert exception.value.code == HIERO_ERROR
    assert exception.value.data == {"status": ResponseCode.INVALID_ACCOUNT_ID.name}


@patch("tck.handlers.account.get_client")
@patch("hiero_sdk_python.query.account_info_query.AccountInfoQuery.execute")
def test_get_account_info_precheck_error_maps_to_hiero_error(mock_execute, mock_get_client):
    """SDK PrecheckError should map to HIERO_ERROR preserving response status."""
    mock_get_client.return_value = MagicMock()
    mock_execute.side_effect = PrecheckError(status=ResponseCode.ACCOUNT_DELETED)

    with pytest.raises(JsonRpcError) as exception:
        dispatch("getAccountInfo", {"sessionId": "sess1", "accountId": "0.0.123"})

    assert exception.value.code == HIERO_ERROR
    assert exception.value.data == {"status": ResponseCode.ACCOUNT_DELETED.name}
