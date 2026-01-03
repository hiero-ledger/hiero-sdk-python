"""
**INTERNAL DEVELOPER REFERENCE**

This example is primarily for internal SDK developers and contributors.

---

This example demonstrates how to work with the TopicInfo class.

TopicInfo represents consensus topic information on the Hedera network.
It exposes attributes such as memo, running hash, sequence number, expiration time,
admin key, submit key, auto-renewal configuration, and ledger ID.

This example shows:
- How to manually construct a TopicInfo instance with mock data
- How to populate key fields
- How to inspect or pretty-print the data with __str__ / __repr__
- How to use _from_proto() with a mocked protobuf message

No network calls or topic creation are performed.

Run with:
    uv run examples/topic_info.py
    python examples/topic_info.py
"""

from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services import consensus_topic_info_pb2
from hiero_sdk_python.hapi.services.basic_types_pb2 import AccountID, Key
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee


def mock_running_hash() -> bytes:
    """Generate a mock 48-byte running hash."""
    return bytes.fromhex("00" * 48)


def mock_admin_key() -> Key:
    """Create a mock admin key."""
    public_key = PrivateKey.generate_ed25519().public_key()
    key = Key()
    key.ed25519 = public_key.to_bytes_raw()
    return key


def mock_submit_key() -> Key:
    """Create a mock submit key."""
    public_key = PrivateKey.generate_ecdsa().public_key()
    key = Key()
    key.ECDSA_secp256k1 = public_key.to_bytes_raw()
    return key


def mock_custom_fee() -> CustomFixedFee:
    """Create a mock custom fee."""
    return CustomFixedFee(
        amount=100,
        denominating_token_id=None,
        fee_collector_account_id=AccountId(0, 0, 456),
        all_collectors_are_exempt=False,
    )


def mock_expiration_time() -> Timestamp:
    """Create a mock expiration timestamp."""
    timestamp = Timestamp()
    timestamp.seconds = 1767225600
    timestamp.nanos = 0
    return timestamp


def mock_auto_renew_account() -> AccountID:
    """Create a mock auto-renew account ID."""
    account_id = AccountID()
    account_id.shardNum = 0
    account_id.realmNum = 0
    account_id.accountNum = 100
    return account_id


def mock_ledger_id() -> bytes:
    """Create a mock ledger ID."""
    return bytes.fromhex("01")


def build_mock_topic_info() -> TopicInfo:
    """Manually construct a TopicInfo instance with mock data."""
    topic_info = TopicInfo(
        memo="Example topic memo",
        running_hash=mock_running_hash(),
        sequence_number=42,
        expiration_time=mock_expiration_time(),
        admin_key=mock_admin_key(),
        submit_key=mock_submit_key(),
        auto_renew_period=Duration(7776000),
        auto_renew_account=mock_auto_renew_account(),
        ledger_id=mock_ledger_id(),
        fee_schedule_key=None,
        fee_exempt_keys=None,
        custom_fees=[mock_custom_fee()],
    )
    return topic_info


def build_topic_info_from_proto() -> TopicInfo:
    """Build a TopicInfo from a mocked protobuf message using _from_proto()."""
    proto = consensus_topic_info_pb2.ConsensusTopicInfo()
    proto.memo = "Topic from protobuf"
    proto.runningHash = mock_running_hash()
    proto.sequenceNumber = 100
    proto.expirationTime.CopyFrom(mock_expiration_time())
    proto.adminKey.CopyFrom(mock_admin_key())
    proto.submitKey.CopyFrom(mock_submit_key())
    proto.autoRenewPeriod.seconds = 7776000
    proto.autoRenewAccount.CopyFrom(mock_auto_renew_account())
    proto.ledger_id = mock_ledger_id()
    proto.custom_fees.append(mock_custom_fee()._to_topic_fee_proto())

    topic_info = TopicInfo._from_proto(proto)
    return topic_info


def print_topic_info(topic: TopicInfo) -> None:
    """Display the key attributes of a TopicInfo instance."""
    print("\nTopicInfo Details:")
    print(f"  Memo: {topic.memo}")
    print(f"  Sequence Number: {topic.sequence_number}")
    print(f"  Running Hash: {topic.running_hash.hex()}")

    if topic.auto_renew_period:
        print(f"  Auto-Renew Period: {topic.auto_renew_period.seconds} seconds")

    if topic.ledger_id:
        print(f"  Ledger ID: {topic.ledger_id.hex()}")

    print(f"  Custom Fees: {len(topic.custom_fees)}")

    # Pretty-print using __str__
    print("\nUsing __str__:")
    print(topic)

    # Pretty-print using __repr__
    print("\nUsing __repr__:")
    print(repr(topic))


def main():
    """Demonstrate TopicInfo functionality."""
    print("TopicInfo Example - Demonstrating topic info construction and inspection")
    print("=" * 70)

    # Build TopicInfo directly
    print("\n1. Building TopicInfo directly:")
    topic1 = build_mock_topic_info()
    print_topic_info(topic1)

    # Build TopicInfo from protobuf
    print("\n" + "=" * 70)
    print("\n2. Building TopicInfo from protobuf:")
    topic2 = build_topic_info_from_proto()
    print_topic_info(topic2)

    print("\n" + "=" * 70)
    print("Example completed successfully!")


if __name__ == "__main__":
    main()
