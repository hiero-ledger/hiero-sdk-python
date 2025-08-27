"""
ContractExecuteTransaction class.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.contract_call_pb2 import ContractCallTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction


class ContractExecuteTransaction(Transaction):
    """
    A transaction that executes a smart contract function.

    This transaction can be used to execute a function on an existing smart contract
    deployed on the network. You can specify the contract ID, gas limit, amount of hbar
    to send, and any function parameters required for the contract call.
    """

    def __init__(
        self,
        contract_id: Optional[ContractId] = None,
        gas: Optional[int] = None,
        amount: Optional[int | Hbar] = None,
        function_parameters: Optional[bytes] = None,
    ):
        """
        Initializes a new ContractExecuteTransaction instance.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to execute.
            gas (Optional[int]): The gas to use for the contract execution.
            amount (Optional[int | Hbar]): The amount of hbar to send with the call.
                You may pass an integer (tinybars) or an Hbar object.
                The value is always stored internally as an integer (tinybars).
            function_parameters (Optional[bytes]): The parameters to pass to the contract function.
        """
        super().__init__()
        self.contract_id: Optional[ContractId] = contract_id
        self.gas: Optional[int] = gas
        self.amount: Optional[int] = (
            amount.to_tinybars() if isinstance(amount, Hbar) else amount
        )
        self.function_parameters: Optional[bytes] = function_parameters

    def set_contract_id(
        self, contract_id: Optional[ContractId]
    ) -> "ContractExecuteTransaction":
        """
        Sets the contract ID for the transaction.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to execute.
        """
        self._require_not_frozen()
        self.contract_id = contract_id
        return self

    def set_gas(self, gas: Optional[int]) -> "ContractExecuteTransaction":
        """
        Sets the gas for the transaction.

        Args:
            gas (Optional[int]): The gas to use for the contract execution.
        """
        self._require_not_frozen()
        self.gas = gas
        return self

    def set_payable_amount(
        self, amount: Optional[int | Hbar]
    ) -> "ContractExecuteTransaction":
        """
        Sets the amount of HBAR to send with the call.

        Args:
            amount (Optional[int | Hbar]): The amount of HBAR to send with the call.
                You may pass an integer (tinybars) or an Hbar object.
                The value is always stored internally as an integer (tinybars).
        """
        self._require_not_frozen()
        self.amount = amount.to_tinybars() if isinstance(amount, Hbar) else amount
        return self

    def set_function_parameters(
        self, function_parameters: Optional[ContractFunctionParameters | bytes]
    ) -> "ContractExecuteTransaction":
        """
        Sets the parameters to pass to the contract function.

        Args:
            function_parameters (Optional[ContractFunctionParameters | bytes]): The parameters to
            pass to the contract function.
        """
        self._require_not_frozen()
        if isinstance(function_parameters, ContractFunctionParameters):
            self.function_parameters = function_parameters.to_bytes()
        else:
            self.function_parameters = function_parameters
        return self

    def set_function(
        self, name: str, params: Optional[ContractFunctionParameters] = None
    ) -> "ContractExecuteTransaction":
        """
        Sets the function to call and the parameters to pass to it.

        Args:
            name (str): The name of the function to call.
            params (Optional[ContractFunctionParameters]): The parameters to pass to the function.
        """
        self._require_not_frozen()
        if params is None:
            params = ContractFunctionParameters()

        params.function_name = name

        self.function_parameters = params.to_bytes()
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the contract execute transaction.

        Returns:
            ContractCallTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If contract_id is not set.
        """
        if self.contract_id is None:
            raise ValueError("Missing required ContractID")

        return ContractCallTransactionBody(
            contractID=self.contract_id._to_proto(),
            gas=self.gas,
            amount=self.amount,
            functionParameters=self.function_parameters,
        )

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for contract execution.

        Returns:
            TransactionBody: The protobuf transaction body containing the
                contract execution details.
        """
        contract_execute_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.contractCall.CopyFrom(contract_execute_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this contract execute transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        contract_execute_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.contractCall.CopyFrom(contract_execute_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the contract execute transaction.

        Implements the abstract method from Transaction to provide the specific
        gRPC method for executing a contract.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the transaction function
        """
        return _Method(
            transaction_func=channel.smart_contract.contractCallMethod,
            query_func=None,
        )
