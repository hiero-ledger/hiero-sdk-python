from datetime import datetime
from hiero_sdk_python.hapi.services.basic_types_pb2 import Key, AccountID
from hiero_sdk_python.hapi.services.timestamp_pb2 import Timestamp
from hiero_sdk_python import Duration
from hiero_sdk_python.utils.key_format import format_key

class TopicInfo:
    def __init__(
        self,
        memo: str,
        running_hash: bytes,
        sequence_number: int,
        expiration_time: Timestamp,
        admin_key: Key,
        submit_key: Key,
        auto_renew_period: Duration,
        auto_renew_account: AccountID,
        ledger_id: bytes,
    ):
        self.memo = memo
        self.running_hash = running_hash
        self.sequence_number = sequence_number
        self.expiration_time = expiration_time
        self.admin_key = admin_key
        self.submit_key = submit_key
        self.auto_renew_period: Duration = auto_renew_period
        self.auto_renew_account = auto_renew_account
        self.ledger_id = ledger_id

    @classmethod
    def from_proto(cls, topic_info_proto):
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
                Duration.from_proto(proto=topic_info_proto.autoRenewPeriod)
                if topic_info_proto.HasField("autoRenewPeriod") else None
            ),
            auto_renew_account=(
                topic_info_proto.autoRenewAccount 
                if topic_info_proto.HasField("autoRenewAccount") else None
            ),
            ledger_id=getattr(topic_info_proto, "ledger_id", None),  # fallback if the field doesn't exist
        )

    def __repr__(self):
        """
        If you print the object with `repr(topic_info)`, you'll see this output.
        """
        return self.__str__()

    def __str__(self):
        """
        Pretty-print the TopicInfo in a multi-line, user-friendly style.
        """

        exp_dt = None
        if self.expiration_time and hasattr(self.expiration_time, "seconds"):
            exp_dt = datetime.fromtimestamp(self.expiration_time.seconds)
            
        running_hash_hex = self.running_hash.hex() if self.running_hash else None

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
            f"  ledger_id={self.ledger_id}\n"
            ")"
        )
