"""
Test cases for the AccountUpdateTransaction class.
"""

from unittest.mock import MagicMock

import pytest

# pylint: disable=no-name-in-module
from google.protobuf.wrappers_pb2 import BoolValue, StringValue

from hiero_sdk_python import Duration, Timestamp
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_update_transaction import (
    AUTO_RENEW_PERIOD,
    AccountUpdateParams,
    AccountUpdateTransaction,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services import (
    response_header_pb2,
    response_pb2,
    transaction_get_receipt_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import (
    TransactionReceipt as TransactionReceiptProto,
)
from hiero_sdk_python.hapi.services.transaction_response_pb2 import (
    TransactionResponse as TransactionResponseProto,
)
from hiero_sdk_python.response_code import ResponseCode
from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit


TEST_EXPIRATION_TIME = Timestamp(1704067200, 0)
TEST_AUTO_RENEW_PERIOD = Duration(6912000)  # ~80 days


def test_constructor_with_account_params():
    """Test creating an account update transaction with AccountUpdateParams."""
    account_id = AccountId(0, 0, 123)
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    account_memo = "Updated account memo"
    receiver_sig_required = True
    expiration_time = TEST_EXPIRATION_TIME
    auto_renew_period = TEST_AUTO_RENEW_PERIOD

    params = AccountUpdateParams(
        account_id=account_id,
        key=public_key,
        auto_renew_period=auto_renew_period,
        account_memo=account_memo,
        receiver_signature_required=receiver_sig_required,
        expiration_time=expiration_time,
    )

    account_tx = AccountUpdateTransaction(account_params=params)

    assert account_tx.account_id == account_id
    assert account_tx.key == public_key
    assert account_tx.auto_renew_period == auto_renew_period
    assert account_tx.account_memo == account_memo
    assert account_tx.receiver_signature_required == receiver_sig_required
    assert account_tx.expiration_time == expiration_time


def test_constructor_without_parameters():
    """Test creating an account update transaction without parameters."""
    account_tx = AccountUpdateTransaction()

    assert account_tx.account_id is None
    assert account_tx.key is None
    assert account_tx.auto_renew_period == AUTO_RENEW_PERIOD
    assert account_tx.account_memo is None
    assert account_tx.receiver_signature_required is None
    assert account_tx.expiration_time is None


def test_account_update_params_default_values():
    """Test that AccountUpdateParams has correct default values."""
    params = AccountUpdateParams()

    assert params.account_id is None
    assert params.key is None
    assert params.auto_renew_period == AUTO_RENEW_PERIOD
    assert params.account_memo is None
    assert params.receiver_signature_required is None
    assert params.expiration_time is None


def test_set_methods():
    """Test the set methods of AccountUpdateTransaction."""
    account_id = AccountId(0, 0, 456)
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    account_memo = "Test memo"
    receiver_sig_required = False
    expiration_time = TEST_EXPIRATION_TIME
    auto_renew_period = TEST_AUTO_RENEW_PERIOD

    account_tx = AccountUpdateTransaction()

    test_cases = [
        ("set_account_id", account_id, "account_id"),
        ("set_key", public_key, "key"),
        ("set_auto_renew_period", auto_renew_period, "auto_renew_period"),
        ("set_account_memo", account_memo, "account_memo"),
        (
            "set_receiver_signature_required",
            receiver_sig_required,
            "receiver_signature_required",
        ),
        ("set_expiration_time", expiration_time, "expiration_time"),
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(account_tx, method_name)(value)
        assert tx_after_set is account_tx
        assert getattr(account_tx, attr_name) == value


def test_set_receiver_signature_required_variations():
    """Test setting receiver signature required with different boolean values."""
    account_tx = AccountUpdateTransaction()

    # Test with True
    account_tx.set_receiver_signature_required(True)
    assert account_tx.receiver_signature_required is True

    # Test with False
    account_tx.set_receiver_signature_required(False)
    assert account_tx.receiver_signature_required is False

    # Test with None
    account_tx.set_receiver_signature_required(None)
    assert account_tx.receiver_signature_required is None


def test_set_methods_require_not_frozen(mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    account_id = AccountId(0, 0, 789)
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)  # Need account_id to freeze
    account_tx.freeze_with(mock_client)

    test_cases = [
        ("set_account_id", AccountId(0, 0, 999)),
        ("set_key", public_key),
        ("set_auto_renew_period", TEST_AUTO_RENEW_PERIOD),
        ("set_account_memo", "new memo"),
        ("set_receiver_signature_required", True),
        ("set_expiration_time", TEST_EXPIRATION_TIME),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(account_tx, method_name)(value)


def test_build_transaction_body(mock_account_ids):
    """Test building an account update transaction body with valid values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 123)

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    account_memo = "Updated memo"
    receiver_sig_required = True
    expiration_time = TEST_EXPIRATION_TIME
    auto_renew_period = TEST_AUTO_RENEW_PERIOD

    account_tx = AccountUpdateTransaction(
        AccountUpdateParams(
            account_id=account_id,
            key=public_key,
            auto_renew_period=auto_renew_period,
            account_memo=account_memo,
            receiver_signature_required=receiver_sig_required,
            expiration_time=expiration_time,
        )
    )

    # Set operator and node account IDs needed for building transaction body
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    assert (
        transaction_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    assert transaction_body.cryptoUpdateAccount.key == public_key._to_proto()
    assert (
        transaction_body.cryptoUpdateAccount.autoRenewPeriod
        == auto_renew_period._to_proto()
    )
    assert transaction_body.cryptoUpdateAccount.memo == StringValue(value=account_memo)
    assert transaction_body.cryptoUpdateAccount.receiverSigRequiredWrapper == BoolValue(
        value=receiver_sig_required
    )
    assert (
        transaction_body.cryptoUpdateAccount.expirationTime
        == expiration_time._to_protobuf()
    )


def test_build_transaction_body_with_optional_fields(mock_account_ids):
    """Test building transaction body with some optional fields set to None."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 456)

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    # Set operator and node account IDs needed for building transaction body
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    assert (
        transaction_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    # When key is None, the key field should not be set in the protobuf
    assert not transaction_body.cryptoUpdateAccount.HasField("key")
    # When account_memo is None, the memo field should not be set in the protobuf
    assert not transaction_body.cryptoUpdateAccount.HasField("memo")
    # When receiver_signature_required is None, the field should not be set
    assert not transaction_body.cryptoUpdateAccount.HasField(
        "receiverSigRequiredWrapper"
    )
    # When expiration_time is None, the expirationTime field should not be set
    assert not transaction_body.cryptoUpdateAccount.HasField("expirationTime")
    # auto_renew_period should still be set to default value
    assert (
        transaction_body.cryptoUpdateAccount.autoRenewPeriod
        == AUTO_RENEW_PERIOD._to_proto()
    )


def test_build_transaction_body_account_memo_variants(mock_account_ids):
    """Test account_memo field variants in transaction body."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 456)

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    # Set operator and node account IDs needed for building transaction body
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    # When account_memo is None, the memo field should not be set in the protobuf
    assert not transaction_body.cryptoUpdateAccount.HasField("memo")

    account_tx.set_account_memo("Test memo")
    transaction_body = account_tx.build_transaction_body()
    # When account_memo is set to a non-empty string, the memo field should be set in the protobuf
    assert transaction_body.cryptoUpdateAccount.HasField("memo")
    assert transaction_body.cryptoUpdateAccount.memo == StringValue(value="Test memo")

    account_tx.set_account_memo("")
    transaction_body = account_tx.build_transaction_body()
    # When account_memo is set to an empty string, the memo field should be set in the protobuf
    assert transaction_body.cryptoUpdateAccount.HasField("memo")
    assert transaction_body.cryptoUpdateAccount.memo == StringValue(value="")


def test_build_transaction_body_receiver_sig_required_variants(mock_account_ids):
    """Test receiver_signature_required field variants in transaction body."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 456)

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    # Set operator and node account IDs needed for building transaction body
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    # When receiver_signature_required is None, the field should not be set
    assert not transaction_body.cryptoUpdateAccount.HasField(
        "receiverSigRequiredWrapper"
    )

    account_tx.set_receiver_signature_required(True)
    transaction_body = account_tx.build_transaction_body()
    # When receiver_signature_required is set to True, the field should be set in the protobuf
    assert transaction_body.cryptoUpdateAccount.HasField("receiverSigRequiredWrapper")
    assert transaction_body.cryptoUpdateAccount.receiverSigRequiredWrapper == BoolValue(
        value=True
    )

    account_tx.set_receiver_signature_required(False)
    transaction_body = account_tx.build_transaction_body()
    # When receiver_signature_required is set to False, the field should be set in the protobuf
    assert transaction_body.cryptoUpdateAccount.HasField("receiverSigRequiredWrapper")
    assert transaction_body.cryptoUpdateAccount.receiverSigRequiredWrapper == BoolValue(
        value=False
    )


def test_missing_account_id():
    """Test that building a transaction without setting account_id raises a ValueError."""
    account_tx = AccountUpdateTransaction()

    with pytest.raises(ValueError, match="Missing required AccountID to update"):
        account_tx.build_transaction_body()


def test_sign_transaction(mock_client):
    """Test signing the account update transaction with a private key."""
    account_id = AccountId(0, 0, 123)
    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    account_tx.freeze_with(mock_client)

    account_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = account_tx._transaction_body_bytes[node_id]

    assert len(account_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = account_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client):
    """Test converting the account update transaction to protobuf format after signing."""
    account_id = AccountId(0, 0, 456)
    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    account_tx.freeze_with(mock_client)

    account_tx.sign(private_key)
    proto = account_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_account_update_transaction_can_execute():
    """Test that an account update transaction can be executed successfully."""
    account_id = AccountId(0, 0, 789)

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for successful account update
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        private_key = PrivateKey.generate()
        public_key = private_key.public_key()

        transaction = (
            AccountUpdateTransaction()
            .set_account_id(account_id)
            .set_key(public_key)
            .set_account_memo("Updated memo")
            .set_receiver_signature_required(True)
        )

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    account_tx = AccountUpdateTransaction()

    mock_channel = MagicMock()
    mock_crypto_stub = MagicMock()
    mock_channel.crypto = mock_crypto_stub

    method = account_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_crypto_stub.updateAccount


def test_constructor_with_partial_account_params():
    """Test creating transaction with partially filled AccountUpdateParams."""
    account_id = AccountId(0, 0, 111)
    account_memo = "Partial memo"

    params = AccountUpdateParams(
        account_id=account_id,
        account_memo=account_memo,
        # Other fields left as defaults
    )

    account_tx = AccountUpdateTransaction(account_params=params)

    assert account_tx.account_id == account_id
    assert account_tx.account_memo == account_memo
    assert account_tx.key is None
    assert account_tx.auto_renew_period == AUTO_RENEW_PERIOD
    assert account_tx.receiver_signature_required is None
    assert account_tx.expiration_time is None


def test_build_transaction_body_with_none_auto_renew_period(mock_account_ids):
    """Test building transaction body when auto_renew_period is explicitly set to None."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 333)

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)
    account_tx.set_auto_renew_period(None)
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    assert (
        transaction_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    # When auto_renew_period is None, the field should not be set in the protobuf
    assert not transaction_body.cryptoUpdateAccount.HasField("autoRenewPeriod")

def test_build_scheduled_body(mock_account_ids):
    """Test building a schedulable account update transaction body with valid values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 123)

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    account_memo = "Scheduled memo"
    receiver_sig_required = True
    expiration_time = TEST_EXPIRATION_TIME
    auto_renew_period = TEST_AUTO_RENEW_PERIOD

    account_tx = AccountUpdateTransaction(
        AccountUpdateParams(
            account_id=account_id,
            key=public_key,
            auto_renew_period=auto_renew_period,
            account_memo=account_memo,
            receiver_signature_required=receiver_sig_required,
            expiration_time=expiration_time,
        )
    )

    # Set operator and node account IDs needed for building transaction body
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    # Build the scheduled body
    schedulable_body = account_tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify the transaction was built with account update type
    assert schedulable_body.HasField("cryptoUpdateAccount")

    assert (
        schedulable_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    assert schedulable_body.cryptoUpdateAccount.key == public_key._to_proto()
    assert (
        schedulable_body.cryptoUpdateAccount.autoRenewPeriod
        == auto_renew_period._to_proto()
    )
    assert schedulable_body.cryptoUpdateAccount.memo == StringValue(value=account_memo)
    assert schedulable_body.cryptoUpdateAccount.receiverSigRequiredWrapper == BoolValue(
        value=receiver_sig_required
    )
    assert (
        schedulable_body.cryptoUpdateAccount.expirationTime
        == expiration_time._to_protobuf()
    )
