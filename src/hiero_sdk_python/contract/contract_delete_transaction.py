"""
ContractDeleteTransaction class.
"""

from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.contract_delete_pb2 import (
    ContractDeleteTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction


class ContractDeleteTransaction(Transaction):
    """
    A transaction that deletes a smart contract.

    This transaction can be used to delete an existing smart contract from the network.
    When a contract is deleted, its remaining balance can be transferred to either
    another contract or an account. The contract can also be permanently removed
    from the network state.

    Args:
        contract_id (Optional[ContractId]): The ID of the contract to delete.
        transfer_contract_id (Optional[ContractId]): The contract ID to transfer
            remaining balance to.
        transfer_account_id (Optional[AccountId]): The account ID to transfer
            remaining balance to.
        permanent_removal (Optional[bool]): Whether to permanently remove the
            contract from network state.
    """

    def __init__(
        self,
        contract_id: Optional[ContractId] = None,
        transfer_contract_id: Optional[ContractId] = None,
        transfer_account_id: Optional[AccountId] = None,
        permanent_removal: Optional[bool] = None,
    ):
        """
        Initializes a new ContractDeleteTransaction instance.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to delete.
            transfer_contract_id (Optional[ContractId]): The contract ID to transfer
                remaining balance to.
            transfer_account_id (Optional[AccountId]): The account ID to transfer
                remaining balance to.
            permanent_removal (Optional[bool]): Whether to permanently remove the
                contract from network state.
        """
        super().__init__()
        self.contract_id: Optional[ContractId] = contract_id
        self.transfer_contract_id: Optional[ContractId] = transfer_contract_id
        self.transfer_account_id: Optional[AccountId] = transfer_account_id
        self.permanent_removal: Optional[bool] = permanent_removal
        self._default_transaction_fee = Hbar(2).to_tinybars()

    def set_contract_id(
        self, contract_id: Optional[ContractId]
    ) -> "ContractDeleteTransaction":
        """
        Sets the ID of the contract to delete.

        Args:
            contract_id (Optional[ContractId]): The ID of the contract to delete.

        Returns:
            ContractDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contract_id = contract_id
        return self

    def set_transfer_contract_id(
        self, transfer_contract_id: Optional[ContractId]
    ) -> "ContractDeleteTransaction":
        """
        Sets the contract ID to transfer the remaining balance to.

        When a contract is deleted, its remaining balance must be transferred
        to either another contract or an account. This method sets the target
        contract for the balance transfer.

        Args:
            transfer_contract_id (Optional[ContractId]): The contract ID to transfer
                remaining balance to.

        Returns:
            ContractDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.transfer_contract_id = transfer_contract_id
        return self

    def set_transfer_account_id(
        self, transfer_account_id: Optional[AccountId]
    ) -> "ContractDeleteTransaction":
        """
        Sets the account ID to transfer the remaining balance to.

        When a contract is deleted, its remaining balance must be transferred
        to either another contract or an account. This method sets the target
        account for the balance transfer.

        Args:
            transfer_account_id (Optional[AccountId]): The account ID to transfer
                remaining balance to.

        Returns:
            ContractDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.transfer_account_id = transfer_account_id
        return self

    def set_permanent_removal(
        self, permanent_removal: Optional[bool]
    ) -> "ContractDeleteTransaction":
        """
        Sets whether to permanently remove the contract from network state.

        When set to True, the contract will be permanently removed from the
        network state and cannot be recovered. When False, the contract may
        be recoverable depending on network configuration.

        Args:
            permanent_removal (Optional[bool]): Whether to permanently remove the
                contract from network state.

        Returns:
            ContractDeleteTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.permanent_removal = permanent_removal
        return self

    def build_transaction_body(self):
        """
        Builds the transaction body for this contract delete transaction.

        Returns:
            TransactionBody: The built transaction body.

        Raises:
            ValueError: If contract_id is not set.
        """
        if self.contract_id is None:
            raise ValueError("Missing required ContractID")

        contract_delete_body = ContractDeleteTransactionBody(
            contractID=self.contract_id._to_proto(),
            transferContractID=(
                self.transfer_contract_id._to_proto()
                if self.transfer_contract_id
                else None
            ),
            transferAccountID=(
                self.transfer_account_id._to_proto()
                if self.transfer_account_id
                else None
            ),
            permanent_removal=self.permanent_removal,
        )

        transaction_body = self.build_base_transaction_body()
        transaction_body.contractDeleteInstance.CopyFrom(contract_delete_body)
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the contract delete transaction.

        Args:
            channel (_Channel): The channel containing service stubs.

        Returns:
            _Method: An object containing the transaction function to
                delete contracts.
        """
        return _Method(
            transaction_func=channel.smart_contract.deleteContract, query_func=None
        )
