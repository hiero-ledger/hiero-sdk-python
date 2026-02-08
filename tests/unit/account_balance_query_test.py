"""Tests for the AccountBalanceQuery functionality."""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.crypto_get_account_balance_pb2 import (
    CryptoGetAccountBalanceResponse,
)
from hiero_sdk_python.hapi.services.query_header_pb2 import ResponseType
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.contract.contract_id import ContractId

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
                cost=0,
            ),
            accountID=basic_types_pb2.AccountID(
                shardNum=0, realmNum=0, accountNum=1800
            ),
            balance=2000,
        )
    )

    response_sequences = [[balance_response]]

    # Use the context manager to set up and tear down the mock environment
    with mock_hedera_servers(response_sequences) as client:
        # Create the query and verify no exceptions are raised
        try:
            CryptoGetAccountBalanceQuery().set_account_id(
                AccountId(0, 0, 1800)
            ).execute(client)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")


def test_account_balance_query_does_not_require_payment():
    """Test that the account balance query does not require payment."""
    query = CryptoGetAccountBalanceQuery()
    assert not query._is_payment_required()


def test_set_account_id_returns_self_for_chaining():
    """set_account_id should return self to enable method chaining."""
    query = CryptoGetAccountBalanceQuery()
    account_id = AccountId(0, 0, 1800)

    result = query.set_account_id(account_id)

    assert result is query
    assert isinstance(result, CryptoGetAccountBalanceQuery)


def test_set_contract_id_returns_self_for_chaining():
    """set_contract_id should return self to enable method chaining."""
    query = CryptoGetAccountBalanceQuery()
    contract_id = ContractId(0, 0, 1234)

    result = query.set_contract_id(contract_id)

    assert result is query
    assert isinstance(result, CryptoGetAccountBalanceQuery)


def test_set_account_id_with_invalid_type_raises():
    query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"account_id must be an AccountId\."):
        query.set_account_id("ciao")


def test_set_contract_id_with_invalid_type_raises():
    query = CryptoGetAccountBalanceQuery()

    with pytest.raises(TypeError, match=r"contract_id must be a ContractId\."):
        query.set_contract_id("ciao")


def test_build_account_balance_query_with_contract_id():
    """Test building a CryptoGetAccountBalanceQuery with a valid contract ID."""
    contract_id = ContractId(0, 0, 1234)
    query = CryptoGetAccountBalanceQuery(contract_id=contract_id)
    assert query.contract_id == contract_id
    assert query.account_id is None
    assert isinstance(query.contract_id, ContractId)
    assert hasattr(query, "contract_id")


def test_set_contract_id_method_chaining_resets_account_id(mock_account_ids):
    """set_contract_id should support chaining and reset account_id."""
    account_id_sender, *_ = mock_account_ids
    contract_id = ContractId(0, 0, 1234)

    query = (
        CryptoGetAccountBalanceQuery()
        .set_account_id(account_id_sender)
        .set_contract_id(contract_id)
    )

    assert query.contract_id == contract_id
    assert query.account_id is None


def test_last_wins_when_both_account_id_and_contract_id_are_set(
    mock_account_ids,
):
    """_make_request should raise if both account_id and contract_id are set."""
    account_id_sender, *_ = mock_account_ids
    contract_id = ContractId(0, 0, 1234)

    query = CryptoGetAccountBalanceQuery(
        account_id=account_id_sender, contract_id=contract_id
    )

    assert query.contract_id == contract_id
    assert query.account_id is None


def test_make_request_raises_when_neither_account_id_nor_contract_id_is_set():
    """_make_request should raise if neither account_id nor contract_id is set."""
    query = CryptoGetAccountBalanceQuery()

    with pytest.raises(
        ValueError,
        match=r"Either account_id or contract_id must be set before making the request\.",
    ):
        query._make_request()


def test_make_request_populates_contract_id_only():
    """_make_request should populate contractID when only contract_id is set."""
    contract_id = ContractId(0, 0, 1234)
    query = CryptoGetAccountBalanceQuery().set_contract_id(contract_id)

    req = query._make_request()
    balance_query = req.cryptogetAccountBalance

    # contractID must match
    assert balance_query.contractID == contract_id._to_proto()

    # accountID should be unset
    assert not balance_query.HasField("accountID")


def test_make_request_populates_account_id_only(mock_account_ids):
    """_make_request should populate accountID when only account_id is set."""
    account_id_sender, *_ = mock_account_ids

    query = CryptoGetAccountBalanceQuery().set_account_id(account_id_sender)
    req = query._make_request()
    balance_query = req.cryptogetAccountBalance

    # accountID must match
    assert balance_query.accountID == account_id_sender._to_proto()

    # contractID should be unset
    assert not balance_query.HasField("contractID")
