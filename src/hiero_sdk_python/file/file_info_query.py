import traceback
from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info import FileInfo
from hiero_sdk_python.hapi.services import file_get_info_pb2, query_pb2, response_pb2
from hiero_sdk_python.hapi.services.file_get_info_pb2 import FileGetInfoResponse
from hiero_sdk_python.query.query import Query
from hiero_sdk_python import ResponseCode as _Status 


class FileInfoQuery(Query):
    """
    A query to retrieve information about a specific File.

    This class constructs and executes a query to retrieve information
    about a file on the network, including the file's properties and settings.
    """

    def __init__(self, file_id: Optional[FileId] = None) -> None:
        """
        Initializes a new FileInfoQuery instance with an optional file_id.

        Args:
            file_id (Optional[FileId], optional): The ID of the file to query.
        """
        super().__init__()
        self.file_id: Optional[FileId] = file_id

    def set_file_id(self, file_id: Optional[FileId]) -> "FileInfoQuery":
        """
        Sets the ID of the file to query.

        Args:
            file_id (Optional[FileId]): The ID of the file.

        Returns:
            FileInfoQuery: Returns self for method chaining.
        """
        self.file_id = file_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a FileGetInfoQuery protobuf message with the
        appropriate header and file ID.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the file ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.file_id:
                raise ValueError("File ID must be set before making the request.")

            query_header = self._make_request_header()

            file_info_query = file_get_info_pb2.FileGetInfoQuery()
            file_info_query.header.CopyFrom(query_header)
            file_info_query.fileID.CopyFrom(self.file_id._to_proto())

            query = query_pb2.Query()
            query.fileGetInfo.CopyFrom(file_info_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the file info query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting file information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(transaction_func=None, query_func=channel.file.getFileInfo)

    def _get_response_header(self, response):
        """
        Gets the response header from the query response.

        Returns:
            The response header object.
        """
        return response.fileGetInfo.header

    def execute(self, client: Client) -> FileInfo:
        """
        Executes the file info query.

        Sends the query to the Hedera network and processes the response
        to return a FileInfo object.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            FileInfo: The file info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error.
        """
        self._before_execute(client)
        response = self._execute(client)

        # The get file info query returns INVALID_FILE_ID in the response
        # body's header, not in the top-level precheck header.
        response_header = self._get_response_header(response)

        # Check the status from the inner header
        if response_header.nodeTransactionPrecheckCode == _Status.INVALID_FILE_ID:
            raise PrecheckError(
                f"Query failed precheck with status: {_Status(response_header.nodeTransactionPrecheckCode).name}",
                status=_Status(response_header.nodeTransactionPrecheckCode),
            )

        return FileInfo._from_proto(response.fileGetInfo.fileInfo)

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> FileGetInfoResponse.FileInfo:
        """
        Extracts the file info response from the full response.

        Implements the abstract method from Query to extract the
        specific file info response object.

        Args:
            response: The full response from the network

        Returns:
            The file get info response object
        """
        return response.fileGetInfo