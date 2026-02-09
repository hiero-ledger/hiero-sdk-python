import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
    transaction_response_pb2,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt
from hiero_sdk_python.transaction.transaction_response import TransactionResponse
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


def test_execute_waits_for_receipt_receipt():
    """Test execute return TransacationReceipt when wait_for_receipt is True (default)."""
    ok_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(
                    shardNum=0, realmNum=0, accountNum=1234
                ),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = (
            AccountCreateTransaction()
            .set_initial_balance(1)
            .set_key_without_alias(PrivateKey.generate())
        )

        # Default value of wait_for_receipt = True
        receipt = tx.execute(client, wait_for_receipt=True)

        assert isinstance(receipt, TransactionReceipt)
        assert receipt.status == ResponseCode.SUCCESS


def test_execute_without_wait_returns_transaction_response():
    """Test execute return TransacationResponse when wait_for_receipt is False."""
    ok_response = transaction_response_pb2.TransactionResponse(
        nodeTransactionPrecheckCode=ResponseCode.OK
    )

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                accountID=basic_types_pb2.AccountID(
                    shardNum=0, realmNum=0, accountNum=1234
                ),
            ),
        )
    )

    response_sequence = [[ok_response, receipt_response]]

    with mock_hedera_servers(response_sequence) as client:
        tx = (
            AccountCreateTransaction()
            .set_initial_balance(1)
            .set_key_without_alias(PrivateKey.generate())
        )

        # Default value of wait_for_receipt = True
        response = tx.execute(client, wait_for_receipt=False)

        assert isinstance(response, TransactionResponse)
        assert response.transaction is tx
        assert response.node_id == tx.node_account_id
        assert response.validate_status is True
