"""
This module provides the `TopicInfo` class for representing consensus topic
metadata on the Hedera network using the Hiero SDK.

It handles constructing the object from a protobuf message, formatting
optional fields, and providing a readable string representation of the
topic state.
"""
from datetime import datetime
from typing import Optional
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key, AccountID
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp
from hiero_sdk_python.hapi.services import consensus_topic_info_pb2
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.utils.key_format import format_key


class TopicInfo:
    """
        Represents consensus topic information on the Hedera network.

        It wraps the `ConsensusTopicInfo` protobuf message, exposing attributes
        such as memo, running hash, sequence number, expiration time, admin key,
        submit key, auto-renewal configuration, and ledger ID.
    """
    def __init__(
            self,
            memo: str,
            running_hash: bytes,
            sequence_number: int,
            expiration_time: Timestamp,
            admin_key: Optional[Key],
            submit_key: Optional[Key],
            auto_renew_period: Optional[Duration],
            auto_renew_account: Optional[AccountID],
            ledger_id: Optional[bytes],

    ) -> None:
        """
        Initializes a new instance of the TopicInfo class.
        Args:
            memo (str): The memo associated with the topic.
            running_hash (bytes): The current running hash of the topic.
            sequence_number (int): The sequence number of the topic.
            expiration_time (Timestamp): The expiration time of the topic.
            admin_key (Key): The admin key for the topic.
            submit_key (Key): The submit key for the topic.
            auto_renew_period (Duration): The auto-renew period for the topic.
            auto_renew_account (AccountID): The account ID for auto-renewal.
            ledger_id (bytes): The ledger ID associated with the topic.
        """
        self.memo: str = memo
        self.running_hash: bytes = running_hash
        self.sequence_number: int = sequence_number
        self.expiration_time: Timestamp = expiration_time
        self.admin_key: Key = admin_key
        self.submit_key: Key = submit_key
        self.auto_renew_period: Duration = auto_renew_period
        self.auto_renew_account: AccountID = auto_renew_account
        self.ledger_id: bytes = ledger_id

    @classmethod
    def _from_proto(
            cls,
            topic_info_proto: consensus_topic_info_pb2.ConsensusTopicInfo
    ) -> "TopicInfo":
        """
        Constructs a TopicInfo object from a protobuf ConsensusTopicInfo message.
        """
        return cls(
            memo=topic_info_proto.memo,
            running_hash=topic_info_proto.runningHash,
            sequence_number=topic_info_proto.sequenceNumber,
            expiration_time=(
                topic_info_proto.expirationTime
                if topic_info_proto.HasField("expirationTime") else None
            ),
            admin_key=(
                topic_info_proto.adminKey
                if topic_info_proto.HasField("adminKey") else None
            ),
            submit_key=(
                topic_info_proto.submitKey
                if topic_info_proto.HasField("submitKey") else None
            ),
            auto_renew_period=(
                Duration._from_proto(proto=topic_info_proto.autoRenewPeriod)
                if topic_info_proto.HasField("autoRenewPeriod") else None
            ),
            auto_renew_account=(
                topic_info_proto.autoRenewAccount
                if topic_info_proto.HasField("autoRenewAccount") else None
            ),
            ledger_id=getattr(topic_info_proto, "ledger_id", None),
            # fallback if the field doesn't exist
        )

    def __repr__(self) -> str:
        """
        If you print the object with `repr(topic_info)`, you'll see this output.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the TopicInfo in a multi-line, user-friendly style.
        """

        exp_dt: datetime = None
        if self.expiration_time and hasattr(self.expiration_time, "seconds"):
            exp_dt = datetime.fromtimestamp(self.expiration_time.seconds)

        running_hash_hex: str = self.running_hash.hex() if self.running_hash else None
        ledger_id_hex: Optional[str] = (
            self.ledger_id.hex() if isinstance(self.ledger_id, (bytes, bytearray)) else None
        )

        return (
            "TopicInfo(\n"
            f"  memo='{self.memo}',\n"
            f"  running_hash=0x{running_hash_hex},\n"
            f"  sequence_number={self.sequence_number},\n"
            f"  expiration_time={exp_dt},\n"
            f"  admin_key={format_key(self.admin_key)},\n"
            f"  submit_key={format_key(self.submit_key)},\n"
            f"  auto_renew_period={self.auto_renew_period.seconds},\n"
            f"  auto_renew_account={self.auto_renew_account},\n"
            f"  ledger_id=0x{ledger_id_hex}\n"
            ")"
        )
