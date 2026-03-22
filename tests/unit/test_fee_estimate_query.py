"""Tests for FeeEstimateQuery."""

import pytest
from unittest.mock import patch, MagicMock

from hiero_sdk_python.query.fee_estimate_query import FeeEstimateQuery
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode

from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction

from hiero_sdk_python.hbar import Hbar

pytestmark = pytest.mark.unit

def mock_client():
    client = MagicMock()
    client.mirror_network = "https://testnet.mirrornode.hedera.com"
    client.max_retries = 3
    return client


def mock_fee_response():
    return {
        "mode": "STATE",
        "node": {"subtotal": 10},
        "service": {"subtotal": 20},
        "network": {"multiplier": 2},
        "notes": [],
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
    tx.add_hbar_transfer("0.0.1001", Hbar(-1))
    tx.add_hbar_transfer("0.0.1002", Hbar(1))

    query = FeeEstimateQuery().set_transaction(tx)

    result = query.execute(mock_client())

    assert result.total == (
        result.node_fee.subtotal
        + result.service_fee.subtotal
        + result.network_fee.subtotal
    )

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_transfer_transaction_intrinsic_mode(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()
    tx.add_hbar_transfer("0.0.1001", Hbar(-1))
    tx.add_hbar_transfer("0.0.1002", Hbar(1))

    query = (
        FeeEstimateQuery()
        .set_transaction(tx)
        .set_mode(FeeEstimateMode.INTRINSIC)
    )

    result = query.execute(mock_client())

    assert result.mode == FeeEstimateMode.INTRINSIC

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_default_mode_is_state(mock_post):
    
    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()

    query = FeeEstimateQuery().set_transaction(tx)

    result = query.execute(mock_client())

    assert result.mode == FeeEstimateMode.STATE

def test_transaction_required():

    query = FeeEstimateQuery()

    with pytest.raises(ValueError):
        query.execute(mock_client())

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_token_create_transaction(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TokenCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_token_mint_transaction(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TokenMintTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_create_transaction(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TopicCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_contract_create_transaction(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = ContractCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_file_create_transaction(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = FileCreateTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_network_fee_formula(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    expected = result.node_fee.subtotal * result.network_fee.multiplier

    assert result.network_fee.subtotal == expected

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_total_fee_formula(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    expected = (
        result.node_fee.subtotal
        + result.service_fee.subtotal
        + result.network_fee.subtotal
    )

    assert result.total == expected

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_invalid_argument_error(mock_post):

    response = MagicMock()
    response.status_code = 400

    mock_post.return_value = response

    tx = TransferTransaction()

    query = FeeEstimateQuery().set_transaction(tx)

    with pytest.raises(ValueError):
        query.execute(mock_client())

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_retry_on_unavailable(mock_post):

    mock_post.side_effect = [
        Exception("UNAVAILABLE"),
        mock_requests_response(),
    ]

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_retry_on_timeout(mock_post):

    mock_post.side_effect = [
        Exception("DEADLINE_EXCEEDED"),
        mock_requests_response(),
    ]

    tx = TransferTransaction()

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_message_single_chunk(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TopicMessageSubmitTransaction()
    tx.set_message("hello")

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None

@patch("hiero_sdk_python.query.fee_estimate_query.requests.post")
def test_topic_message_multiple_chunks(mock_post):

    mock_post.return_value = mock_requests_response()

    tx = TopicMessageSubmitTransaction()
    tx.set_message("A" * 5000)

    result = FeeEstimateQuery().set_transaction(tx).execute(mock_client())

    assert result is not None