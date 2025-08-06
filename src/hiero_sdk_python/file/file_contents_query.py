"""
Query to get the contents of a file on the network.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import (
    file_get_contents_pb2,
    query_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.file_get_contents_pb2 import FileGetContentsResponse
from hiero_sdk_python.query.query import Query


class FileContentsQuery(Query):
    """
    A query to retrieve the contents of a specific File.

    This class constructs and executes a query to retrieve the contents
    of a file on the network.

    """

    def __init__(self, file_id: Optional[FileId] = None) -> None:
        """
        Initializes a new FileContentsQuery instance with an optional file_id.

        Args:
            file_id (Optional[FileId], optional): The ID of the file to query.
        """
        super().__init__()
        self.file_id = file_id

    def set_file_id(self, file_id: Optional[FileId]) -> "FileContentsQuery":
        """
        Sets the ID of the file to query.

        Args:
            file_id (Optional[FileId]): The ID of the file.

        Returns:
            FileContentsQuery: Returns self for method chaining.
        """
        self.file_id = file_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a FileGetContentsQuery protobuf message with the
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

            file_contents_query = file_get_contents_pb2.FileGetContentsQuery()
            file_contents_query.header.CopyFrom(query_header)
            file_contents_query.fileID.CopyFrom(self.file_id._to_proto())

            query = query_pb2.Query()
            query.fileGetContents.CopyFrom(file_contents_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the file contents query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting file contents.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(transaction_func=None, query_func=channel.file.getFileContent)

    def execute(self, client: Client) -> str:
        """
        Executes the file contents query.

        Sends the query to the Hedera network and processes the response
        to return the file contents.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            str: The contents of the file from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client)

        return response.fileGetContents.fileContents.contents

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> FileGetContentsResponse:
        """
        Extracts the file contents response from the full response.

        Implements the abstract method from Query to extract the
        specific file contents response object.

        Args:
            response: The full response from the network

        Returns:
            The file get contents response object
        """
        return response.fileGetContents
