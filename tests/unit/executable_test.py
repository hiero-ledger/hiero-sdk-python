import pytest
import grpc
from unittest.mock import patch
from itertools import chain, repeat

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError
from hiero_sdk_python.executable import (
    _is_transaction_receipt_or_record_request,
)
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    crypto_get_account_balance_pb2,
    query_pb2,
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
from hiero_sdk_python.query.transaction_get_receipt_query import (
    TransactionGetReceiptQuery,
)
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
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
        assert transaction.node_account_ids[
            transaction._node_account_ids_index
        ] == AccountId(0, 0, 4), "Client should have switched to the second node"


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
        assert transaction.node_account_ids[
            transaction._node_account_ids_index
        ] == AccountId(0, 0, 5), "Client should have switched to the third node"
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
        assert transaction.node_account_ids[
            transaction._node_account_ids_index
        ] == AccountId(0, 0, 4), "Client should have switched to the second node"


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
        assert query._node_account_ids_index == 1
        assert query.node_account_ids[query._node_account_ids_index] == AccountId(
            0, 0, 4
        ), "Client should have switched to the second node"


# Set max_attempts
def test_set_max_attempts_with_valid_param():
    """Test that set_max_attempts for the transaction and query."""
    # Transaction
    transaction = AccountCreateTransaction()

    assert transaction._max_attempts == None
    transaction.set_max_attempts(10)
    assert transaction._max_attempts == 10

    # Query
    query = CryptoGetAccountBalanceQuery()

    assert query._max_attempts == None
    query.set_max_attempts(10)
    assert query._max_attempts == 10


@pytest.mark.parametrize("invalid_max_attempts", ["1", 0.2, True, False, object(), {}])
def test_set_max_attempts_with_invalid_type(invalid_max_attempts):
    """Test that set_max_attempts raises TypeError for non-int values."""
    with pytest.raises(
        TypeError,
        match=f"max_attempts must be of type int, got {type(invalid_max_attempts).__name__}",
    ):
        transaction = AccountCreateTransaction()
        transaction.set_max_attempts(invalid_max_attempts)

    with pytest.raises(
        TypeError,
        match=f"max_attempts must be of type int, got {type(invalid_max_attempts).__name__}",
    ):
        query = CryptoGetAccountBalanceQuery()
        query.set_max_attempts(invalid_max_attempts)


@pytest.mark.parametrize("invalid_max_attempts", [0, -10])
def test_set_max_attempts_with_invalid_value(invalid_max_attempts):
    """Test that set_max_attempts raises ValueError for non-positive values."""
    with pytest.raises(ValueError, match="max_attempts must be greater than 0"):
        transaction = AccountCreateTransaction()
        transaction.set_max_attempts(invalid_max_attempts)

    with pytest.raises(ValueError, match="max_attempts must be greater than 0"):
        query = CryptoGetAccountBalanceQuery()
        query.set_max_attempts(invalid_max_attempts)


# Set grpc_deadline
def test_set_grpc_deadline_with_valid_param():
    """Test that set_grpc_deadline updates default value of _grpc_deadline."""
    # Transaction
    transaction = AccountCreateTransaction()
    assert transaction._grpc_deadline == None

    returned = transaction.set_grpc_deadline(20)
    assert transaction._grpc_deadline == 20
    assert returned is transaction

    # Query
    query = CryptoGetAccountBalanceQuery()
    assert query._grpc_deadline == None

    returned = query.set_grpc_deadline(20)
    assert query._grpc_deadline == 20
    assert returned is query


@pytest.mark.parametrize("invalid_grpc_deadline", ["1", True, False, object(), {}])
def test_set_grpc_deadline_with_invalid_type(invalid_grpc_deadline):
    """Test that set_grpc_deadline raises TypeError for invalid types."""
    with pytest.raises(
        TypeError,
        match=f"grpc_deadline must be of type Union\\[int, float\\], got {type(invalid_grpc_deadline).__name__}",
    ):
        # Transaction
        transaction = AccountCreateTransaction()
        transaction.set_grpc_deadline(invalid_grpc_deadline)

    with pytest.raises(
        TypeError,
        match=f"grpc_deadline must be of type Union\\[int, float\\], got {type(invalid_grpc_deadline).__name__}",
    ):
        query = CryptoGetAccountBalanceQuery()
        query.set_grpc_deadline(invalid_grpc_deadline)


@pytest.mark.parametrize(
    "invalid_grpc_deadline", [0, -10, 0.0, -2.3, float("inf"), float("nan")]
)
def test_set_grpc_deadline_with_invalid_value(invalid_grpc_deadline):
    """Test that set_grpc_deadline raises ValueError for non-positive values."""
    with pytest.raises(
        ValueError, match="grpc_deadline must be a finite value greater than 0"
    ):
        # Transaction
        transaction = AccountCreateTransaction()
        transaction.set_grpc_deadline(invalid_grpc_deadline)

    with pytest.raises(
        ValueError, match="grpc_deadline must be a finite value greater than 0"
    ):
        # Query
        query = CryptoGetAccountBalanceQuery()
        query.set_grpc_deadline(invalid_grpc_deadline)


def test_warning_when_request_timeout_less_than_grpc_deadline():
    """Warn when request_timeout is less than grpc_deadline."""
    tx = AccountCreateTransaction()
    tx.set_grpc_deadline(10)

    with pytest.warns(UserWarning):
        tx.set_request_timeout(5)


# Set request_timeout
def test_set_request_timeout_with_valid_param():
    """Test that set_request_timeout updates default value of _request_timeout."""
    # Transaction
    transaction = AccountCreateTransaction()
    assert transaction._request_timeout == None

    returned = transaction.set_request_timeout(200)
    assert transaction._request_timeout == 200
    assert returned is transaction

    # Query
    query = CryptoGetAccountBalanceQuery()
    assert query._request_timeout == None

    returned = query.set_request_timeout(200)
    assert query._request_timeout == 200
    assert returned is query


@pytest.mark.parametrize("invalid_request_timeout", ["1", True, False, object(), {}])
def test_set_request_timeout_with_invalid_type(invalid_request_timeout):
    """Test that set_request_timeout raises TypeError for invalid types."""
    with pytest.raises(
        TypeError,
        match=f"request_timeout must be of type Union\\[int, float\\], got {type(invalid_request_timeout).__name__}",
    ):
        # Transaction
        transaction = AccountCreateTransaction()
        transaction.set_request_timeout(invalid_request_timeout)

    with pytest.raises(
        TypeError,
        match=f"request_timeout must be of type Union\\[int, float\\], got {type(invalid_request_timeout).__name__}",
    ):
        # Query
        query = CryptoGetAccountBalanceQuery()
        query.set_request_timeout(invalid_request_timeout)


@pytest.mark.parametrize(
    "invalid_request_timeout", [0, -10, 0.0, -2.3, float("inf"), float("nan")]
)
def test_set_request_timeout_with_invalid_value(invalid_request_timeout):
    """Test that set_request_timeout raises ValueError for non-positive values."""
    with pytest.raises(
        ValueError, match="request_timeout must be a finite value greater than 0"
    ):
        transaction = AccountCreateTransaction()
        transaction.set_request_timeout(invalid_request_timeout)

    with pytest.raises(
        ValueError, match="request_timeout must be a finite value greater than 0"
    ):
        query = CryptoGetAccountBalanceQuery()
        query.set_request_timeout(invalid_request_timeout)


def test_warning_when_grpc_deadline_exceeds_request_timeout():
    """Warn when grpc_deadline is greater than request_timeout."""
    tx = AccountCreateTransaction()

    tx.set_request_timeout(5)

    with pytest.warns(UserWarning):
        tx.set_grpc_deadline(10)


# Test is transaction_recepit_or_record
def test_is_transaction_receipt_or_record_request():
    """Detect receipt and record query requests correctly."""
    receipt_query = query_pb2.Query(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptQuery()
    )

    assert _is_transaction_receipt_or_record_request(receipt_query) is True
    assert _is_transaction_receipt_or_record_request(object()) is False


# Set min_backoff
def test_set_min_backoff_with_valid_param():
    """Test that set_min_backoff updates default value of _min_backoff."""
    # Transaction
    transaction = AccountCreateTransaction()
    assert transaction._min_backoff == None

    returned = transaction.set_min_backoff(2)
    assert transaction._min_backoff == 2
    assert returned is transaction

    # Query
    query = CryptoGetAccountBalanceQuery()
    assert query._min_backoff == None

    returned = query.set_min_backoff(2)
    assert query._min_backoff == 2
    assert returned is query


@pytest.mark.parametrize("invalid_min_backoff", ["1", True, False, object(), {}])
def test_set_min_backoff_with_invalid_type(invalid_min_backoff):
    """Test that set_min_backoff raises TypeError for invalid types."""
    with pytest.raises(
        TypeError,
        match=f"min_backoff must be of type int or float, got {type(invalid_min_backoff).__name__}",
    ):
        # Transaction
        transaction = AccountCreateTransaction()
        transaction.set_min_backoff(invalid_min_backoff)

    with pytest.raises(
        TypeError,
        match=f"min_backoff must be of type int or float, got {type(invalid_min_backoff).__name__}",
    ):
        query = CryptoGetAccountBalanceQuery()
        query.set_min_backoff(invalid_min_backoff)


@pytest.mark.parametrize(
    "invalid_min_backoff", [-1, -10, float("inf"), float("-inf"), float("nan")]
)
def test_set_min_backoff_with_invalid_value(invalid_min_backoff):
    """Test that set_min_backoff raises ValueError for invalid values."""
    with pytest.raises(ValueError, match="min_backoff must be a finite value >= 0"):
        transaction = AccountCreateTransaction()
        transaction.set_min_backoff(invalid_min_backoff)

    with pytest.raises(ValueError, match="min_backoff must be a finite value >= 0"):
        query = CryptoGetAccountBalanceQuery()
        query.set_min_backoff(invalid_min_backoff)


def test_set_min_backoff_exceeds_max_backoff():
    """Test that set_min_backoff raises ValueError if it exceeds max_backoff."""
    with pytest.raises(ValueError, match="min_backoff cannot exceed max_backoff"):
        transaction = AccountCreateTransaction()
        transaction.set_max_backoff(5)

        transaction.set_min_backoff(10)

    with pytest.raises(ValueError, match="min_backoff cannot exceed max_backoff"):
        query = CryptoGetAccountBalanceQuery()
        query.set_max_backoff(5)

        query.set_min_backoff(10)


# Set max_backoff
def test_set_max_backoff_with_valid_param():
    """Test that set_max_backoff updates default value of _max_backoff."""
    # Transaction
    transaction = AccountCreateTransaction()
    assert transaction._max_backoff == None

    returned = transaction.set_max_backoff(2)
    assert transaction._max_backoff == 2
    assert returned is transaction

    # Query
    query = CryptoGetAccountBalanceQuery()
    assert query._max_backoff == None

    returned = query.set_max_backoff(2)
    assert query._max_backoff == 2
    assert returned is query


@pytest.mark.parametrize("invalid_max_backoff", ["1", True, False, object(), {}])
def test_set_max_backoff_with_invalid_type(invalid_max_backoff):
    """Test that set_max_backoff raises TypeError for invalid types."""
    with pytest.raises(
        TypeError,
        match=f"max_backoff must be of type int or float, got {type(invalid_max_backoff).__name__}",
    ):
        transaction = AccountCreateTransaction()
        transaction.set_max_backoff(invalid_max_backoff)

    with pytest.raises(
        TypeError,
        match=f"max_backoff must be of type int or float, got {type(invalid_max_backoff).__name__}",
    ):
        query = CryptoGetAccountBalanceQuery()
        query.set_max_backoff(invalid_max_backoff)


@pytest.mark.parametrize(
    "invalid_max_backoff", [-1, -10, float("inf"), float("-inf"), float("nan")]
)
def test_set_max_backoff_with_invalid_value(invalid_max_backoff):
    """Test that set_max_backoff raises ValueError for invalid values."""
    with pytest.raises(ValueError, match="max_backoff must be a finite value >= 0"):
        transaction = AccountCreateTransaction()
        transaction.set_max_backoff(invalid_max_backoff)

    with pytest.raises(ValueError, match="max_backoff must be a finite value >= 0"):
        query = CryptoGetAccountBalanceQuery()
        query.set_max_backoff(invalid_max_backoff)


def test_set_max_backoff_less_than_min_backoff():
    """Test that set_max_backoff raises ValueError if it is less than min_backoff."""
    with pytest.raises(ValueError, match="max_backoff cannot be less than min_backoff"):
        transaction = AccountCreateTransaction()
        transaction.set_min_backoff(5)

        transaction.set_max_backoff(2)

    with pytest.raises(ValueError, match="max_backoff cannot be less than min_backoff"):
        query = CryptoGetAccountBalanceQuery()
        query.set_min_backoff(5)

        query.set_max_backoff(2)


def test_backoff_is_capped_by_max_backoff():
    """Backoff delay must not exceed max_backoff."""
    tx = AccountCreateTransaction()
    tx.set_min_backoff(2)
    tx.set_max_backoff(5)

    # attempt=0  min * 2 = 4
    assert tx._calculate_backoff(0) == 4
    # attempt=1  min * 4 = 8 : capped to 5
    assert tx._calculate_backoff(1) == 5


# Resolve config
def test_execution_config_inherits_from_client(mock_client):
    """Test that resolve_execution_config inherits config from client if not set."""
    mock_client.max_attempts = 7
    mock_client._min_backoff = 1
    mock_client._max_backoff = 8
    mock_client._grpc_deadline = 9
    mock_client._request_timeout = 20

    tx = AccountCreateTransaction()

    tx._resolve_execution_config(mock_client, None)

    assert tx._max_attempts == 7
    assert tx._min_backoff == 1
    assert tx._max_backoff == 8
    assert tx._grpc_deadline == 9
    assert tx._request_timeout == 20


def test_executable_overrides_client_config(mock_client):
    """Test the set value override the set config property."""
    mock_client.max_attempts = 10

    tx = AccountCreateTransaction().set_max_attempts(3)
    tx._resolve_execution_config(mock_client, None)

    assert tx._max_attempts == 3


def test_no_healthy_nodes_raises(mock_client):
    """Test that execution fails if no healthy nodes are available."""
    mock_client.network._healthy_nodes = []

    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate().public_key())
        .set_initial_balance(1)
    )

    with pytest.raises(RuntimeError, match="No healthy nodes available"):
        tx.execute(mock_client)


def test_set_node_account_ids_overrides_client_nodes(mock_client):
    """Explicit node_account_ids should override client network."""
    node = AccountId(0, 0, 999)

    tx = AccountCreateTransaction().set_node_account_id(node)
    tx._resolve_execution_config(mock_client, None)

    assert tx.node_account_ids == [node]


def test_parameter_timeout_overrides_client_default(mock_client):
    """Explicit timeout pass on the executable should override the client default timeout."""
    tx = AccountCreateTransaction()
    tx._resolve_execution_config(mock_client, 2)

    assert tx._request_timeout == 2


def test_set_timeout_overrides_parameter_timeout(mock_client):
    """Explicit timeout set on the tx should override the pass timeout."""
    tx = AccountCreateTransaction()
    tx.set_request_timeout(5)
    tx._resolve_execution_config(mock_client, 2)

    assert tx._request_timeout == 5


# Reuest timeout
def test_request_timeout_exceeded_stops_execution():
    """Test that execution stops when request_timeout is exceeded."""
    busy_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.BUSY
    )

    response_sequences = [[busy_response]]

    def fake_time():
        yield 0  # start
        yield 5  # attempt 1
        while True:
            yield 11  # timeout exceeded

    time_iter = fake_time()

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep"),
        patch(
            "hiero_sdk_python.executable.time.monotonic", side_effect=lambda: next(time_iter)
        ),
        patch("hiero_sdk_python.node._Node.is_healthy", return_value=True),
        patch(
            "hiero_sdk_python.executable._execute_method",
            return_value=busy_response,
        ),
    ):
        client._request_timeout = 10
        client.max_attempts = 5

        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        with pytest.raises(MaxAttemptsError):
            tx.execute(client)


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.DEADLINE_EXCEEDED, "timeout"),
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
        RealRpcError(
            grpc.StatusCode.INTERNAL, "received rst stream"
        ),  # internal with rst stream
        Exception("non grpc exception"),  # non grpc exception
    ],
)
def test_should_exponential_returns_true(error):
    """Test should exponential returns true for listed grpc error and non grpc error."""
    tx = AccountCreateTransaction()
    assert tx._should_retry_exponentially(error) is True


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.INVALID_ARGUMENT, "invalid args"),
        RealRpcError(
            grpc.StatusCode.INTERNAL, "internal"
        ),  # internal with no rst stream
    ],
)
def test_should_exponential_returns_false(error):
    """Test should exponential returns false for non-listed grpc error."""
    tx = AccountCreateTransaction()
    assert tx._should_retry_exponentially(error) is False


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.DEADLINE_EXCEEDED, "timeout"),
        RealRpcError(grpc.StatusCode.UNAVAILABLE, "unavailable"),
        RealRpcError(grpc.StatusCode.RESOURCE_EXHAUSTED, "busy"),
    ],
)
def test_should_exponential_error_mark_node_unhealty_and_advance(error):
    """Exponential gRPC retry errors advance the node without sleep-based backoff."""
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

    response_sequences = [
        [error],
        [ok_response, receipt_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep") as mock_sleep,
    ):
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        receipt = tx.execute(client)

        assert receipt.status == ResponseCode.SUCCESS
        # No delay_for_attempt backoff call, Node is mark unhealthy and advance
        assert mock_sleep.call_count == 0
        # Node must have changed
        assert tx._node_account_ids_index == 1


def test_rst_stream_error_marks_node_unhealthy_and_advances_without_backoff():
    """INTERNAL RST_STREAM errors trigger exponential retry by advancing the node without sleep-based backoff."""
    error = RealRpcError(grpc.StatusCode.INTERNAL, "received rst stream")

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

    response_sequences = [
        [error],
        [ok_response, receipt_response],
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.executable.time.sleep") as mock_sleep,
    ):
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        receipt = tx.execute(client)

        # Retry succeeds
        assert receipt.status == ResponseCode.SUCCESS
        # RST_STREAM exponential retry does not use delay-based backoff
        assert mock_sleep.call_count == 0
        # Node must advance after marking the first node unhealthy
        assert tx._node_account_ids_index == 1


@pytest.mark.parametrize(
    "error",
    [
        RealRpcError(grpc.StatusCode.ALREADY_EXISTS, "already exists"),
        RealRpcError(grpc.StatusCode.ABORTED, "aborted"),
        RealRpcError(grpc.StatusCode.UNAUTHENTICATED, "unauthenticated"),
    ],
)
def test_non_exponential_grpc_error_raises_exception(error):
    """Errors that are not retried exponentially should raise error immediately"""
    response_sequences = [[error]]

    with (
        mock_hedera_servers(response_sequences) as client,
        pytest.raises(grpc.RpcError),
    ):
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        tx.execute(client)


def test_execution_skips_unhealthy_nodes_and_advances():
    """Execution should skip unhealthy nodes and advance to the next healthy one."""
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

    response_sequences = [
        [busy_response],  # first node (unhealthy)
        [ok_response, receipt_response],  # second node (healthy)
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch(
            "hiero_sdk_python.node._Node.is_healthy",
            side_effect=chain([False, True], repeat(True)),
        ),
    ):
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        receipt = tx.execute(client)

        assert receipt.status == ResponseCode.SUCCESS
        # Ensure the node index advanced past the unhealthy node
        assert tx._node_account_ids_index == 1


def test_execution_raises_if_all_nodes_unhealthy(mock_client):
    """Execution should raise RuntimeError if all nodes are unhealthy."""
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate().public_key())
        .set_initial_balance(1)
    )

    # Patch node health to always return False
    with patch("hiero_sdk_python.node._Node.is_healthy", side_effect=repeat(False)):
        with pytest.raises(RuntimeError, match="All nodes are unhealthy"):
            tx.execute(mock_client)


@pytest.mark.parametrize(
    "tx",
    [
        TransactionRecordQuery().set_transaction_id(
            TransactionId.from_string("0.0.3@1769674705.770340600")
        ),
        TransactionGetReceiptQuery().set_transaction_id(
            TransactionId.from_string("0.0.3@1769674705.770340600")
        ),
    ],
)
def test_unhealthy_node_receipt_request_triggers_delay_and_no_node_change(
    tx, mock_client
):
    """Unhealthy node with transaction receipt/record request calls _delay_for_attempt but does not advance node."""
    initial_index = tx._node_account_ids_index

    with (
        patch("hiero_sdk_python.node._Node.is_healthy", return_value=False),
        patch("hiero_sdk_python.executable._delay_for_attempt") as mock_delay,
    ):

        with pytest.raises(Exception):
            tx.execute(mock_client)

        # _delay_for_attempt called
        assert mock_delay.call_count > 0
        # Node index did NOT change
        assert tx._node_account_ids_index == initial_index


def test_retry_invalid_node_account_updates_network():
    """
    Verify that a RETRY execution state with INVALID_NODE_ACCOUNT triggers
    node backoff, network refresh, and retry delay before succeeding.
    """
    error_response = TransactionResponseProto(
        nodeTransactionPrecheckCode=ResponseCode.INVALID_NODE_ACCOUNT
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

    response_sequences = [
        [error_response],  # first node → INVALID_NODE_ACCOUNT
        [ok_response],  # second node → success
    ]

    with (
        mock_hedera_servers(response_sequences) as client,
        patch("hiero_sdk_python.node._Node.is_healthy", return_value=True),
        patch(
            "hiero_sdk_python.client.network.Network._increase_backoff",
        ) as mock_increase_backoff,
        patch(
            "hiero_sdk_python.client.client.Client.update_network",
        ) as mock_update_network,
        patch(
            "hiero_sdk_python.executable._delay_for_attempt",
        ) as mock_delay,
        patch(
            "hiero_sdk_python.transaction.transaction_response.TransactionResponse.get_receipt",
            return_value=receipt_response,
        ),
    ):
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_initial_balance(1)
        )

        tx.execute(client)

        # Node index must advance after INVALID_NODE_ACCOUNT
        assert tx._node_account_ids_index == 1

        # Recovery actions
        mock_increase_backoff.assert_called_once()
        mock_update_network.assert_called_once()
        mock_delay.assert_called_once()
