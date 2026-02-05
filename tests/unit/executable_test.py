import pytest
import grpc
from unittest.mock import patch

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    crypto_get_account_balance_pb2,
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
    transaction_receipt_pb2,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import RealRpcError, mock_hedera_servers

pytestmark = pytest.mark.unit


def test_retry_success_before_max_attempts():
    """Test that execution succeeds on the last attempt before max_attempts."""
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

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

    # First server gives 2 BUSY responses then OK on the 3rd try
    response_sequences = [[busy_response, busy_response, ok_response, receipt_response]]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        # Configure client to allow 3 attempts - should succeed on the last try
        client.max_attempts = 3

        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        try:
            receipt = transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )

        assert receipt.status == ResponseCode.SUCCESS


def test_retry_failure_after_max_attempts():
    """Test that execution fails after max_attempts with retriable errors."""
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )

    response_sequences = [[busy_response, busy_response]]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        client.max_attempts = 2

        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        # Should raise an exception after max attempts
        with pytest.raises(MaxAttemptsError) as excinfo:
            transaction.execute(client)

        # Verify the exception contains information about retry exhaustion
        error_message = str(excinfo.value)
        assert "Exceeded maximum attempts" in error_message
        assert "failed precheck with status: BUSY" in error_message


def test_node_switching_after_single_grpc_error():
    """Test that execution switches nodes after receiving a non-retriable error."""
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    error = RealRpcError(grpc.StatusCode.UNAVAILABLE, "Test error")

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )

    # First node gives error, second node gives OK, third node gives error
    response_sequences = [
        [error],
        [ok_response, receipt_response],
        [error],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )
        # Verify we're now on the second node
        assert client.network.current_node._account_id == AccountId(
            0, 0, 4
        ), "Client should have switched to the second node"


def test_node_switching_after_multiple_grpc_errors():
    """Test that execution switches nodes after receiving multiple non-retriable errors."""
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    error_response = RealRpcError(grpc.StatusCode.UNAVAILABLE, "Test error")

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )

    response_sequences = [
        [error_response, error_response],
        [error_response, error_response],
        [ok_response, receipt_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        try:
            receipt = transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )

        # Verify we're now on the third node
        assert client.network.current_node._account_id == AccountId(
            0, 0, 5
        ), "Client should have switched to the third node"
        assert receipt.status == ResponseCode.SUCCESS


def test_transaction_with_expired_error_not_retried():
    """Test that an expired error is not retried."""
    error_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.TRANSACTION_EXPIRED
    )
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )
    response_sequences = [[error_response]]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        with pytest.raises(PrecheckError) as exc_info:
            transaction.execute(client)

        assert str(error_response.nodeTransactionPrecheckCode) in str(exc_info.value)


def test_transaction_with_fatal_error_not_retried():
    """Test that a fatal error is not retried."""
    error_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION_BODY
    )
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )
    response_sequences = [[error_response]]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        with pytest.raises(PrecheckError) as exc_info:
            transaction.execute(client)

        assert str(error_response.nodeTransactionPrecheckCode) in str(exc_info.value)


def test_exponential_backoff_retry():
    """Test that the retry mechanism uses exponential backoff."""
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )

    # Create several BUSY responses to force multiple retries
    response_sequences = [
        [busy_response, busy_response, busy_response, ok_response, receipt_response]
    ]

    # Use a mock for time.sleep to capture the delay values
    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep") as mock_sleep,
    ):
        client.max_attempts = 5

        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )

        # Check that time.sleep was called the expected number of times (3 retries)
        assert (
            mock_sleep.call_count == 3
        ), f"Expected 3 sleep calls, got {mock_sleep.call_count}"

        # Verify exponential backoff by checking sleep durations are increasing
        sleep_args = [call_args[0][0] for call_args in mock_sleep.call_args_list]

        # Verify each subsequent delay is double than the previous
        for i in range(1, len(sleep_args)):
            assert (
                abs(sleep_args[i] - sleep_args[i - 1] * 2) < 0.1
            ), f"Expected doubling delays, but got {sleep_args}"


def test_retriable_error_does_not_switch_node():
    """Test that a retriable error does not switch nodes."""
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )
    response_sequences = [[busy_response, ok_response, receipt_response]]
    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
        )

        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )

        assert client.network.current_node._account_id == AccountId(
            0, 0, 3
        ), "Client should not switch node on retriable errors"


def test_topic_create_transaction_retry_on_busy():
    """Test that TopicCreateTransaction retries on BUSY response."""
    # First response is BUSY, second is OK
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )

    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS,
                topicID=basic_types_pb2.TopicID(shardNum=0, realmNum=0, topicNum=456),
            ),
        )
    )

    response_sequences = [
        [busy_response, ok_response, receipt_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep") as mock_sleep,
    ):
        client.max_attempts = 3

        tx = (
            TopicCreateTransaction()
            .set_memo("Test with retry")
            .set_admin_key(PrivateKey.generate().public_key())
        )

        try:
            receipt = tx.execute(client)
        except Exception as e:
            pytest.fail(f"Should not raise exception, but raised: {e}")
        # Verify transaction succeeded after retry
        assert receipt.status == ResponseCode.SUCCESS
        assert receipt.topic_id.num == 456

        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"

        # Verify we didn't switch nodes (BUSY is retriable without node switch)
        assert client.network.current_node._account_id == AccountId(
            0, 0, 3
        ), "Should not have switched nodes on BUSY"


def test_topic_create_transaction_fails_on_nonretriable_error():
    """Test that TopicCreateTransaction fails on non-retriable error."""
    # Create a response with a non-retriable error
    error_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.INVALID_TRANSACTION_BODY
    )

    response_sequences = [
        [error_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        tx = (
            TopicCreateTransaction()
            .set_memo("Test with error")
            .set_admin_key(PrivateKey.generate().public_key())
        )

        with pytest.raises(
            PrecheckError, match="failed precheck with status: INVALID_TRANSACTION_BODY"
        ):
            tx.execute(client)


def test_transaction_node_switching_body_bytes():
    """Test that execution switches nodes after receiving a non-retriable error."""
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    error = RealRpcError(grpc.StatusCode.UNAVAILABLE, "Test error")

    receipt_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=transaction_receipt_pb2.TransactionReceipt(
                status=ResponseCode.SUCCESS
            ),
        )
    )
    # First node gives error, second node gives OK, third node gives error
    response_sequences = [
        [error],
        [ok_response, receipt_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
    ):
        # We set the current node to 0
        client.network._node_index = 0
        client.network.current_node = client.network.nodes[0]

        transaction = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(100_000_000)
            .freeze_with(client)
            .sign(client.operator_private_key)
        )

        for node in client.network.nodes:
            assert (
                transaction._transaction_body_bytes.get(node._account_id) is not None
            ), "Transaction body bytes should be set for all nodes"
            sig_map = transaction._signature_map.get(
                transaction._transaction_body_bytes[node._account_id]
            )
            assert sig_map is not None, "Signature map should be set for all nodes"
            assert len(sig_map.sigPair) == 1, "Signature map should have one signature"
            assert (
                sig_map.sigPair[0].pubKeyPrefix
                == client.operator_private_key.public_key().to_bytes_raw()
            ), "Signature should be for the operator"

        try:
            transaction.execute(client)
        except (Exception, grpc.RpcError) as e:
            pytest.fail(
                f"Transaction execution should not raise an exception, but raised: {e}"
            )
        # Verify we're now on the second node
        assert client.network.current_node._account_id == AccountId(
            0, 0, 4
        ), "Client should have switched to the second node"


def test_query_retry_on_busy():
    """
    Test query retry behavior when receiving BUSY response.

    This test simulates two scenarios:
    1. First node returns BUSY response
    2. Second node returns OK response with the balance

    Verifies that the query successfully retries on a different node after receiving BUSY,
    that the balance is returned correctly and that time.sleep was called once for the retry delay.
    """
    # Create a BUSY response to simulate a node being temporarily unavailable
    # This response indicates the node cannot process the request at this time
    busy_response = response_pb2.Response(
        cryptogetAccountBalance=crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.BUSY
            )
        )
    )

    # Create a successful OK response with a balance of 1 Hbar
    # This simulates a successful account balance query response
    ok_response = response_pb2.Response(
        cryptogetAccountBalance=crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            balance=100000000,  # Balance in tinybars
        )
    )

    # Set up response sequences for multiple nodes:
    # First node returns BUSY, forcing a retry
    # Second node returns OK with the balance
    response_sequences = [
        [busy_response],
        [ok_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep") as mock_sleep,
    ):
        # We set the current node to the first node so we are sure it will return BUSY response
        client.network._node_index = 0
        client.network.current_node = client.network.nodes[0]

        query = CryptoGetAccountBalanceQuery()
        query.set_account_id(AccountId(0, 0, 1234))

        balance = query.execute(client)

        # Verify we slept once for the retry
        assert mock_sleep.call_count == 1, "Should have retried once"

        assert balance.hbars.to_tinybars() == 100000000
        # Verify we switched to the second node
        assert client.network.current_node._account_id == AccountId(
            0, 0, 4
        ), "Client should have switched to the second node"
