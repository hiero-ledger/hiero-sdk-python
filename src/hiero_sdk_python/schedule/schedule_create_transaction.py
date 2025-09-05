"""
ScheduleCreateTransaction class.
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.schedule_create_pb2 import (
    ScheduleCreateTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction


@dataclass
class ScheduleCreateParams:
    """
    Represents schedule attributes that can be set on creation.

    Attributes:
        payer_account_id (Optional[AccountId]): The account ID of the payer
            for the scheduled transaction.
        admin_key (Optional[PublicKey]): The key that can delete or sign the schedule.
        schedulable_body (Optional[SchedulableTransactionBody]): The body of the transaction
            to be scheduled.
        schedule_memo (Optional[str]): A memo to include with the schedule.
        expiration_time (Optional[Timestamp]): The time at which the schedule should expire.
        wait_for_expiry (Optional[bool]): If True, the transaction will execute only at expiration time,
            even if all required signatures are collected before then. If False or unset,
            the transaction will execute as soon as all required signatures are received.
    """

    payer_account_id: Optional[AccountId] = None
    admin_key: Optional[PublicKey] = None
    schedulable_body: Optional[SchedulableTransactionBody] = None
    schedule_memo: Optional[str] = None
    expiration_time: Optional[Timestamp] = None
    wait_for_expiry: Optional[bool] = None


class ScheduleCreateTransaction(Transaction):
    """
    Represents a schedule create transaction on the network.

    This transaction creates a new schedule on the network with the specified payer account ID,
    admin key, schedulable body, schedule memo, expiration time and wait for expiry.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a schedule create transaction.
    """

    def __init__(
        self,
        schedule_params: Optional[ScheduleCreateParams] = None,
    ):
        """
        Initializes a new ScheduleCreateTransaction instance with the specified parameters.

        Args:
            schedule_params (Optional[ScheduleCreateParams]):
                The parameters for the schedule create transaction.
        """
        super().__init__()
        schedule_params = schedule_params or ScheduleCreateParams()
        self.payer_account_id: Optional[AccountId] = schedule_params.payer_account_id
        self.admin_key: Optional[PublicKey] = schedule_params.admin_key
        self.schedulable_body: Optional[SchedulableTransactionBody] = (
            schedule_params.schedulable_body
        )
        self.schedule_memo: Optional[str] = schedule_params.schedule_memo
        self.expiration_time: Optional[Timestamp] = schedule_params.expiration_time
        self.wait_for_expiry: Optional[bool] = schedule_params.wait_for_expiry
        self._default_transaction_fee = Hbar(5).to_tinybars()

    def _set_schedulable_body(
        self, schedulable_body: Optional[SchedulableTransactionBody]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the schedulable body for this schedule create transaction.

        Args:
            schedulable_body (Optional[SchedulableTransactionBody]):
                The body of the schedulable transaction.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.schedulable_body = schedulable_body
        return self

    def set_scheduled_transaction(
        self, transaction: "Transaction"
    ) -> "ScheduleCreateTransaction":
        """
        Sets the scheduled transaction for this schedule create transaction.

        Args:
            transaction (Transaction):
                The transaction to schedule.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.schedulable_body = transaction.build_scheduled_body()

        return self

    def set_schedule_memo(
        self, schedule_memo: Optional[str]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the schedule memo for this schedule create transaction.

        Args:
            schedule_memo (Optional[str]): The schedule memo for the schedule.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.schedule_memo = schedule_memo
        return self

    def set_payer_account_id(
        self, payer_account_id: Optional[AccountId]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the payer account ID for this schedule create transaction.

        Args:
            payer_account_id (Optional[AccountId]): The payer account ID for the schedule.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.payer_account_id = payer_account_id
        return self

    def set_expiration_time(
        self, expiration_time: Optional[Timestamp]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the expiration time for this schedule create transaction.

        Args:
            expiration_time (Optional[Timestamp]): The expiration time for the schedule.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def set_wait_for_expiry(
        self, wait_for_expiry: Optional[bool]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the wait for expiry for this schedule create transaction.

        Args:
            wait_for_expiry (Optional[bool]): Whether to wait for the schedule to expire.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.wait_for_expiry = wait_for_expiry
        return self

    def set_admin_key(
        self, admin_key: Optional[PublicKey]
    ) -> "ScheduleCreateTransaction":
        """
        Sets the admin key for this schedule create transaction.

        Args:
            admin_key (Optional[PublicKey]): The admin key for the schedule.

        Returns:
            ScheduleCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the schedule create transaction.

        Returns:
            ScheduleCreateTransactionBody: The protobuf body for this transaction.
        """
        return ScheduleCreateTransactionBody(
            wait_for_expiry=self.wait_for_expiry,
            memo=self.schedule_memo,
            adminKey=self.admin_key._to_proto() if self.admin_key else None,
            scheduledTransactionBody=self.schedulable_body,
            expiration_time=(
                self.expiration_time._to_protobuf() if self.expiration_time else None
            ),
            payerAccountID=(
                self.payer_account_id._to_proto() if self.payer_account_id else None
            ),
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this schedule create transaction.

        Returns:
            TransactionBody: The built transaction body.
        """
        schedule_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.scheduleCreate.CopyFrom(schedule_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this schedule create transaction.

        Raises:
            ValueError: ScheduleCreateTransaction cannot be scheduled.
        """
        raise ValueError("Cannot schedule a ScheduleCreateTransaction")

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the schedule create transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to create a schedule.
        """
        return _Method(transaction_func=channel.schedule.createSchedule, query_func=None)
