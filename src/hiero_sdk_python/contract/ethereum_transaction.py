"""
EthereumTransaction class.
"""

from typing import Optional

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.ethereum_transaction_pb2 import (
    EthereumTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.transaction.transaction import Transaction


class EthereumTransaction(Transaction):
    """
    A transaction that executes Ethereum transactions on the network.

    This transaction can be used to execute Ethereum transactions on the network,
    allowing for compatibility with Ethereum smart contracts and transactions. You can
    specify Ethereum transaction data, call data from a file, and gas limits for the
    transaction execution.
    """

    def __init__(
        self,
        ethereum_data: Optional[bytes] = None,
        call_data_file_id: Optional[FileId] = None,
        max_gas_allowed: Optional[int] = None,
    ):
        """
        Initializes a new EthereumTransaction instance.

        Args:
            ethereum_data (Optional[bytes]): The Ethereum transaction data to execute.
            call_data_file_id (Optional[FileId]):
                The FileId containing call data for the transaction.
            max_gas_allowed (Optional[int]): The maximum gas allowed for the transaction execution.
        """
        super().__init__()

        self.ethereum_data: Optional[bytes] = ethereum_data
        self.call_data: Optional[FileId] = call_data_file_id
        self.max_gas_allowed: Optional[int] = max_gas_allowed

    def set_ethereum_data(self, ethereum_data: Optional[bytes]) -> "EthereumTransaction":
        """
        Sets the Ethereum transaction data to execute.

        Args:
            ethereum_data (Optional[bytes]): The Ethereum transaction data to execute.

        Returns:
            EthereumTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.ethereum_data = ethereum_data
        return self

    def set_call_data_file_id(
        self, call_data_file_id: Optional[FileId]
    ) -> "EthereumTransaction":
        """
        Sets the call data for the transaction.

        Args:
            call_data_file_id (Optional[FileId]): The FileId containing call data for the transaction.

        Returns:
            EthereumTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.call_data = call_data_file_id
        return self

    def set_max_gas_allowed(
        self, max_gas_allowed: Optional[int]
    ) -> "EthereumTransaction":
        """
        Sets the maximum gas allowed for the transaction execution.

        Args:
            max_gas_allowed (Optional[int]): The maximum gas allowed for the transaction execution.

        Returns:
            EthereumTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.max_gas_allowed = max_gas_allowed
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the ethereum transaction.

        Returns:
            EthereumTransactionBody: The protobuf body for this transaction.
        """
        return EthereumTransactionBody(
            ethereum_data=self.ethereum_data,
            call_data=self.call_data._to_proto() if self.call_data else None,
            max_gas_allowance=self.max_gas_allowed,
        )

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for ethereum transaction.

        Returns:
            TransactionBody: The protobuf transaction body containing the
                ethereum transaction details.
        """
        ethereum_transaction_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.ethereumTransaction.CopyFrom(ethereum_transaction_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this ethereum transaction.

        Raises:
            ValueError: EthereumTransaction cannot be scheduled.
        """
        raise ValueError("Cannot schedule an EthereumTransaction")

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the ethereum transaction.

        Implements the abstract method from Transaction to provide the specific
        gRPC method for calling an ethereum transaction.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the transaction function
        """
        return _Method(
            transaction_func=channel.smart_contract.callEthereum,
            query_func=None,
        )
