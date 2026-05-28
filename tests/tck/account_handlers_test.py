from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.response_code import ResponseCode
from tck.handlers.account import _build_update_account_transaction, update_account
from tck.param.account import UpdateAccountParams
from tck.util.client_utils import remove_client, store_client
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def test_update_account_params_parse_json():
    params = UpdateAccountParams.parse_json_params(
        {
            "sessionId": "session-1",
            "accountId": "0.0.123",
            "key": "abcd",
            "receiverSignatureRequired": "true",
            "autoRenewPeriod": "5184000",
            "expirationTime": "1704067200",
            "memo": "",
            "maxAutoTokenAssociations": "100",
            "stakedAccountId": "0.0.3",
            "stakedNodeId": "10",
            "declineStakingRewards": "false",
            "commonTransactionParams": {
                "maxTransactionFee": "100000000",
                "signers": [],
            },
        }
    )

    assert params.sessionId == "session-1"
    assert params.accountId == "0.0.123"
    assert params.key == "abcd"
    assert params.receiverSignatureRequired is True
    assert params.autoRenewPeriod == 5184000
    assert params.expirationTime == 1704067200
    assert params.memo == ""
    assert params.maxAutoTokenAssociations == 100
    assert params.stakedAccountId == "0.0.3"
    assert params.stakedNodeId == 10
    assert params.declineStakingReward is False
    assert params.commonTransactionParams.maxTransactionFee == 100000000


def test_build_update_account_transaction_sets_tck_fields():
    public_key = PrivateKey.generate_ed25519().public_key()

    transaction = _build_update_account_transaction(
        UpdateAccountParams(
            sessionId="session-1",
            accountId="0.0.123",
            key=public_key.to_string_der(),
            receiverSignatureRequired=False,
            autoRenewPeriod=5184000,
            expirationTime=1704067200,
            memo="updated memo",
            maxAutoTokenAssociations=100,
            stakedNodeId=10,
            declineStakingReward=True,
        )
    )

    update_body = transaction._build_proto_body()

    assert update_body.accountIDToUpdate == AccountId.from_string("0.0.123")._to_proto()
    assert update_body.key == public_key.to_proto_key()
    assert update_body.receiverSigRequiredWrapper.value is False
    assert update_body.autoRenewPeriod.seconds == 5184000
    assert update_body.expirationTime.seconds == 1704067200
    assert update_body.memo.value == "updated memo"
    assert update_body.max_automatic_token_associations.value == 100
    assert update_body.staked_node_id == 10
    assert update_body.decline_reward.value is True


def test_build_update_account_transaction_uses_zero_account_when_omitted():
    transaction = _build_update_account_transaction(UpdateAccountParams(sessionId="session-1"))

    update_body = transaction._build_proto_body()

    assert update_body.accountIDToUpdate == AccountId(0, 0, 0)._to_proto()
    assert not update_body.HasField("autoRenewPeriod")


def test_update_account_handler_returns_receipt_status():
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=mock_receipt_proto,
        )
    )

    with mock_hedera_servers([[ok_response, receipt_query_response]]) as client:
        store_client("session-1", client)
        try:
            response = update_account(
                UpdateAccountParams(
                    sessionId="session-1",
                    accountId="0.0.123",
                    memo="updated memo",
                )
            )
        finally:
            remove_client("session-1")

    assert response.status == "SUCCESS"
