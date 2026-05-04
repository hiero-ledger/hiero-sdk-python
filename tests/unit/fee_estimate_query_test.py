"""Tests for FeeEstimateQuery."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.fee_estimate_query import FeeEstimateQuery
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit


def mock_client():
    client = MagicMock()
    client.mirror_network = "https://testnet.mirrornode.hedera.com"
    client.max_retries = 3

    client.generate_transaction_id.return_value = TransactionId.generate(AccountId(0, 0, 1001))
    client.operator_account_id._to_proto.return_value = AccountId(0, 0, 1)._to_proto()

    node = MagicMock()
    node._account_id = AccountId(0, 0, 3)

    client.network = MagicMock()
    client.network.nodes = [node]

    return client


def mock_fee_response():
    return {
        "high_volume_multiplier": 1,
        "network": {"multiplier": 9, "subtotal": 1},
        "node": {"base": 10, "extras": []},
        "service": {"base": 20, "extras": []},
        "total": 210,
    }


def mock_requests_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = mock_fee_response()
    return response


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_transfer_transaction_state_mode(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()
    tx.add_hbar_transfer(AccountId.from_string("0.0.1001"), Hbar(-1))
    tx.add_hbar_transfer(AccountId.from_string("0.0.1002"), Hbar(1))

    result = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx).execute(mock_client())

    assert result.mode == FeeEstimateMode.STATE
    assert result.total > 0


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_transfer_transaction_intrinsic_mode(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()
    tx.add_hbar_transfer(AccountId.from_string("0.0.1001"), Hbar(-1))
    tx.add_hbar_transfer(AccountId.from_string("0.0.1002"), Hbar(1))

    result = FeeEstimateQuery().set_mode(FeeEstimateMode.INTRINSIC).set_transaction(tx).execute(mock_client())

    assert result.mode == FeeEstimateMode.INTRINSIC


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_default_mode_is_intrinsic(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.mode == FeeEstimateMode.INTRINSIC


def test_transaction_required():
    query = FeeEstimateQuery()

    with pytest.raises(ValueError):
        query.execute(mock_client())


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_token_create_transaction(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TokenCreateTransaction().set_token_name("Test Token").set_token_symbol("TK").set_initial_supply(1)

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_token_mint_transaction(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TokenMintTransaction().set_token_id(TokenId(0, 0, 2)).set_amount(20)

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_create_transaction(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = TopicCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_contract_create_transaction(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = ContractCreateTransaction().set_bytecode_file_id(FileId(0, 0, 1)).set_gas(10)

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_file_create_transaction(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = FileCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0


# ---------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_invalid_argument_error(mock_post):
    response = MagicMock()
    response.status_code = 400

    mock_post.return_value = response

    tx = TransferTransaction()

    with pytest.raises(RuntimeError):
        FeeEstimateQuery().set_transaction(tx).execute(mock_client())


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_retry_on_timeout(mock_post):
    mock_post.side_effect = [
        requests.Timeout(),
        mock_requests_response(),
    ]

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0
    assert mock_post.call_count == 2


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_retry_on_503(mock_post):
    error_response = MagicMock()
    error_response.status_code = 503

    mock_post.side_effect = [
        error_response,
        mock_requests_response(),
    ]

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0
    assert mock_post.call_count == 2


# ---------------------------------------------------------------------
# Chunked transactions
# ---------------------------------------------------------------------


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_message_single_chunk(mock_post):
    mock_post.return_value = mock_requests_response()

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId(0, 0, 4))
        .set_transaction_id(TransactionId.generate(AccountId(0, 0, 3)))
        .set_node_account_id(AccountId(0, 0, 4))
    )
    tx.set_message("hello")

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result.total > 0
    assert mock_post.call_count == 1


@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_message_multiple_chunks(mock_post):
    mock_post.side_effect = [
        mock_requests_response(),
        mock_requests_response(),
    ]

    tx = (
        TopicMessageSubmitTransaction()
        .set_topic_id(TopicId(0, 0, 4))
        .set_transaction_id(TransactionId.generate(AccountId(0, 0, 3)))
        .set_node_account_id(AccountId(0, 0, 4))
    )
    tx.set_message("A" * 2048)  # force chunking

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    # aggregated expectations
    # 'network': {'multiplier': 9, 'subtotal': 1 * 2},
    # 'node': {'base': 10 * 2, 'extras': []},
    # 'service': {'base': 20 * 2, 'extras': []},
    # 'total':  210 * 2

    assert mock_post.call_count == 2
    assert result.node_fee.base == 10 * 2
    assert result.service_fee.base == 20 * 2
    assert result.network_fee.subtotal == 1 * 2
    assert result.total == 210 * 2


# ---------------------------------------------------------------------
# Configuration / validation coverage
# ---------------------------------------------------------------------


def test_high_volume_throttle_validation():
    q = FeeEstimateQuery()

    with pytest.raises(TypeError):
        q.set_high_volume_throttle("100")

    with pytest.raises(ValueError):
        q.set_high_volume_throttle(-1)

    with pytest.raises(ValueError):
        q.set_high_volume_throttle(10001)

    # valid case
    q.set_high_volume_throttle(5000)
    assert q.get_high_volume_throttle() == 5000


def test_max_attempts_validation():
    q = FeeEstimateQuery()

    with pytest.raises(TypeError):
        q.set_max_attempts("3")

    with pytest.raises(ValueError):
        q.set_max_attempts(0)

    # valid case
    q.set_max_attempts(2)
    assert q._max_attempts == 2


def test_max_backoff_validation():
    q = FeeEstimateQuery()

    with pytest.raises(TypeError):
        q.set_max_backoff("fast")

    with pytest.raises(ValueError):
        q.set_max_backoff(0)

    # valid case
    q.set_max_backoff(1.5)
    assert q._max_backoff == 1.5


def test_getters_and_defaults():
    q = FeeEstimateQuery()

    assert q.get_mode() is None
    assert q.get_transaction() is None
    assert q.get_high_volume_throttle() == 0


def test_setters_are_chainable():
    q = FeeEstimateQuery()

    result = q.set_max_attempts(2).set_max_backoff(1.0).set_high_volume_throttle(100)

    assert result is q
