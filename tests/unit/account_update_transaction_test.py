"""
Test cases for the AccountUpdateTransaction class.
"""

from unittest.mock import MagicMock

import pytest

# pylint: disable=no-name-in-module
from google.protobuf.wrappers_pb2 import BoolValue, Int32Value, StringValue

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
    max_associations = 50
    staked_account_id = AccountId(0, 0, 999)
    decline_reward = False

    params = AccountUpdateParams(
        account_id=account_id,
        key=public_key,
        auto_renew_period=auto_renew_period,
        account_memo=account_memo,
        receiver_signature_required=receiver_sig_required,
        expiration_time=expiration_time,
        max_automatic_token_associations=max_associations,
        staked_account_id=staked_account_id,
        decline_staking_reward=decline_reward,
    )

    account_tx = AccountUpdateTransaction(account_params=params)

    assert account_tx.account_id == account_id
    assert account_tx.key == public_key
    assert account_tx.auto_renew_period == auto_renew_period
    assert account_tx.account_memo == account_memo
    assert account_tx.receiver_signature_required == receiver_sig_required
    assert account_tx.expiration_time == expiration_time
    assert account_tx.max_automatic_token_associations == max_associations
    assert account_tx.staked_account_id == staked_account_id
    assert (
        account_tx.staked_node_id is None
    )  # Should be cleared when staked_account_id is set
    assert account_tx.decline_staking_reward == decline_reward


def test_constructor_without_parameters():
    """Test creating an account update transaction without parameters."""
    account_tx = AccountUpdateTransaction()

    assert account_tx.account_id is None
    assert account_tx.key is None
    assert account_tx.auto_renew_period == AUTO_RENEW_PERIOD
    assert account_tx.account_memo is None
    assert account_tx.receiver_signature_required is None
    assert account_tx.expiration_time is None
    assert account_tx.max_automatic_token_associations is None
    assert account_tx.staked_account_id is None
    assert account_tx.staked_node_id is None
    assert account_tx.decline_staking_reward is None


def test_account_update_params_default_values():
    """Test that AccountUpdateParams has correct default values."""
    params = AccountUpdateParams()

    assert params.account_id is None
    assert params.key is None
    assert params.auto_renew_period == AUTO_RENEW_PERIOD
    assert params.account_memo is None
    assert params.receiver_signature_required is None
    assert params.expiration_time is None
    assert params.max_automatic_token_associations is None
    assert params.staked_account_id is None
    assert params.staked_node_id is None
    assert params.decline_staking_reward is None


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
        (
            "set_max_automatic_token_associations",
            100,
            "max_automatic_token_associations",
        ),
        ("set_decline_staking_reward", True, "decline_staking_reward"),
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
        ("set_max_automatic_token_associations", 100),
        ("set_staked_account_id", AccountId(0, 0, 888)),
        ("set_staked_node_id", 5),
        ("set_decline_staking_reward", True),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(account_tx, method_name)(value)

    zero_arg_methods = [
        "clear_staked_account_id",
        "clear_staked_node_id",
    ]

    for method_name in zero_arg_methods:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(account_tx, method_name)()


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
    assert account_tx.max_automatic_token_associations is None
    assert account_tx.staked_account_id is None
    assert account_tx.staked_node_id is None
    assert account_tx.decline_staking_reward is None


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


def test_constructor_with_new_fields():
    """Test creating an account update transaction with new fields in params."""
    account_id = AccountId(0, 0, 123)
    staked_account_id = AccountId(0, 0, 456)
    max_associations = 100

    params = AccountUpdateParams(
        account_id=account_id,
        max_automatic_token_associations=max_associations,
        staked_account_id=staked_account_id,
        decline_staking_reward=True,
    )

    account_tx = AccountUpdateTransaction(account_params=params)

    assert account_tx.account_id == account_id
    assert account_tx.max_automatic_token_associations == max_associations
    assert account_tx.staked_account_id == staked_account_id
    assert (
        account_tx.staked_node_id is None
    )  # Should be cleared when staked_account_id is set
    assert account_tx.decline_staking_reward is True


def test_set_max_automatic_token_associations():
    """Test setting max automatic token associations."""
    account_tx = AccountUpdateTransaction()
    max_associations = 100
    result = account_tx.set_max_automatic_token_associations(max_associations)

    assert account_tx.max_automatic_token_associations == max_associations
    assert result is account_tx  # Method chaining


def test_set_max_automatic_token_associations_validation():
    """Test validation for max_automatic_token_associations."""
    account_tx = AccountUpdateTransaction()

    # Test good value: -1 for unlimited
    account_tx.set_max_automatic_token_associations(-1)
    assert account_tx.max_automatic_token_associations == -1

    # Test good value: 0 for default
    account_tx.set_max_automatic_token_associations(0)
    assert account_tx.max_automatic_token_associations == 0

    # Test good value: 100
    account_tx.set_max_automatic_token_associations(100)
    assert account_tx.max_automatic_token_associations == 100

    # Test None (should be allowed)
    account_tx.set_max_automatic_token_associations(None)
    assert account_tx.max_automatic_token_associations is None

    # Test bad value: -2
    with pytest.raises(ValueError) as e:
        account_tx.set_max_automatic_token_associations(-2)

    assert "must be -1 (unlimited) or a non-negative integer" in str(e.value)


def test_set_staked_account_id():
    """Test setting staked account ID."""
    account_tx = AccountUpdateTransaction()
    staked_account_id = AccountId(0, 0, 789)
    result = account_tx.set_staked_account_id(staked_account_id)

    assert account_tx.staked_account_id == staked_account_id
    assert account_tx.staked_node_id is None  # Should clear the other field
    assert result is account_tx  # Method chaining

    # Passing None should clear and set sentinel 0.0.0
    account_tx.set_staked_account_id(None)
    assert account_tx.staked_account_id == AccountId(0, 0, 0)
    assert account_tx.staked_node_id is None


def test_set_staked_node_id():
    """Test setting staked node ID."""
    account_tx = AccountUpdateTransaction()
    staked_node_id = 5
    result = account_tx.set_staked_node_id(staked_node_id)

    assert account_tx.staked_node_id == staked_node_id
    assert account_tx.staked_account_id is None  # Should clear the other field
    assert result is account_tx  # Method chaining

    # Passing None should clear and set sentinel -1
    account_tx.set_staked_node_id(None)
    assert account_tx.staked_node_id == -1
    assert account_tx.staked_account_id is None


def test_staked_id_oneof_behavior():
    """Test that staked_account_id and staked_node_id are mutually exclusive."""
    account_tx = AccountUpdateTransaction()
    staked_account_id = AccountId(0, 0, 789)
    staked_node_id = 5

    # Set staked_account_id first
    account_tx.set_staked_account_id(staked_account_id)
    assert account_tx.staked_account_id == staked_account_id
    assert account_tx.staked_node_id is None

    # Setting staked_node_id should clear staked_account_id
    account_tx.set_staked_node_id(staked_node_id)
    assert account_tx.staked_node_id == staked_node_id
    assert account_tx.staked_account_id is None

    # Setting staked_account_id again should clear staked_node_id
    account_tx.set_staked_account_id(staked_account_id)
    assert account_tx.staked_account_id == staked_account_id
    assert account_tx.staked_node_id is None

    # Clearing should set sentinel values
    account_tx.clear_staked_account_id()
    assert account_tx.staked_account_id == AccountId(0, 0, 0)
    assert account_tx.staked_node_id is None

    account_tx.clear_staked_node_id()
    assert account_tx.staked_node_id == -1
    assert account_tx.staked_account_id is None


def test_set_decline_staking_reward():
    """Test setting decline staking reward."""
    account_tx = AccountUpdateTransaction()

    # Test with True
    result = account_tx.set_decline_staking_reward(True)
    assert account_tx.decline_staking_reward is True
    assert result is account_tx

    # Test with False
    account_tx.set_decline_staking_reward(False)
    assert account_tx.decline_staking_reward is False

    # Test with None
    account_tx.set_decline_staking_reward(None)
    assert account_tx.decline_staking_reward is None


def test_clear_staked_account_id():
    """Test clearing the staked account id using sentinel value."""
    account_tx = AccountUpdateTransaction()
    account_tx.set_staked_node_id(5)
    account_tx.clear_staked_account_id()

    assert account_tx.staked_account_id == AccountId(0, 0, 0)
    assert account_tx.staked_node_id is None


def test_clear_staked_node_id():
    """Test clearing the staked node id using sentinel value (-1)."""
    account_tx = AccountUpdateTransaction()
    account_tx.set_staked_account_id(AccountId(0, 0, 123))
    account_tx.clear_staked_node_id()

    assert account_tx.staked_node_id == -1
    assert account_tx.staked_account_id is None


def test_build_transaction_body_with_new_fields(mock_account_ids):
    """Test building transaction body with new fields."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 123)
    staked_account_id = AccountId(0, 0, 456)
    max_associations = 100

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)
    account_tx.set_max_automatic_token_associations(max_associations)
    account_tx.set_staked_account_id(staked_account_id)
    account_tx.set_decline_staking_reward(True)

    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    assert (
        transaction_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    assert (
        transaction_body.cryptoUpdateAccount.max_automatic_token_associations
        == Int32Value(value=max_associations)
    )
    assert (
        transaction_body.cryptoUpdateAccount.staked_account_id.accountNum
        == staked_account_id.num
    )
    assert transaction_body.cryptoUpdateAccount.decline_reward == BoolValue(value=True)


def test_build_transaction_body_with_staked_node_id(mock_account_ids):
    """Test building transaction body with staked_node_id."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 123)
    staked_node_id = 5

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)
    account_tx.set_staked_node_id(staked_node_id)

    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    assert (
        transaction_body.cryptoUpdateAccount.accountIDToUpdate == account_id._to_proto()
    )
    assert transaction_body.cryptoUpdateAccount.staked_node_id == staked_node_id
    # staked_account_id should not be set
    assert not transaction_body.cryptoUpdateAccount.HasField("staked_account_id")


def test_build_transaction_body_with_optional_new_fields_none(mock_account_ids):
    """Test building transaction body when new optional fields are None."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 456)

    account_tx = AccountUpdateTransaction()
    account_tx.set_account_id(account_id)

    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id

    transaction_body = account_tx.build_transaction_body()

    # When new fields are None, they should not be set in the protobuf
    assert not transaction_body.cryptoUpdateAccount.HasField(
        "max_automatic_token_associations"
    )
    assert not transaction_body.cryptoUpdateAccount.HasField("staked_account_id")
    assert not transaction_body.cryptoUpdateAccount.HasField("staked_node_id")
    assert not transaction_body.cryptoUpdateAccount.HasField("decline_reward")


def test_build_transaction_body_with_cleared_staking(mock_account_ids):
    """Sentinel values should be emitted when staking is cleared."""
    operator_id, _, node_account_id, _, _ = mock_account_ids
    account_id = AccountId(0, 0, 123)

    # Clear staked account
    account_tx = AccountUpdateTransaction().set_account_id(account_id)
    account_tx.set_staked_account_id(None)
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id
    txn_body = account_tx.build_transaction_body().cryptoUpdateAccount
    assert txn_body.staked_account_id.accountNum == 0
    assert txn_body.staked_account_id.realmNum == 0
    assert txn_body.staked_account_id.shardNum == 0
    assert not txn_body.HasField("staked_node_id")

    # Clear staked node
    account_tx = AccountUpdateTransaction().set_account_id(account_id)
    account_tx.set_staked_node_id(None)
    account_tx.operator_account_id = operator_id
    account_tx.node_account_id = node_account_id
    txn_body = account_tx.build_transaction_body().cryptoUpdateAccount
    assert txn_body.staked_node_id == -1
    assert not txn_body.HasField("staked_account_id")
