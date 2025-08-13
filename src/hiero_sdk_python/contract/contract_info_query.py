"""
Query to get information about a contract on the network.
"""

import traceback
from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_info import ContractInfo
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import (
    contract_get_info_pb2,
    query_pb2,
    response_pb2,
)
from hiero_sdk_python.hapi.services.contract_get_info_pb2 import ContractGetInfoResponse
from hiero_sdk_python.query.query import Query


class ContractInfoQuery(Query):
    """
    A query to retrieve information about a specific Contract.

    This class constructs and executes a query to retrieve information
    about a contract on the network, including the contract's properties and settings.

    """

    def __init__(self, contract_id: Optional[ContractId] = None) -> None:
        """
        Initializes a new ContractInfoQuery instance with an optional contract_id.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to query.
        """
        super().__init__()
        self.contract_id: Optional[ContractId] = contract_id

    def set_contract_id(self, contract_id: Optional[ContractId]) -> "ContractInfoQuery":
        """
        Sets the ID of the contract to query.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract.
        """
        self.contract_id = contract_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a ContractGetInfoQuery protobuf message with the
        appropriate header and contract ID.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the contract ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.contract_id:
                raise ValueError("Contract ID must be set before making the request.")

            query_header = self._make_request_header()

            contract_info_query = contract_get_info_pb2.ContractGetInfoQuery()
            contract_info_query.header.CopyFrom(query_header)
            contract_info_query.contractID.CopyFrom(self.contract_id._to_proto())

            query = query_pb2.Query()
            query.contractGetInfo.CopyFrom(contract_info_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the contract info query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting contract information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None, query_func=channel.smart_contract.getContractInfo
        )

    def execute(self, client: Client) -> ContractInfo:
        """
        Executes the contract info query.

        Sends the query to the network and processes the response
        to return a ContractInfo object.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            ContractInfo: The contract info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client)

        return ContractInfo._from_proto(response.contractGetInfo.contractInfo)

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> ContractGetInfoResponse.ContractInfo:
        """
        Extracts the contract info response from the full response.

        Implements the abstract method from Query to extract the
        specific contract info response object.

        Args:
            response: The full response from the network

        Returns:
            The contract get info response object
        """
        return response.contractGetInfo
