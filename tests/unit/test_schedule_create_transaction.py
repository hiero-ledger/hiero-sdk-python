"""
Test cases for the ScheduleCreateTransaction class.
"""

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.schedule.schedule_create_transaction import (
    ScheduleCreateParams,
    ScheduleCreateTransaction,
)
from hiero_sdk_python.timestamp import Timestamp
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
    schedule_tx.node_account_id = node_account_id

    transaction_body = schedule_tx.build_transaction_body()

    # Verify the transaction body contains scheduleCreate field
    assert transaction_body.HasField("scheduleCreate")

    # Verify all fields are correctly set
    schedule_create = transaction_body.scheduleCreate
    assert (
        schedule_create.payerAccountID == schedule_params["payer_account_id"]._to_proto()
    )
    assert schedule_create.adminKey == schedule_params["admin_key"]._to_proto()
    assert schedule_create.scheduledTransactionBody == schedule_params["schedulable_body"]
    assert schedule_create.memo == schedule_params["schedule_memo"]
    assert (
        schedule_create.expiration_time
        == schedule_params["expiration_time"]._to_protobuf()
    )
    assert schedule_create.wait_for_expiry == schedule_params["wait_for_expiry"]


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
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
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
    body_bytes = schedule_tx._transaction_body_bytes[node_id]

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
