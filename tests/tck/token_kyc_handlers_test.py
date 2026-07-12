from __future__ import annotations

import importlib

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, transaction_get_receipt_pb2
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from tck.errors import JsonRpcError
from tck.handlers.registry import get_handler
from tck.handlers.token import (
    _build_grant_token_kyc_transaction,
    _build_revoke_token_kyc_transaction,
)
from tck.param.token import FreezeTokenParams, GrantTokenKycParams, RevokeTokenKycParams
from tck.util.client_utils import remove_client, store_client
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


ACCOUNT_ID = AccountId(0, 0, 5555)
TOKEN_ID = TokenId(0, 0, 9999)


@pytest.fixture(autouse=True)
def _ensure_handlers_registered():
    from tck.handlers import token as token_handlers

    importlib.reload(token_handlers)
    yield


def _success_response_sequence():
    """Build a single-transaction response sequence that reports SUCCESS."""
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=receipt_proto,
        )
    )
    return [[ok_response, receipt_query_response]]


class TestGrantTokenKycParamsParsing:
    def test_parses_full_valid_payload(self):
        params = GrantTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "session-1"}
        )
        assert params.tokenId == "0.0.9999"
        assert params.accountId == "0.0.5555"
        assert params.sessionId == "session-1"

    def test_missing_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            GrantTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "accountId": "0.0.5555"})

    def test_empty_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            GrantTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": ""})

    def test_missing_token_and_account_id_parse_as_none(self):
        """tokenId/accountId are optional at parse time; the TCK spec uses
        their absence to test the endpoint's own validation errors."""
        params = GrantTokenKycParams.parse_json_params({"sessionId": "session-1"})
        assert params.tokenId is None
        assert params.accountId is None


class TestRevokeTokenKycParamsParsing:
    def test_parses_full_valid_payload(self):
        params = RevokeTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "session-1"}
        )
        assert params.tokenId == "0.0.9999"
        assert params.accountId == "0.0.5555"
        assert params.sessionId == "session-1"

    def test_missing_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            RevokeTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "accountId": "0.0.5555"})

    def test_empty_session_id_raises(self):
        with pytest.raises(ValueError, match="sessionId"):
            RevokeTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": ""})

    def test_missing_token_and_account_id_parse_as_none(self):
        """tokenId/accountId are optional at parse time; the TCK spec uses
        their absence to test the endpoint's own validation errors."""
        params = RevokeTokenKycParams.parse_json_params({"sessionId": "session-1"})
        assert params.tokenId is None
        assert params.accountId is None


class TestBuildGrantTokenKycTransaction:
    def test_sets_both_fields_when_present(self):
        params = GrantTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "s"}
        )
        tx = _build_grant_token_kyc_transaction(params)
        assert tx.token_id == TOKEN_ID
        assert tx.account_id == ACCOUNT_ID

    def test_leaves_account_id_none_when_absent(self):
        params = GrantTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "sessionId": "s"})
        tx = _build_grant_token_kyc_transaction(params)
        assert tx.token_id == TOKEN_ID
        assert tx.account_id is None

    def test_missing_account_id_fails_at_proto_build_not_silently(self):
        """Partial params build an executable-looking transaction object,
        but the SDK's own validation must still catch the missing field
        before anything reaches the network."""
        params = GrantTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "sessionId": "s"})
        tx = _build_grant_token_kyc_transaction(params)
        with pytest.raises(ValueError, match="Missing account ID"):
            tx._build_proto_body()

    def test_leaves_token_id_none_when_absent(self):
        params = GrantTokenKycParams.parse_json_params({"accountId": "0.0.5555", "sessionId": "s"})
        tx = _build_grant_token_kyc_transaction(params)
        assert tx.token_id is None
        assert tx.account_id == ACCOUNT_ID

    def test_missing_token_id_fails_at_proto_build_not_silently(self):
        params = GrantTokenKycParams.parse_json_params({"accountId": "0.0.5555", "sessionId": "s"})
        tx = _build_grant_token_kyc_transaction(params)
        with pytest.raises(ValueError, match="Missing token ID"):
            tx._build_proto_body()


class TestBuildRevokeTokenKycTransaction:
    def test_sets_both_fields_when_present(self):
        params = RevokeTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "s"}
        )
        tx = _build_revoke_token_kyc_transaction(params)
        assert tx.token_id == TOKEN_ID
        assert tx.account_id == ACCOUNT_ID

    def test_missing_token_id_fails_at_proto_build_not_silently(self):
        params = RevokeTokenKycParams.parse_json_params({"accountId": "0.0.5555", "sessionId": "s"})
        tx = _build_revoke_token_kyc_transaction(params)
        with pytest.raises(ValueError, match="Missing token ID"):
            tx._build_proto_body()

    def test_leaves_account_id_none_when_absent(self):
        params = RevokeTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "sessionId": "s"})
        tx = _build_revoke_token_kyc_transaction(params)
        assert tx.token_id == TOKEN_ID
        assert tx.account_id is None

    def test_missing_account_id_fails_at_proto_build_not_silently(self):
        params = RevokeTokenKycParams.parse_json_params({"tokenId": "0.0.9999", "sessionId": "s"})
        tx = _build_revoke_token_kyc_transaction(params)
        with pytest.raises(ValueError, match="Missing account ID"):
            tx._build_proto_body()


class TestEndToEndDispatch:
    def test_grant_token_kyc_success(self):
        session_id = "e2e-grant-session"
        with mock_hedera_servers(_success_response_sequence()) as client:
            store_client(session_id, client)
            try:
                handler = get_handler("grantTokenKyc")
                params = GrantTokenKycParams.parse_json_params(
                    {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": session_id}
                )
                response = handler(params)
                assert response.status == "SUCCESS"
            finally:
                remove_client(session_id)

    def test_revoke_token_kyc_success(self):
        session_id = "e2e-revoke-session"
        with mock_hedera_servers(_success_response_sequence()) as client:
            store_client(session_id, client)
            try:
                handler = get_handler("revokeTokenKyc")
                params = RevokeTokenKycParams.parse_json_params(
                    {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": session_id}
                )
                response = handler(params)
                assert response.status == "SUCCESS"
            finally:
                remove_client(session_id)


class TestErrorHandlingRobustness:
    def test_unknown_session_id_does_not_leak_raw_exception(self):
        handler = get_handler("revokeTokenKyc")
        params = RevokeTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "never-registered"}
        )
        with pytest.raises(JsonRpcError) as exc_info:
            handler(params)
        assert exc_info.value.code == JsonRpcError.internal_error().code
        assert exc_info.value.message == "Internal error"
        assert exc_info.value.data is None

    def test_unknown_session_id_same_behavior_as_freeze_token_control(self):
        handler = get_handler("freezeToken")
        params = FreezeTokenParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": "0.0.5555", "sessionId": "never-registered"}
        )
        with pytest.raises(JsonRpcError) as exc_info:
            handler(params)
        assert exc_info.value.code == JsonRpcError.internal_error().code
        assert exc_info.value.message == "Internal error"

    def test_wrong_type_token_id_does_not_leak_raw_exception(self):
        handler = get_handler("revokeTokenKyc")
        params = RevokeTokenKycParams.parse_json_params(
            {"tokenId": 9999, "accountId": "0.0.5555", "sessionId": "irrelevant"}
        )
        with pytest.raises(JsonRpcError) as exc_info:
            handler(params)
        assert exc_info.value.code == JsonRpcError.internal_error().code
        assert exc_info.value.message == "Internal error"
        assert exc_info.value.data is None

    def test_wrong_type_account_id_does_not_leak_raw_exception(self):
        handler = get_handler("grantTokenKyc")
        params = GrantTokenKycParams.parse_json_params(
            {"tokenId": "0.0.9999", "accountId": ["not", "a", "string"], "sessionId": "irrelevant"}
        )
        with pytest.raises(JsonRpcError) as exc_info:
            handler(params)
        assert exc_info.value.code == JsonRpcError.internal_error().code
        assert exc_info.value.message == "Internal error"
