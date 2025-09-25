"""
Unit tests for the ScheduleInfo class.
"""

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.schedule_get_info_pb2 import (
    ScheduleInfo as ScheduleInfoProto,
)
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info import ScheduleInfo
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


@pytest.fixture
def schedule_info():
    """Fixture for a ScheduleInfo object"""
    return ScheduleInfo(
        schedule_id=ScheduleId(0, 0, 100),
        creator_account_id=AccountId(0, 0, 200),
        payer_account_id=AccountId(0, 0, 300),
        deleted_at=Timestamp(1625097600, 0),
        executed_at=Timestamp(1625097601, 0),
        expiration_time=Timestamp(1625097602, 0),
        scheduled_transaction_id=TransactionId.generate(AccountId(0, 0, 200)),
        scheduled_transaction_body=SchedulableTransactionBody(),
        schedule_memo="Test schedule memo",
        admin_key=PrivateKey.generate_ed25519().public_key(),
        signers=[PrivateKey.generate_ed25519().public_key()],
        ledger_id=b"test_ledger_id",
        wait_for_expiry=True,
    )


@pytest.fixture
def proto_schedule_info():
    """Fixture for a proto ScheduleInfo object"""
    public_key = PrivateKey.generate_ed25519().public_key()
    schedule_id = ScheduleId(0, 0, 100)
    creator_account_id = AccountId(0, 0, 200)
    payer_account_id = AccountId(0, 0, 300)
    scheduled_transaction_id = TransactionId.generate(creator_account_id)

    proto = ScheduleInfoProto(
        scheduleID=schedule_id._to_proto(),
        creatorAccountID=creator_account_id._to_proto(),
        payerAccountID=payer_account_id._to_proto(),
        deletion_time=None,
        execution_time=Timestamp(1625097601, 0)._to_protobuf(),
        expirationTime=Timestamp(1625097602, 0)._to_protobuf(),
        scheduledTransactionID=scheduled_transaction_id._to_proto(),
        scheduledTransactionBody=SchedulableTransactionBody(),
        memo="Test schedule memo",
        adminKey=public_key._to_proto(),
        signers=KeyListProto(keys=[public_key._to_proto()]),
        ledger_id=b"test_ledger_id",
        wait_for_expiry=True,
    )
    return proto


def test_schedule_info_initialization(schedule_info):
    """Test the initialization of the ScheduleInfo class"""
    assert schedule_info.schedule_id == ScheduleId(0, 0, 100)
    assert schedule_info.creator_account_id == AccountId(0, 0, 200)
    assert schedule_info.payer_account_id == AccountId(0, 0, 300)
    assert schedule_info.deleted_at == Timestamp(1625097600, 0)
    assert schedule_info.executed_at == Timestamp(1625097601, 0)
    assert schedule_info.expiration_time == Timestamp(1625097602, 0)
    assert schedule_info.scheduled_transaction_id is not None
    assert schedule_info.scheduled_transaction_body is not None
    assert schedule_info.schedule_memo == "Test schedule memo"
    assert schedule_info.admin_key is not None
    assert len(schedule_info.signers) == 1
    assert schedule_info.ledger_id == b"test_ledger_id"
    assert schedule_info.wait_for_expiry is True


def test_schedule_info_default_initialization():
    """Test the default initialization of the ScheduleInfo class"""
    schedule_info = ScheduleInfo()
    assert schedule_info.schedule_id is None
    assert schedule_info.creator_account_id is None
    assert schedule_info.payer_account_id is None
    assert schedule_info.deleted_at is None
    assert schedule_info.executed_at is None
    assert schedule_info.expiration_time is None
    assert schedule_info.scheduled_transaction_id is None
    assert schedule_info.scheduled_transaction_body is None
    assert schedule_info.schedule_memo is None
    assert schedule_info.admin_key is None
    assert not schedule_info.signers
    assert schedule_info.ledger_id is None
    assert schedule_info.wait_for_expiry is None


def test_from_proto(proto_schedule_info):
    """Test the from_proto method of the ScheduleInfo class"""
    schedule_info = ScheduleInfo._from_proto(proto_schedule_info)

    assert schedule_info.schedule_id == ScheduleId(0, 0, 100)
    assert schedule_info.creator_account_id == AccountId(0, 0, 200)
    assert schedule_info.payer_account_id == AccountId(0, 0, 300)
    assert schedule_info.deleted_at is None
    assert schedule_info.executed_at == Timestamp(1625097601, 0)
    assert schedule_info.expiration_time == Timestamp(1625097602, 0)
    assert schedule_info.scheduled_transaction_id is not None
    assert schedule_info.scheduled_transaction_body is not None
    assert schedule_info.schedule_memo == "Test schedule memo"
    assert schedule_info.admin_key is not None
    assert len(schedule_info.signers) == 1
    assert schedule_info.ledger_id == b"test_ledger_id"
    assert schedule_info.wait_for_expiry is True


def test_from_proto_with_empty_signers():
    """Test the from_proto method of the ScheduleInfo class with empty signers"""
    public_key = PrivateKey.generate_ed25519().public_key()
    schedule_id = ScheduleId(0, 0, 100)
    creator_account_id = AccountId(0, 0, 200)
    payer_account_id = AccountId(0, 0, 300)
    scheduled_transaction_id = TransactionId.generate(creator_account_id)

    proto = ScheduleInfoProto(
        scheduleID=schedule_id._to_proto(),
        creatorAccountID=creator_account_id._to_proto(),
        payerAccountID=payer_account_id._to_proto(),
        expirationTime=Timestamp(1625097602, 0)._to_protobuf(),
        scheduledTransactionID=scheduled_transaction_id._to_proto(),
        scheduledTransactionBody=SchedulableTransactionBody(),
        memo="Test schedule memo",
        adminKey=public_key._to_proto(),
        signers=KeyListProto(keys=[]),
        ledger_id=b"test_ledger_id",
        wait_for_expiry=True,
    )

    schedule_info = ScheduleInfo._from_proto(proto)
    assert schedule_info.schedule_id == ScheduleId(0, 0, 100)
    assert schedule_info.creator_account_id == AccountId(0, 0, 200)
    assert schedule_info.payer_account_id == AccountId(0, 0, 300)
    assert schedule_info.schedule_memo == "Test schedule memo"
    assert not schedule_info.signers


def test_from_proto_none_raises_error():
    """Test the from_proto method of the ScheduleInfo class with a None proto"""
    with pytest.raises(ValueError, match="Schedule info proto is None"):
        ScheduleInfo._from_proto(None)


def test_to_proto(schedule_info):
    """Test the to_proto method of the ScheduleInfo class"""
    proto = schedule_info._to_proto()

    assert proto.scheduleID == ScheduleId(0, 0, 100)._to_proto()
    assert proto.creatorAccountID == AccountId(0, 0, 200)._to_proto()
    assert proto.payerAccountID == AccountId(0, 0, 300)._to_proto()
    assert not proto.HasField("deletion_time")
    assert proto.execution_time == Timestamp(1625097601, 0)._to_protobuf()
    assert proto.expirationTime == Timestamp(1625097602, 0)._to_protobuf()
    assert proto.scheduledTransactionID is not None
    assert proto.scheduledTransactionBody is not None
    assert proto.memo == "Test schedule memo"
    assert proto.adminKey is not None
    assert len(proto.signers.keys) == 1
    assert proto.ledger_id == b"test_ledger_id"
    assert proto.wait_for_expiry is True


def test_to_proto_with_none_values():
    """Test the to_proto method of the ScheduleInfo class with none values"""
    schedule_info = ScheduleInfo()
    proto = schedule_info._to_proto()

    # Protobuf has default values, so we check the proto structure exists
    assert hasattr(proto, "scheduleID")
    assert hasattr(proto, "creatorAccountID")
    assert hasattr(proto, "payerAccountID")
    assert hasattr(proto, "deletion_time")
    assert hasattr(proto, "execution_time")
    assert hasattr(proto, "expirationTime")
    assert hasattr(proto, "scheduledTransactionID")
    assert hasattr(proto, "scheduledTransactionBody")
    assert proto.memo == ""  # Empty string is default for protobuf
    assert hasattr(proto, "adminKey")
    assert not proto.signers.keys  # Empty list for signers
    assert proto.ledger_id == b""  # Empty bytes is default for protobuf
    assert proto.wait_for_expiry is False  # False is default for protobuf bool


def test_to_proto_with_empty_signers():
    """Test the to_proto method of the ScheduleInfo class with empty signers list"""
    schedule_info = ScheduleInfo(
        schedule_id=ScheduleId(0, 0, 100),
        creator_account_id=AccountId(0, 0, 200),
        payer_account_id=AccountId(0, 0, 300),
        schedule_memo="Test schedule memo",
        signers=[],
    )
    proto = schedule_info._to_proto()

    assert proto.scheduleID == ScheduleId(0, 0, 100)._to_proto()
    assert proto.creatorAccountID == AccountId(0, 0, 200)._to_proto()
    assert proto.payerAccountID == AccountId(0, 0, 300)._to_proto()
    assert proto.memo == "Test schedule memo"
    assert proto.signers.keys == []


def test_proto_conversion_full_object(schedule_info):
    """Test proto conversion with fully populated object"""
    converted = ScheduleInfo._from_proto(schedule_info._to_proto())

    assert converted.schedule_id == schedule_info.schedule_id
    assert converted.creator_account_id == schedule_info.creator_account_id
    assert converted.payer_account_id == schedule_info.payer_account_id
    assert converted.deleted_at is None
    assert converted.executed_at == schedule_info.executed_at
    assert converted.expiration_time == schedule_info.expiration_time
    assert converted.scheduled_transaction_id == schedule_info.scheduled_transaction_id
    assert (
        converted.scheduled_transaction_body == schedule_info.scheduled_transaction_body
    )
    assert converted.schedule_memo == schedule_info.schedule_memo
    assert converted.admin_key.to_bytes_raw() == schedule_info.admin_key.to_bytes_raw()
    assert len(converted.signers) == len(schedule_info.signers)
    assert converted.ledger_id == schedule_info.ledger_id
    assert converted.wait_for_expiry == schedule_info.wait_for_expiry


def test_proto_conversion_multiple_signers():
    """Test proto conversion with multiple signers"""
    signer1 = PrivateKey.generate_ed25519().public_key()
    signer2 = PrivateKey.generate_ed25519().public_key()

    schedule_info = ScheduleInfo(
        schedule_id=ScheduleId(0, 0, 100),
        signers=[signer1, signer2],
    )
    converted = ScheduleInfo._from_proto(schedule_info._to_proto())

    assert len(converted.signers) == 2
    assert converted.signers[0].to_bytes_raw() == signer1.to_bytes_raw()
    assert converted.signers[1].to_bytes_raw() == signer2.to_bytes_raw()


def test_proto_conversion_minimal_fields():
    """Test proto conversion with minimal fields"""
    schedule_info = ScheduleInfo(
        schedule_id=ScheduleId(0, 0, 100),
        schedule_memo="Minimal schedule",
        wait_for_expiry=False,
    )
    converted = ScheduleInfo._from_proto(schedule_info._to_proto())

    assert converted.schedule_id == schedule_info.schedule_id
    assert converted.schedule_memo == schedule_info.schedule_memo
    assert converted.wait_for_expiry == schedule_info.wait_for_expiry
    assert converted.admin_key is None
    assert not converted.signers


def test_from_proto_field_helper():
    """Test the _from_proto_field helper method"""
    public_key = PrivateKey.generate_ed25519().public_key()
    schedule_id = ScheduleId(0, 0, 100)

    proto = ScheduleInfoProto(
        scheduleID=schedule_id._to_proto(),
        adminKey=public_key._to_proto(),
    )

    # Test with populated field
    result = ScheduleInfo._from_proto_field(proto, "scheduleID", ScheduleId._from_proto)
    assert result == schedule_id

    # Test with empty field
    result = ScheduleInfo._from_proto_field(
        proto, "execution_time", ScheduleId._from_proto
    )
    assert result is None


def test_convert_to_proto_helper():
    """Test the _convert_to_proto helper method"""
    schedule_info = ScheduleInfo()

    # Test with None value
    result = schedule_info._convert_to_proto(None, ScheduleId._to_proto)
    assert result is None

    # Test with valid value
    schedule_id = ScheduleId(0, 0, 100)
    result = schedule_info._convert_to_proto(schedule_id, ScheduleId._to_proto)
    assert result == schedule_id._to_proto()
