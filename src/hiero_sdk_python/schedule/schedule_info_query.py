"""
Query to get information about a schedule on the network.
"""

import traceback
from typing import Optional, Union

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import query_pb2, response_pb2, schedule_get_info_pb2
from hiero_sdk_python.hapi.services.schedule_get_info_pb2 import ScheduleGetInfoResponse
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.schedule.schedule_id import ScheduleId
from hiero_sdk_python.schedule.schedule_info import ScheduleInfo


class ScheduleInfoQuery(Query):
    """
    A query to retrieve information about a specific Schedule.

    This class constructs and executes a query to retrieve information
    about a schedule on the network, including the schedule's properties and settings.
    """

    def __init__(self, schedule_id: Optional[ScheduleId] = None) -> None:
        """
        Initializes a new ScheduleInfoQuery instance with an optional schedule_id.

        Args:
            schedule_id (Optional[ScheduleId]): The ID of the schedule to query.
        """
        super().__init__()
        self.schedule_id: Optional[ScheduleId] = schedule_id

    def set_schedule_id(self, schedule_id: Optional[ScheduleId]) -> "ScheduleInfoQuery":
        """
        Sets the ID of the schedule to query.

        Args:
            schedule_id (Optional[ScheduleId]): The ID of the schedule.
        """
        self.schedule_id = schedule_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a ScheduleGetInfoQuery protobuf message with the
        appropriate header and schedule ID.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the schedule ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.schedule_id:
                raise ValueError("Schedule ID must be set before making the request.")

            query_header = self._make_request_header()

            schedule_info_query = schedule_get_info_pb2.ScheduleGetInfoQuery()
            schedule_info_query.header.CopyFrom(query_header)
            schedule_info_query.scheduleID.CopyFrom(self.schedule_id._to_proto())

            query = query_pb2.Query()
            query.scheduleGetInfo.CopyFrom(schedule_info_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the schedule info query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting schedule information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(transaction_func=None, query_func=channel.schedule.getScheduleInfo)

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> ScheduleInfo:
        """
        Executes the schedule info query.

        Sends the query to the network and processes the response
        to return a ScheduleInfo object.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            ScheduleInfo: The schedule info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        return ScheduleInfo._from_proto(response.scheduleGetInfo.scheduleInfo)

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> ScheduleGetInfoResponse:
        """
        Extracts the schedule info response from the full response.

        Implements the abstract method from Query to extract the
        specific schedule info response object.

        Args:
            response: The full response from the network

        Returns:
            The schedule get info response object
        """
        return response.scheduleGetInfo
