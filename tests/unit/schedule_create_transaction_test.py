"""
Test cases for the ScheduleCreateTransaction class.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.schedule.schedule_create_transaction import (
    ScheduleCreateParams,
    ScheduleCreateTransaction,
)
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit


@pytest.fixture
def schedule_params():
    """Fixture for schedule create parameters."""
    return {
        "payer_account_id": AccountId(0, 0, 123),
        "admin_key": PrivateKey.generate_ed25519().public_key(),
        "schedulable_body": TransferTransaction().build_scheduled_body(),
        "schedule_memo": "test memo",
        "expiration_time": Timestamp(seconds=1620000000, nanos=0),
        "wait_for_expiry": True,
    }


def test_constructor_with_parameters(schedule_params):
    """Test creating a schedule create transaction with constructor parameters."""
    schedule_create_params = ScheduleCreateParams(
        payer_account_id=schedule_params["payer_account_id"],
        admin_key=schedule_params["admin_key"],
        schedulable_body=schedule_params["schedulable_body"],
        schedule_memo=schedule_params["schedule_memo"],
        expiration_time=schedule_params["expiration_time"],
        wait_for_expiry=schedule_params["wait_for_expiry"],
    )

    schedule_tx = ScheduleCreateTransaction(schedule_params=schedule_create_params)

    assert schedule_tx.payer_account_id == schedule_params["payer_account_id"]
    assert schedule_tx.admin_key == schedule_params["admin_key"]
    assert schedule_tx.schedulable_body == schedule_params["schedulable_body"]
    assert schedule_tx.schedule_memo == schedule_params["schedule_memo"]
    assert schedule_tx.expiration_time == schedule_params["expiration_time"]
    assert schedule_tx.wait_for_expiry == schedule_params["wait_for_expiry"]


def test_constructor_default_values():
    """Test that constructor sets default values correctly."""
    schedule_tx = ScheduleCreateTransaction()

    assert schedule_tx.payer_account_id is None
    assert schedule_tx.admin_key is None
    assert schedule_tx.schedulable_body is None
    assert schedule_tx.schedule_memo is None
    assert schedule_tx.expiration_time is None
    assert schedule_tx.wait_for_expiry is None
    assert schedule_tx._default_transaction_fee == 500000000  # 5 hbar in tinybars


def test_build_transaction_body_with_valid_parameters(mock_account_ids, schedule_params):
    """Test building a schedule create transaction body with valid parameters."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    schedule_create_params = ScheduleCreateParams(**schedule_params)
    schedule_tx = ScheduleCreateTransaction(schedule_params=schedule_create_params)

    # Set operator and node account IDs needed for building transaction body
    schedule_tx.operator_account_id = operator_id
    schedule_tx.set_node_account_ids([node_account_id])

    transaction_body = schedule_tx.build_transaction_body()

    # Verify the transaction body contains scheduleCreate field
    assert transaction_body.HasField("scheduleCreate")

    # Verify all fields are correctly set
    schedule_create = transaction_body.scheduleCreate
    assert schedule_create.payerAccountID == schedule_params["payer_account_id"]._to_proto()
    assert schedule_create.adminKey == schedule_params["admin_key"].to_proto_key()
    assert schedule_create.scheduledTransactionBody == schedule_params["schedulable_body"]
    assert schedule_create.memo == schedule_params["schedule_memo"]
    assert schedule_create.expiration_time == schedule_params["expiration_time"]._to_protobuf()
    assert schedule_create.wait_for_expiry == schedule_params["wait_for_expiry"]


@pytest.mark.parametrize(
    "admin_key",
    [
        PrivateKey.generate(),
        KeyList([PrivateKey.generate().public_key(), PrivateKey.generate().public_key()]),
    ],
    ids=["private-key", "key-list"],
)
def test_build_proto_body_with_generic_admin_key(admin_key):
    """Test building a schedule create body with generic admin key types."""
    schedule_tx = ScheduleCreateTransaction().set_admin_key(admin_key)

    proto_body = schedule_tx._build_proto_body()

    assert schedule_tx.admin_key is admin_key
    assert proto_body.adminKey == admin_key.to_proto_key()


def test_set_schedulable_body(schedule_params):
    """Test setting schedulable_body using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx._set_schedulable_body(schedule_params["schedulable_body"])

    assert schedule_tx.schedulable_body == schedule_params["schedulable_body"]
    assert result is schedule_tx


def test_set_scheduled_transaction():
    """Test setting scheduled transaction using the setter method."""
    schedule_tx = ScheduleCreateTransaction()
    transfer_tx = TransferTransaction()

    result = schedule_tx.set_scheduled_transaction(transfer_tx)

    assert schedule_tx.schedulable_body == transfer_tx.build_scheduled_body()
    assert result is schedule_tx  # Should return self for method chaining


def test_set_schedule_memo(schedule_params):
    """Test setting schedule_memo using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx.set_schedule_memo(schedule_params["schedule_memo"])

    assert schedule_tx.schedule_memo == schedule_params["schedule_memo"]
    assert result is schedule_tx  # Should return self for method chaining


def test_set_payer_account_id(schedule_params):
    """Test setting payer_account_id using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx.set_payer_account_id(schedule_params["payer_account_id"])

    assert schedule_tx.payer_account_id == schedule_params["payer_account_id"]
    assert result is schedule_tx  # Should return self for method chaining


def test_set_expiration_time(schedule_params):
    """Test setting expiration_time using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx.set_expiration_time(schedule_params["expiration_time"])

    assert schedule_tx.expiration_time == schedule_params["expiration_time"]
    assert result is schedule_tx  # Should return self for method chaining


def test_set_wait_for_expiry(schedule_params):
    """Test setting wait_for_expiry using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx.set_wait_for_expiry(schedule_params["wait_for_expiry"])

    assert schedule_tx.wait_for_expiry == schedule_params["wait_for_expiry"]
    assert result is schedule_tx  # Should return self for method chaining


def test_set_admin_key(schedule_params):
    """Test setting admin_key using the setter method."""
    schedule_tx = ScheduleCreateTransaction()

    result = schedule_tx.set_admin_key(schedule_params["admin_key"])

    assert schedule_tx.admin_key == schedule_params["admin_key"]
    assert result is schedule_tx  # Should return self for method chaining


def test_method_chaining_with_all_setters(schedule_params):
    """Test that all setter methods support method chaining."""
    schedule_tx = ScheduleCreateTransaction()

    result = (
        schedule_tx.set_payer_account_id(schedule_params["payer_account_id"])
        .set_admin_key(schedule_params["admin_key"])
        ._set_schedulable_body(schedule_params["schedulable_body"])
        .set_schedule_memo(schedule_params["schedule_memo"])
        .set_expiration_time(schedule_params["expiration_time"])
        .set_wait_for_expiry(schedule_params["wait_for_expiry"])
    )

    assert result is schedule_tx
    assert schedule_tx.payer_account_id == schedule_params["payer_account_id"]
    assert schedule_tx.admin_key == schedule_params["admin_key"]
    assert schedule_tx.schedulable_body == schedule_params["schedulable_body"]
    assert schedule_tx.schedule_memo == schedule_params["schedule_memo"]
    assert schedule_tx.expiration_time == schedule_params["expiration_time"]
    assert schedule_tx.wait_for_expiry == schedule_params["wait_for_expiry"]


def test_set_methods_require_not_frozen(mock_client, schedule_params):
    """Test that setter methods raise exception when transaction is frozen."""
    schedule_tx = ScheduleCreateTransaction()
    schedule_tx.freeze_with(mock_client)

    test_cases = [
        ("_set_schedulable_body", schedule_params["schedulable_body"]),
        ("set_scheduled_transaction", TransferTransaction()),
        ("set_schedule_memo", schedule_params["schedule_memo"]),
        ("set_payer_account_id", schedule_params["payer_account_id"]),
        ("set_expiration_time", schedule_params["expiration_time"]),
        ("set_wait_for_expiry", schedule_params["wait_for_expiry"]),
        ("set_admin_key", schedule_params["admin_key"]),
    ]

    for method_name, value in test_cases:
        with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
            getattr(schedule_tx, method_name)(value)


def test_build_scheduled_body_raises_exception():
    """Test that build_scheduled_body raises ValueError."""
    schedule_tx = ScheduleCreateTransaction()

    with pytest.raises(ValueError, match="Cannot schedule a ScheduleCreateTransaction"):
        schedule_tx.build_scheduled_body()


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    schedule_tx = ScheduleCreateTransaction()

    mock_channel = MagicMock()
    mock_schedule_stub = MagicMock()
    mock_channel.schedule = mock_schedule_stub

    method = schedule_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_schedule_stub.createSchedule


def test_sign_transaction(mock_client):
    """Test signing the schedule create transaction with a private key."""
    schedule_tx = ScheduleCreateTransaction()
    schedule_tx.set_scheduled_transaction(TransferTransaction())

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    schedule_tx.freeze_with(mock_client)
    schedule_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = schedule_tx._transaction_body_bytes[schedule_tx.transaction_id][node_id]

    assert len(schedule_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = schedule_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client):
    """Test converting the schedule create transaction to protobuf format after signing."""
    schedule_tx = ScheduleCreateTransaction()
    schedule_tx.set_scheduled_transaction(TransferTransaction())

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    schedule_tx.freeze_with(mock_client)
    schedule_tx.sign(private_key)
    proto = schedule_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def _freeze(params, client):
    return ScheduleCreateTransaction(ScheduleCreateParams(**params)).freeze_with(client)


def test_from_bytes_round_trip(mock_client, schedule_params):
    """Test that from_bytes restores every schedule field and keeps the bytes identical."""
    schedule_params["expiration_time"] = Timestamp(seconds=1620000000, nanos=123456789)
    original = _freeze(schedule_params, mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, ScheduleCreateTransaction)
    assert restored.payer_account_id == schedule_params["payer_account_id"]
    assert restored.admin_key == schedule_params["admin_key"]
    assert restored.schedulable_body == schedule_params["schedulable_body"]
    assert restored.schedule_memo == schedule_params["schedule_memo"]
    assert restored.expiration_time == schedule_params["expiration_time"]
    assert restored.wait_for_expiry is True
    assert restored.to_bytes() == original_bytes


@pytest.mark.parametrize(
    "inner",
    [
        TransferTransaction().add_hbar_transfer(AccountId(0, 0, 123), -10).add_hbar_transfer(AccountId(0, 0, 456), 10),
        TokenDeleteTransaction().set_token_id(TokenId(0, 0, 5)),
    ],
    ids=["transfer", "token_delete"],
)
def test_from_bytes_round_trip_inner_transaction(mock_client, schedule_params, inner):
    """Test that the scheduled transaction survives the round trip whatever its type."""
    schedule_params["schedulable_body"] = inner.build_scheduled_body()
    original = _freeze(schedule_params, mock_client)

    restored = Transaction.from_bytes(original.to_bytes())

    assert restored.schedulable_body == inner.build_scheduled_body()
    assert restored.schedulable_body.WhichOneof("data") == inner.build_scheduled_body().WhichOneof("data")


@pytest.mark.parametrize(
    "admin_key",
    [
        PrivateKey.generate_ed25519().public_key(),
        PrivateKey.generate_ecdsa().public_key(),
        KeyList([PrivateKey.generate_ed25519().public_key(), PrivateKey.generate_ecdsa().public_key()], threshold=1),
    ],
    ids=["ed25519", "ecdsa", "threshold_key_list"],
)
def test_from_bytes_round_trip_admin_key(mock_client, schedule_params, admin_key):
    """Test that each kind of admin key restores to the same protobuf key."""
    schedule_params["admin_key"] = admin_key
    original = _freeze(schedule_params, mock_client)

    restored = Transaction.from_bytes(original.to_bytes())

    assert restored.admin_key.to_proto_key() == admin_key.to_proto_key()


def test_from_bytes_round_trip_unset_fields(mock_client):
    """Test that unset message fields come back as None and plain fields keep their proto defaults."""
    original = ScheduleCreateTransaction().freeze_with(mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, ScheduleCreateTransaction)
    assert restored.payer_account_id is None
    assert restored.admin_key is None
    assert restored.schedulable_body is None
    assert restored.expiration_time is None
    assert restored.schedule_memo == ""
    assert restored.wait_for_expiry is False
    assert restored.to_bytes() == original_bytes


def test_from_bytes_round_trip_explicit_default_values(mock_client, schedule_params):
    """Test that an explicitly empty memo and wait_for_expiry=False are restored as set."""
    schedule_params["schedule_memo"] = ""
    schedule_params["wait_for_expiry"] = False
    original = _freeze(schedule_params, mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert restored.schedule_memo == ""
    assert restored.wait_for_expiry is False
    assert restored.to_bytes() == original_bytes


def test_from_bytes_round_trip_multiple_nodes(mock_client, schedule_params):
    """Test the multi-node path, where every node's body is restored and the fields still match."""
    original = ScheduleCreateTransaction(ScheduleCreateParams(**schedule_params))
    original.set_node_account_ids([AccountId(0, 0, 3), AccountId(0, 0, 4)])
    original.freeze_with(mock_client)
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, ScheduleCreateTransaction)
    assert restored.node_account_ids == [AccountId(0, 0, 3), AccountId(0, 0, 4)]
    assert restored.schedulable_body == schedule_params["schedulable_body"]
    assert restored.schedule_memo == schedule_params["schedule_memo"]
    assert restored.to_bytes() == original_bytes
