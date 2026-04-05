"""
This module provides the `TopicInfo` class for representing consensus topic
metadata on the Hedera network using the Hiero SDK.

It handles constructing the object from a protobuf message, formatting
optional fields, and providing a readable string representation of the
topic state.
"""

from __future__ import annotations

from datetime import UTC, datetime

from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hapi.services import consensus_topic_info_pb2
from hiero_sdk_python.hapi.services.basic_types_pb2 import AccountID, Key
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
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
        expiration_time: Timestamp | None,
        admin_key: Key | None,
        submit_key: Key | None,
        auto_renew_period: Duration | None,
        auto_renew_account: AccountID | None,
        ledger_id: bytes | None,
        fee_schedule_key: PublicKey | None,
        fee_exempt_keys: list[PublicKey] | None,
        custom_fees: list[CustomFixedFee] | None,
    ) -> None:
        """
        Initializes a new instance of the TopicInfo class.

        Args:
            memo (str): The memo associated with the topic.
            running_hash (bytes): The current running hash of the topic.
            sequence_number (int): The sequence number of the topic.
            expiration_time (Timestamp, optional): The expiration time of the topic.
            admin_key (Key, optional): The admin key for the topic.
            submit_key (Key, optional): The submit key for the topic.
            auto_renew_period (Duration, optional): The auto-renew period for the topic.
            auto_renew_account (AccountID, optional): The account ID for auto-renewal.
            ledger_id (bytes, optional): The ledger ID associated with the topic.
            fee_schedule_key (PublicKey): The fee schedule key for the topic.
            fee_exempt_keys (list[PublicKey]): The fee exempt keys for the topic.
            custom_fees (list[CustomFixedFee]): The custom fees for the topic.
        """
        self.memo: str = memo
        self.running_hash: bytes = running_hash
        self.sequence_number: int = sequence_number
        self.expiration_time: Timestamp | None = expiration_time
        self.admin_key: Key | None = admin_key
        self.submit_key: Key | None = submit_key
        self.auto_renew_period: Duration | None = auto_renew_period
        self.auto_renew_account: AccountID | None = auto_renew_account
        self.ledger_id: bytes | None = ledger_id
        self.fee_schedule_key: PublicKey = fee_schedule_key
        self.fee_exempt_keys: list[PublicKey] = list(fee_exempt_keys) if fee_exempt_keys is not None else []
        self.custom_fees: list[CustomFixedFee] = list(custom_fees) if custom_fees is not None else []

    @classmethod
    def _from_proto(cls, topic_info_proto: consensus_topic_info_pb2.ConsensusTopicInfo) -> TopicInfo:
        """
        Constructs a TopicInfo object from a protobuf ConsensusTopicInfo message.

        Args:
            topic_info_proto (ConsensusTopicInfo): The protobuf message.

        Returns:
            TopicInfo: The constructed TopicInfo object.
        """
        return cls(
            memo=topic_info_proto.memo,
            running_hash=topic_info_proto.runningHash,
            sequence_number=topic_info_proto.sequenceNumber,
            expiration_time=(topic_info_proto.expirationTime if topic_info_proto.HasField("expirationTime") else None),
            admin_key=(topic_info_proto.adminKey if topic_info_proto.HasField("adminKey") else None),
            submit_key=(topic_info_proto.submitKey if topic_info_proto.HasField("submitKey") else None),
            auto_renew_period=(
                Duration._from_proto(proto=topic_info_proto.autoRenewPeriod)
                if topic_info_proto.HasField("autoRenewPeriod")
                else None
            ),
            auto_renew_account=(
                topic_info_proto.autoRenewAccount if topic_info_proto.HasField("autoRenewAccount") else None
            ),
            ledger_id=getattr(topic_info_proto, "ledger_id", None),
            fee_schedule_key=(
                PublicKey._from_proto(topic_info_proto.fee_schedule_key)
                if topic_info_proto.HasField("fee_schedule_key")
                else None
            ),
            fee_exempt_keys=[PublicKey._from_proto(key) for key in topic_info_proto.fee_exempt_key_list],
            custom_fees=[CustomFixedFee._from_proto(fee) for fee in topic_info_proto.custom_fees],
        )

    def __repr__(self) -> str:
        """
        If you print the object with `repr(topic_info)`, you'll see this output.

        Returns:
            str: The string representation.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the TopicInfo in a multi-line, user-friendly style.

        Returns:
            str: A nicely formatted string representation of the topic.
        """
        exp_dt: str | None = None
        if self.expiration_time and hasattr(self.expiration_time, "seconds"):
            utc_dt = datetime.fromtimestamp(self.expiration_time.seconds, tz=UTC)
            exp_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

        running_hash_str: str | None = f"0x{self.running_hash.hex()}" if self.running_hash else "None"

        # shows 0x{hex} when present, or "None" as a string when absent (previously could be 0xNone)
        ledger_id_hex: str | None = None
        if self.ledger_id and isinstance(self.ledger_id, (bytes, bytearray)):
            ledger_id_hex = self.ledger_id.hex()
        ledger_id_str = f"0x{ledger_id_hex}" if ledger_id_hex else "None"

        # extracts and displays just the seconds value (e.g., 7776000) from Duration
        auto_renew_seconds = self.auto_renew_period.seconds if self.auto_renew_period else None

        if self.auto_renew_account is None:
            auto_renew_account_str = "None"
        elif hasattr(self.auto_renew_account, "shardNum"):
            # Protobuf AccountID -displays AccountId(shard=X, realm=Y, account=Z) format
            auto_renew_account_str = (
                f"AccountId(shard={self.auto_renew_account.shardNum}, "
                f"realm={self.auto_renew_account.realmNum}, "
                f"account={self.auto_renew_account.accountNum})"
            )
        else:
            auto_renew_account_str = str(self.auto_renew_account)

        fee_exempt_keys_formatted = [format_key(key) for key in self.fee_exempt_keys]

        return (
            "TopicInfo(\n"
            f"  memo='{self.memo}',\n"
            f"  running_hash={running_hash_str},\n"
            f"  sequence_number={self.sequence_number},\n"
            f"  expiration_time={exp_dt},\n"
            f"  admin_key={format_key(self.admin_key)},\n"
            f"  submit_key={format_key(self.submit_key)},\n"
            f"  auto_renew_period={auto_renew_seconds},\n"
            f"  auto_renew_account={auto_renew_account_str},\n"
            f"  ledger_id={ledger_id_str},\n"
            f"  fee_schedule_key={format_key(self.fee_schedule_key)},\n"
            f"  fee_exempt_keys={fee_exempt_keys_formatted},\n"
            f"  custom_fees={self.custom_fees},\n"
            ")"
        )
