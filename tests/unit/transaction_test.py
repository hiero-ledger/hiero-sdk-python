from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import ReceiptStatusError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def test_execute_waits_for_receipt_receipt():
    """Test execute return TransactionReceipt when wait_for_receipt is True (default)."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Default value of wait_for_receipt = True
        receipt = tx.execute(client, wait_for_receipt=True)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.SUCCESS


def test_execute_without_wait_returns_transaction_response():
    """Test execute return TransactionResponse when wait_for_receipt is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(shardNum=0, realmNum=0, accountNum=1234),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        # Explicitly pass wait_for_receipt=False to get TransactionResponse
        response = tx.execute(client, wait_for_receipt=False)

        assert isinstance(response, TransactionResponse)
        assert response.transaction is tx
        assert response.node_id == tx.node_account_id
        assert response.validate_status is True


def test_execute_raises_error_when_validation_enabled_and_transaction_fails():
    """Test execute raises error for failing transactions when validate_status is True."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        with pytest.raises(ReceiptStatusError) as e:
            tx.execute(client, validate_status=True)

        assert e.value.status == ResponseCode.INVALID_SIGNATURE


def test_execute_returns_receipt_without_error_when_validation_disabled():
    """Test execute returns a receipt normally on failure when validate_status is False."""
    ok_response = transaction_response_pb2.TransactionResponse(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=transaction_receipt_pb2.TransactionReceipt(status=ResponseCode.INVALID_SIGNATURE),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = AccountCreateTransaction().set_initial_balance(1).set_key_without_alias(PrivateKey.generate())

        receipt = tx.execute(client)

        assert receipt.status == ResponseCode.INVALID_SIGNATURE


def test_duplicate_signature_not_added():
    tx = TokenMintTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))
    tx.set_token_id(TokenId(0, 0, 1))
    tx.set_amount(100)
    key = PrivateKey.generate_ed25519()
    tx.freeze()
    tx.sign(key)
    tx.sign(key)
    assert tx._signature_map, "signature_map should not be empty after freeze+sign"  # ← ADD HERE
    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair
    assert len(sig_pairs) == 1, "Expected 1 signature for duplicate key"


def test_multiple_keys_still_work():
    tx = TokenMintTransaction()
    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))
    tx.set_token_id(TokenId(0, 0, 1))
    tx.set_amount(100)
    key1 = PrivateKey.generate_ed25519()
    key2 = PrivateKey.generate_ed25519()
    tx.freeze()
    tx.sign(key1)
    tx.sign(key2)
    assert tx._signature_map, "signature_map should not be empty after freeze+sign"
    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair
    assert len(sig_pairs) == 2, "Expected 2 signatures for different keys"
    pubkey_prefixes = {sp.pubKeyPrefix for sp in sig_pairs}
    expected_prefixes = {
        key1.public_key().to_bytes_raw(),
        key2.public_key().to_bytes_raw(),
    }
    assert pubkey_prefixes == expected_prefixes, "Signatures should match key1 and key2 exactly"
