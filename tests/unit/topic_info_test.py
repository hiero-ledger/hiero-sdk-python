import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services import consensus_topic_info_pb2
from hiero_sdk_python.hapi.services.basic_types_pb2 import AccountID, Key
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee

pytestmark = pytest.mark.unit


@pytest.fixture
def topic_info():
    """Create a TopicInfo instance with all parameters for testing."""
    public_key = PrivateKey.generate_ed25519().public_key()

    # Create protobuf timestamp
    timestamp = Timestamp()
    timestamp.seconds = 1625097600  # 2021-07-01 00:00:00 UTC
    timestamp.nanos = 0

    # Create protobuf account ID
    account_id = AccountID()
    account_id.shardNum = 0
    account_id.realmNum = 0
    account_id.accountNum = 100

    # Create protobuf key
    key = Key()
    key.ed25519 = public_key.to_bytes_raw()

    # Create custom fee
    custom_fee = CustomFixedFee(
        amount=1000,
        denominating_token_id=None,
        fee_collector_account_id=AccountId(0, 0, 200),
        all_collectors_are_exempt=False,
    )

    return TopicInfo(
        memo="Test topic memo",
        running_hash=b"\x01\x02\x03\x04\x05\x06\x07\x08",
        sequence_number=42,
        expiration_time=timestamp,
        admin_key=key,
        submit_key=key,
        auto_renew_period=Duration(7776000),  # 90 days
        auto_renew_account=account_id,
        ledger_id=b"\x09\x0a\x0b\x0c",
        fee_schedule_key=public_key,
        fee_exempt_keys=[public_key],
        custom_fees=[custom_fee],
    )


@pytest.fixture
def proto_topic_info():
    """Create a protobuf ConsensusTopicInfo for testing."""
    public_key = PrivateKey.generate_ed25519().public_key()

    # Create protobuf timestamp
    timestamp = Timestamp()
    timestamp.seconds = 1625097600  # 2021-07-01 00:00:00 UTC
    timestamp.nanos = 0

    # Create protobuf account ID
    account_id = AccountID()
    account_id.shardNum = 0
    account_id.realmNum = 0
    account_id.accountNum = 100

    # Create protobuf key
    key = Key()
    key.ed25519 = public_key.to_bytes_raw()

    # Create custom fee
    custom_fee = CustomFixedFee(
        amount=1000,
        denominating_token_id=None,
        fee_collector_account_id=AccountId(0, 0, 200),
        all_collectors_are_exempt=False,
    )

    proto = consensus_topic_info_pb2.ConsensusTopicInfo()
    proto.memo = "Test topic memo"
    proto.runningHash = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    proto.sequenceNumber = 42
    proto.expirationTime.CopyFrom(timestamp)
    proto.adminKey.CopyFrom(key)
    proto.submitKey.CopyFrom(key)
    proto.autoRenewPeriod.seconds = 7776000
    proto.autoRenewAccount.CopyFrom(account_id)
    proto.ledger_id = b"\x09\x0a\x0b\x0c"
    proto.fee_schedule_key.CopyFrom(public_key._to_proto())
    proto.fee_exempt_key_list.append(public_key._to_proto())
    proto.custom_fees.append(custom_fee._to_topic_fee_proto())
    return proto


def test_topic_info_initialization(topic_info):
    """Test the initialization of the TopicInfo class with all parameters."""
    assert topic_info.memo == "Test topic memo"
    assert topic_info.running_hash == b"\x01\x02\x03\x04\x05\x06\x07\x08"
    assert topic_info.sequence_number == 42
    assert topic_info.expiration_time is not None
    assert topic_info.admin_key is not None
    assert topic_info.submit_key is not None
    assert topic_info.auto_renew_period == Duration(7776000)
    assert topic_info.auto_renew_account is not None
    assert topic_info.ledger_id == b"\x09\x0a\x0b\x0c"
    assert topic_info.fee_schedule_key is not None
    assert len(topic_info.fee_exempt_keys) == 1
    assert len(topic_info.custom_fees) == 1
    assert topic_info.custom_fees[0].amount == 1000


def test_topic_info_initialization_with_none_values():
    """Test the initialization of the TopicInfo class with None values for optional parameters."""
    topic_info = TopicInfo(
        memo="Test memo",
        running_hash=b"\x01\x02",
        sequence_number=1,
        expiration_time=None,
        admin_key=None,
        submit_key=None,
        auto_renew_period=None,
        auto_renew_account=None,
        ledger_id=None,
        fee_schedule_key=None,
        fee_exempt_keys=None,
        custom_fees=None,
    )

    assert topic_info.memo == "Test memo"
    assert topic_info.running_hash == b"\x01\x02"
    assert topic_info.sequence_number == 1
    assert topic_info.expiration_time is None
    assert topic_info.admin_key is None
    assert topic_info.submit_key is None
    assert topic_info.auto_renew_period is None
    assert topic_info.auto_renew_account is None
    assert topic_info.ledger_id is None
    assert topic_info.fee_schedule_key is None
    assert not topic_info.fee_exempt_keys
    assert not topic_info.custom_fees


def test_topic_info_initialization_with_empty_lists():
    """Test the initialization of the TopicInfo class with empty lists."""
    topic_info = TopicInfo(
        memo="Test memo",
        running_hash=b"\x01\x02",
        sequence_number=1,
        expiration_time=None,
        admin_key=None,
        submit_key=None,
        auto_renew_period=None,
        auto_renew_account=None,
        ledger_id=None,
        fee_schedule_key=None,
        fee_exempt_keys=[],
        custom_fees=[],
    )

    assert not topic_info.fee_exempt_keys
    assert not topic_info.custom_fees


def test_from_proto(proto_topic_info):
    """Test the _from_proto method of the TopicInfo class."""
    topic_info = TopicInfo._from_proto(proto_topic_info)

    assert topic_info.memo == "Test topic memo"
    assert topic_info.running_hash == b"\x01\x02\x03\x04\x05\x06\x07\x08"
    assert topic_info.sequence_number == 42
    assert topic_info.expiration_time is not None
    assert topic_info.admin_key is not None
    assert topic_info.submit_key is not None
    assert topic_info.auto_renew_period == Duration(7776000)
    assert topic_info.auto_renew_account is not None
    assert topic_info.ledger_id == b"\x09\x0a\x0b\x0c"
    assert topic_info.fee_schedule_key is not None
    assert len(topic_info.fee_exempt_keys) == 1
    assert len(topic_info.custom_fees) == 1
    assert topic_info.custom_fees[0].amount == 1000


def test_from_proto_with_auto_renew_period():
    """Test the _from_proto method with auto renew period."""
    proto = consensus_topic_info_pb2.ConsensusTopicInfo()
    proto.memo = "Test memo"
    proto.runningHash = b"\x01\x02"
    proto.sequenceNumber = 1
    proto.autoRenewPeriod.seconds = 86400  # 1 day

    topic_info = TopicInfo._from_proto(proto)

    assert topic_info.auto_renew_period == Duration(86400)


def test_from_proto_with_fee_exempt_keys():
    """Test the _from_proto method with fee exempt keys."""
    public_key = PrivateKey.generate_ed25519().public_key()

    proto = consensus_topic_info_pb2.ConsensusTopicInfo()
    proto.memo = "Test memo"
    proto.runningHash = b"\x01\x02"
    proto.sequenceNumber = 1
    proto.fee_exempt_key_list.append(public_key._to_proto())
    proto.fee_exempt_key_list.append(public_key._to_proto())

    topic_info = TopicInfo._from_proto(proto)

    assert len(topic_info.fee_exempt_keys) == 2
    # Compare hex representations since PublicKey objects don't compare directly
    assert topic_info.fee_exempt_keys[0].to_bytes_raw() == public_key.to_bytes_raw()
    assert topic_info.fee_exempt_keys[1].to_bytes_raw() == public_key.to_bytes_raw()


def test_from_proto_with_custom_fees():
    """Test the _from_proto method with custom fees."""
    custom_fee = CustomFixedFee(
        amount=1000,
        denominating_token_id=None,
        fee_collector_account_id=AccountId(0, 0, 200),
        all_collectors_are_exempt=False,
    )

    proto = consensus_topic_info_pb2.ConsensusTopicInfo()
    proto.memo = "Test memo"
    proto.runningHash = b"\x01\x02"
    proto.sequenceNumber = 1
    proto.custom_fees.append(custom_fee._to_topic_fee_proto())
    proto.custom_fees.append(custom_fee._to_topic_fee_proto())

    topic_info = TopicInfo._from_proto(proto)

    assert len(topic_info.custom_fees) == 2
    assert topic_info.custom_fees[0].amount == custom_fee.amount
    assert topic_info.custom_fees[1].amount == custom_fee.amount


def test_repr_and_str(topic_info):
    """Test the __repr__ and __str__ methods of the TopicInfo class."""
    str_output = str(topic_info)
    repr_output = repr(topic_info)

    assert str_output == repr_output
    assert "TopicInfo" in repr_output
    assert "memo='Test topic memo'" in repr_output
    assert "sequence_number=42" in repr_output
    assert "running_hash=0x0102030405060708" in repr_output
    assert "expiration_time=2021-07-01" in str_output  
    assert "auto_renew_period=7776000" in repr_output

def test_str_formatting(topic_info):
    """Test the string formatting of the TopicInfo class."""
    str_output = str(topic_info)

    assert "TopicInfo(" in str_output
    assert "memo='Test topic memo'" in str_output
    assert "running_hash=0x0102030405060708" in str_output
    assert "sequence_number=42" in str_output
    # Instead of the full date-time string
    assert "expiration_time=2021-07-01" in str_output   
    assert "admin_key=ed25519(" in str_output
    assert "submit_key=ed25519(" in str_output 
    assert "auto_renew_period=7776000" in str_output
    assert "auto_renew_account=AccountId(shard=0, realm=0, account=100)" in str_output
    assert "ledger_id=0x090a0b0c" in str_output
    assert "fee_schedule_key=ed25519(" in str_output
    assert "fee_exempt_keys=['ed25519(" in str_output
    assert "custom_fees=[" in str_output

def test_str_with_none_values():
    """Test the string formatting of the TopicInfo class with None values."""
    topic_info = TopicInfo(
        memo="Test memo",
        running_hash=b"\x01\x02",
        sequence_number=1,
        expiration_time=None,
        admin_key=None,
        submit_key=None,
        auto_renew_period=None,
        auto_renew_account=None,
        ledger_id=None,
        fee_schedule_key=None,
        fee_exempt_keys=None,
        custom_fees=None,
    )

    str_output = str(topic_info)

    assert "TopicInfo(" in str_output
    assert "memo='Test memo'" in str_output
    assert "running_hash=0x0102" in str_output
    assert "sequence_number=1" in str_output
    assert "expiration_time=None" in str_output
    assert "admin_key=None" in str_output
    assert "submit_key=None" in str_output
    assert "auto_renew_period=None" in str_output
    assert "auto_renew_account=None" in str_output
    assert "ledger_id=None" in str_output
    assert "fee_schedule_key=None" in str_output
    assert "fee_exempt_keys=[]" in str_output
    assert "custom_fees=[]" in str_output

