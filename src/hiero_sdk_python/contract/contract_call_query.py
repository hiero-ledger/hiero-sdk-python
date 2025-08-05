# pylint: disable=too-many-positional-arguments
# pylint: disable=too-many-arguments
"""
Query to call a contract on the network.
"""

import traceback
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import (
    contract_call_local_pb2,
    query_pb2,
    response_pb2,
)
from hiero_sdk_python.query.query import Query


class ContractCallQuery(Query):
    """
    A query to call a contract on the network.

    This class constructs and executes a query to call a contract on the network.
    """

    def __init__(
        self,
        contract_id: Optional[ContractId] = None,
        gas: Optional[int] = None,
        max_result_size: Optional[int] = None,
        function_parameters: Optional[bytes] = None,
        sender: Optional[AccountId] = None,
    ) -> None:
        """
        Initializes a new ContractCallQuery instance with an optional contract_id.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to call.
            gas (Optional[int]): The gas to use for the contract call.
            max_result_size (Optional[int]): The maximum size of the result to return.
            function_parameters (Optional[bytes]): The parameters to pass to the contract function.
            sender (Optional[AccountId]): The account to use for the contract call.
        """
        super().__init__()
        self.contract_id: Optional[ContractId] = contract_id
        self.gas: Optional[int] = gas
        self.max_result_size: Optional[int] = max_result_size
        self.function_parameters: Optional[bytes] = function_parameters
        self.sender: Optional[AccountId] = sender

    def set_contract_id(self, contract_id: Optional[ContractId]) -> "ContractCallQuery":
        """
        Sets the ID of the contract to call.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to call.
        """
        self.contract_id = contract_id
        return self

    def set_gas(self, gas: Optional[int]) -> "ContractCallQuery":
        """
        Sets the gas to use for the contract call.

        Args:
            gas (Optional[int]): The gas to use for the contract call.
        """
        self.gas = gas
        return self

    def set_max_result_size(
        self, max_result_size: Optional[int]
    ) -> "ContractCallQuery":
        """
        Sets the maximum size of the result to return.

        Args:
            max_result_size (Optional[int]): The maximum size of the result to return.
        """
        self.max_result_size = max_result_size
        return self

    def set_function_parameters(
        self, function_parameters: Optional[ContractFunctionParameters | bytes]
    ) -> "ContractCallQuery":
        """
        Sets the parameters to pass to the contract function.

        Args:
            function_parameters (Optional[ContractFunctionParameters | bytes]): The parameters to
            pass to the contract function.
        """
        if isinstance(function_parameters, ContractFunctionParameters):
            self.function_parameters = function_parameters.to_bytes()
        else:
            self.function_parameters = function_parameters
        return self

    def set_function(
        self, name: str, params: Optional[ContractFunctionParameters] = None
    ) -> "ContractCallQuery":
        """
        Sets the contract function to call and the parameters to pass to it.

        Args:
            name (str): The name of the contract function to call.
            params (Optional[ContractFunctionParameters]): The parameters to pass to the function.
                If not provided, the function is called with no parameters.
        """
        if params is None:
            params = ContractFunctionParameters()

        params.function_name = name

        self.function_parameters = params.to_bytes()
        return self

    def set_sender(self, sender: Optional[AccountId]) -> "ContractCallQuery":
        """
        Sets the account to use for the contract call.

        Args:
            sender (Optional[AccountId]): The account to use for the contract call.
        """
        self.sender = sender
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a ContractCallQuery protobuf message with the appropriate header and contract ID.

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

            contract_call_query = contract_call_local_pb2.ContractCallLocalQuery(
                header=query_header,
                contractID=self.contract_id._to_proto() if self.contract_id else None,
                gas=self.gas,
                maxResultSize=self.max_result_size,
                functionParameters=self.function_parameters,
                sender_id=self.sender._to_proto() if self.sender else None,
            )
            query = query_pb2.Query()
            query.contractCallLocal.CopyFrom(contract_call_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the contract call query.

        Implements the abstract method from Query to provide the specific
        gRPC method for calling a contract.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.smart_contract.contractCallLocalMethod,
        )

    def execute(self, client: Client) -> ContractFunctionResult:
        """
        Executes the contract call query.

        Sends the query to the network and processes the response
        to return a ContractFunctionResult object.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution

        Returns:
            ContractFunctionResult: The result of the contract call

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client)

        return ContractFunctionResult._from_proto(
            response.contractCallLocal.functionResult
        )

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> contract_call_local_pb2.ContractCallLocalResponse:
        """
        Extracts the contract call response from the full response.

        Implements the abstract method from Query to extract the
        specific contract call response object.

        Args:
            response: The full response from the network

        Returns:
            The contract call response object
        """
        return response.contractCallLocal
