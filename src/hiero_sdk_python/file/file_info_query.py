"""
Query to get information about a file on the network.
"""

import traceback
from typing import Optional

# Important: Add these imports
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python import ResponseCode as _Status

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info import FileInfo
from hiero_sdk_python.hapi.services import file_get_info_pb2, query_pb2, response_pb2
from hiero_sdk_python.hapi.services.file_get_info_pb2 import FileGetInfoResponse
from hiero_sdk_python.query.query import Query


class FileInfoQuery(Query):
    """
    A query to retrieve information about a specific File.
    """

    def __init__(self, file_id: Optional[FileId] = None) -> None:
        """
        Initializes a new FileInfoQuery instance.
        """
        super().__init__()
        self.file_id: Optional[FileId] = file_id

    def set_file_id(self, file_id: Optional[FileId]) -> "FileInfoQuery":
        """
        Sets the ID of the file to query.
        """
        self.file_id = file_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.
        """
        if not self.file_id:
            raise ValueError("File ID must be set before making the request.")

        query_header = self._make_request_header()

        file_info_query = file_get_info_pb2.FileGetInfoQuery()
        file_info_query.header.CopyFrom(query_header)
        file_info_query.fileID.CopyFrom(self.file_id._to_proto())

        query = query_pb2.Query()
        query.fileGetInfo.CopyFrom(file_info_query)

        return query

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the file info query.
        """
        return _Method(transaction_func=None, query_func=channel.file.getFileInfo)

    def _get_response_header(self, response: response_pb2.Response):
        """
        Gets the header from the query's response body.
        """
        return response.fileGetInfo.header

    def execute(self, client: Client) -> FileInfo:
        """
        Executes the file info query.
        """
        self._before_execute(client)
        response = self._execute(client)

        response_header = self._get_response_header(response)
        
        # Check the status from the inner header.
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
        """
        return response.fileGetInfo