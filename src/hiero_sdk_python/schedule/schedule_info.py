"""
ScheduleInfo class
"""

import datetime
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hapi.services.basic_types_pb2 import KeyList as KeyListProto
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.schedule_get_info_pb2 import (
    ScheduleInfo as ScheduleInfoProto,
)
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_id import TransactionId


@dataclass()
class ScheduleInfo:
    """
    Information about a scheduled transaction on the network.

    Attributes:
        schedule_id (Optional[ScheduleId]): The unique identifier for the schedule.
        creator_account_id (Optional[AccountId]): The account that created the schedule.
        payer_account_id (Optional[AccountId]): The account responsible for paying
            for the scheduled transaction.
        deleted_at (Optional[Timestamp]): The time at which the schedule was deleted.
        executed_at (Optional[Timestamp]): The time at which the scheduled transaction was executed.
        expiration_time (Optional[Timestamp]): The time at which the schedule will expire.
        scheduled_transaction_id (Optional[TransactionId]):
            The transaction ID of the scheduled transaction.
        scheduled_transaction_body (Optional[SchedulableTransactionBody]):
            The body of the scheduled transaction.
        schedule_memo (Optional[str]): The memo associated with the schedule.
        admin_key (Optional[PublicKey]): The key that can delete or update the schedule.
        signers (list[PublicKey]): The list of public keys that have signed the schedule.
        ledger_id (Optional[bytes]): The ID of the ledger this schedule exists in.
        wait_for_expiry (Optional[bool]): Whether the schedule is set to wait for expiry.
    """

    schedule_id: Optional[ScheduleId] = None
    creator_account_id: Optional[AccountId] = None
    payer_account_id: Optional[AccountId] = None
    deleted_at: Optional[Timestamp] = None
    executed_at: Optional[Timestamp] = None
    expiration_time: Optional[Timestamp] = None
    scheduled_transaction_id: Optional[TransactionId] = None
    scheduled_transaction_body: Optional[SchedulableTransactionBody] = None
    schedule_memo: Optional[str] = None
    admin_key: Optional[PublicKey] = None
    signers: list[PublicKey] = field(default_factory=list)
    ledger_id: Optional[bytes] = None
    wait_for_expiry: Optional[bool] = None

    @classmethod
    def _from_proto(cls, proto: ScheduleInfoProto) -> "ScheduleInfo":
        """
        Creates a ScheduleInfo instance from its protobuf representation.

        Args:
            proto (ScheduleGetInfoResponse.scheduleInfo):
                The protobuf ScheduleInfo object to convert.

        Returns:
            ScheduleInfo: A new ScheduleInfo instance.
        """
        if proto is None:
            raise ValueError("Schedule info proto is None")

        return cls(
            schedule_id=(
                cls._from_proto_field(proto, "scheduleID", ScheduleId._from_proto)
            ),
            creator_account_id=(
                cls._from_proto_field(proto, "creatorAccountID", AccountId._from_proto)
            ),
            payer_account_id=(
                cls._from_proto_field(proto, "payerAccountID", AccountId._from_proto)
            ),
            deleted_at=(
                cls._from_proto_field(proto, "deletion_time", Timestamp._from_protobuf)
            ),
            executed_at=(
                cls._from_proto_field(proto, "execution_time", Timestamp._from_protobuf)
            ),
            expiration_time=(
                cls._from_proto_field(proto, "expirationTime", Timestamp._from_protobuf)
            ),
            scheduled_transaction_id=(
                cls._from_proto_field(
                    proto, "scheduledTransactionID", TransactionId._from_proto
                )
            ),
            scheduled_transaction_body=proto.scheduledTransactionBody,
            schedule_memo=proto.memo,
            admin_key=(cls._from_proto_field(proto, "adminKey", PublicKey._from_proto)),
            signers=[PublicKey._from_proto(key) for key in proto.signers.keys],
            ledger_id=proto.ledger_id,
            wait_for_expiry=proto.wait_for_expiry,
        )

    def _to_proto(self) -> ScheduleInfoProto:
        """
        Converts this ScheduleInfo instance to its protobuf representation.

        Returns:
            ScheduleInfoProto: The protobuf representation of this ScheduleInfo.
        """
        return ScheduleInfoProto(
            scheduleID=self._convert_to_proto(self.schedule_id, ScheduleId._to_proto),
            creatorAccountID=(
                self._convert_to_proto(self.creator_account_id, AccountId._to_proto)
            ),
            payerAccountID=(
                self._convert_to_proto(self.payer_account_id, AccountId._to_proto)
            ),
            deletion_time=self._convert_to_proto(self.deleted_at, Timestamp._to_protobuf),
            execution_time=(
                self._convert_to_proto(self.executed_at, Timestamp._to_protobuf)
            ),
            expirationTime=(
                self._convert_to_proto(self.expiration_time, Timestamp._to_protobuf)
            ),
            scheduledTransactionID=(
                self._convert_to_proto(
                    self.scheduled_transaction_id, TransactionId._to_proto
                )
            ),
            scheduledTransactionBody=self.scheduled_transaction_body,
            memo=self.schedule_memo,
            adminKey=self._convert_to_proto(self.admin_key, PublicKey._to_proto),
            signers=KeyListProto(
                keys=[
                    self._convert_to_proto(key, PublicKey._to_proto)
                    for key in self.signers or []
                ]
            ),
            ledger_id=self.ledger_id,
            wait_for_expiry=self.wait_for_expiry,
        )

    def __repr__(self) -> str:
        """
        Returns a string representation of the ScheduleInfo object.

        Returns:
            str: A string representation of the ScheduleInfo object.
        """
        return self.__str__()

    def __str__(self) -> str:
        """
        Pretty-print the ScheduleInfo.
        """

        exp_dt = (
            datetime.datetime.fromtimestamp(self.expiration_time.seconds)
            if self.expiration_time and hasattr(self.expiration_time, "seconds")
            else self.expiration_time
        )

        # Format signers as readable strings
        signers_str = [key.to_string() for key in self.signers] if self.signers else []

        # Format ledger_id as hex if it's bytes
        ledger_id_display = (
            f"0x{self.ledger_id.hex()}"
            if isinstance(self.ledger_id, (bytes, bytearray))
            else self.ledger_id
        )

        return (
            "ScheduleInfo(\n"
            f"  schedule_id={self.schedule_id},\n"
            f"  creator_account_id={self.creator_account_id},\n"
            f"  payer_account_id={self.payer_account_id},\n"
            f"  deleted_at={self.deleted_at},\n"
            f"  executed_at={self.executed_at},\n"
            f"  expiration_time={exp_dt},\n"
            f"  scheduled_transaction_id={self.scheduled_transaction_id},\n"
            f"  scheduled_transaction_body={self.scheduled_transaction_body},\n"
            f"  schedule_memo='{self.schedule_memo}',\n"
            f"  admin_key={self.admin_key.to_string() if self.admin_key else None},\n"
            f"  signers={signers_str},\n"
            f"  ledger_id={ledger_id_display},\n"
            f"  wait_for_expiry={self.wait_for_expiry}\n"
            ")"
        )

    @classmethod
    def _from_proto_field(
        cls,
        proto: ScheduleInfoProto,
        field_name: str,
        from_proto: Callable,
    ):
        """
        Helper to extract and convert proto fields to a python object.

        Args:
            proto: The protobuf object to extract the field from.
            field_name: The name of the field to extract.
            from_proto: A callable to convert the field from protobuf to a python object.

        Returns:
            The converted field value or None if the field doesn't exist.
        """
        if not proto.HasField(field_name):
            return None

        value = getattr(proto, field_name)
        return from_proto(value)

    def _convert_to_proto(self, obj: Optional[Any], to_proto: Callable) -> Any:
        """Convert object to proto if it exists, otherwise return None"""
        return to_proto(obj) if obj else None
