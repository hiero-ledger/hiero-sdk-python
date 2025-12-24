"""Tests for the AccountBalanceQuery functionality."""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import basic_types_pb2, response_header_pb2, response_pb2
from hiero_sdk_python.hapi.services.crypto_get_account_balance_pb2 import CryptoGetAccountBalanceResponse
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

# This test uses fixture mock_account_ids as parameter
def test_build_account_balance_query(mock_account_ids):
    """Test building a CryptoGetAccountBalanceQuery with a valid account ID."""
    account_id_sender, *_ = mock_account_ids
    query = CryptoGetAccountBalanceQuery(account_id=account_id_sender)
    assert query.account_id == account_id_sender


def test_execute_account_balance_query():
    """Test executing the CryptoGetAccountBalanceQuery with a mocked client."""
    balance_response = response_pb2.Response(
        cryptogetAccountBalance=CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK,
                responseType=ResponseType.ANSWER_ONLY,
                cost=0
            ),
            accountID=basic_types_pb2.AccountID(
                shardNum=0,
                realmNum=0,
                accountNum=1800
            ),
            balance=2000
        )
    )

    response_sequences = [[balance_response]]
    
    # Use the context manager to set up and tear down the mock environment
    with mock_hedera_servers(response_sequences) as client:
        # Create the query and verify no exceptions are raised
        try:
            CryptoGetAccountBalanceQuery().set_account_id(AccountId(0, 0, 1800)).execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")

def test_account_balance_query_does_not_require_payment():
    """Test that the account balance query does not require payment."""
    query = CryptoGetAccountBalanceQuery()
    assert not query._is_payment_required()