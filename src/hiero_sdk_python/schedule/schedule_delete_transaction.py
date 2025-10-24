"""
ScheduleDeleteTransaction class.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.schedule_delete_pb2 import (
    ScheduleDeleteTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.transaction.transaction import Transaction


class ScheduleDeleteTransaction(Transaction):
    """
    Represents a schedule delete transaction on the network.

    This transaction deletes a schedule on the network with the specified schedule ID.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a schedule delete transaction.
    """

    def __init__(self, schedule_id: Optional[ScheduleId] = None):
        """
        Initializes a new ScheduleDeleteTransaction instance with the specified parameters.

        Args:
            schedule_id (Optional[ScheduleId]): The ID of the schedule to delete.
        """
        super().__init__()
        self.schedule_id: Optional[ScheduleId] = schedule_id
        self._default_transaction_fee = Hbar(5).to_tinybars()

    def set_schedule_id(
        self, schedule_id: Optional[ScheduleId]
    ) -> "ScheduleDeleteTransaction":
        """
        Sets the ID of the schedule to delete.

        Args:
            schedule_id (Optional[ScheduleId]): The ID of the schedule to delete.

        Returns:
            ScheduleDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.schedule_id = schedule_id
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the schedule delete transaction.

        Returns:
            ScheduleDeleteTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If schedule_id is not set.
        """
        if self.schedule_id is None:
            raise ValueError("Missing required ScheduleID")

        return ScheduleDeleteTransactionBody(scheduleID=self.schedule_id._to_proto())

    def build_transaction_body(self):
        """
        Builds the transaction body for this schedule delete transaction.

        Returns:
            TransactionBody: The built transaction body.

        Raises:
            ValueError: If schedule_id is not set.
        """
        schedule_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.scheduleDelete.CopyFrom(schedule_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this schedule delete transaction.

        Raises:
            ValueError: ScheduleDeleteTransaction cannot be scheduled.
        """
        raise ValueError("Cannot schedule a ScheduleDeleteTransaction")

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the schedule delete transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to delete a schedule.
        """
        return _Method(
            transaction_func=channel.schedule.deleteSchedule, query_func=None
        )
