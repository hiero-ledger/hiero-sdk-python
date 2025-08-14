"""
Transaction to update a contract's properties, metadata, or keys on the network.
"""

# pylint: disable=too-many-instance-attributes
from dataclasses import dataclass
from typing import Optional

from google.protobuf.wrappers_pb2 import StringValue, Int32Value, BoolValue

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    contract_update_pb2,
    timestamp_pb2,
    transaction_body_pb2,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.file.file_id import FileId


@dataclass
class ContractUpdateParams:
    """
    Represents contract update parameters.

    Attributes
    contract_id: ContractId
    expiration_time: Timestamp
    admin_key: PublicKey
    auto_renew_period: Duration
    file_id: FileId
    contract_memo: str
    max_automatic_token_associations: int
    auto_renew_account_id: AccountId
    staked_node_id: int
    decline_reward: bool
    """

    contract_id: ContractId = None
    expiration_time: Timestamp = None
    admin_key: Optional[PublicKey] = None
    auto_renew_period: Duration = None
    file_id: Optional[FileId] = None
    contract_memo: Optional[str] = None
    max_automatic_token_associations: Optional[int] = None
    auto_renew_account_id: Optional[AccountId] = None
    staked_node_id: Optional[int] = None
    staked_account_id: Optional[AccountId] = None
    decline_reward: Optional[bool] = None


class ContractUpdateTransaction(Transaction):
    """
    Represents a contract update transaction on the network.

    This transaction updates the metadata and/or properties of a smart contract. If a field is
    not set
    in the transaction body, the corresponding contract attribute will be unchanged. This
    transaction
    must be signed by the admin key of the contract being updated.
    If the admin key itself is being updated, then the transaction must
    also be signed by the new admin key.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a contract update transaction.
    """

    def __init__(
        self,
        contract_params: Optional[ContractUpdateParams] = None,
    ) -> None:
        """
        Initializes a new ContractUpdateTransaction instance with the specified parameters.

        Args:
            contract_params (Optional[ContractUpdateParams], optional): The contract update
                parameters
                containing all the fields that can be updated. If not provided, defaults to an empty
                ContractUpdateParams instance.
        """
        super().__init__()
        params = contract_params or ContractUpdateParams()
        self.contract_id: Optional[ContractId] = params.contract_id
        self.expiration_time: Optional[Timestamp] = params.expiration_time
        self.admin_key: Optional[PublicKey] = params.admin_key
        self.auto_renew_period: Optional[Duration] = params.auto_renew_period
        self.file_id: Optional[FileId] = params.file_id
        self.contract_memo: Optional[str] = params.contract_memo
        self.max_automatic_token_associations: Optional[int] = (
            params.max_automatic_token_associations
        )
        self.auto_renew_account_id: Optional[AccountId] = params.auto_renew_account_id
        self.staked_node_id: Optional[int] = params.staked_node_id
        self.staked_account_id: Optional[AccountId] = params.staked_account_id
        self.decline_reward: Optional[bool] = params.decline_reward
        self._default_transaction_fee = Hbar(20).to_tinybars()

    def set_contract_id(self, contract_id: ContractId) -> "ContractUpdateTransaction":
        """
        Sets the ContractID to be updated.

        Args:
            contract_id (ContractId): The ID of the contract to update.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contract_id = contract_id
        return self

    def set_expiration_time(
        self, expiration_time: Optional[Timestamp]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new expiration time for the contract.

        Args:
            expiration_time (Optional[Timestamp]): The new expiration time for the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def set_admin_key(
        self, admin_key: Optional[PublicKey]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new admin key for the contract.

        Args:
            admin_key (Optional[PublicKey]): The new admin key for the contract.
                This key can update or delete the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_auto_renew_period(
        self, auto_renew_period: Optional[Duration]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new auto-renewal period for the contract.

        Args:
            auto_renew_period (Optional[Duration]): The new auto-renewal period for the contract.
                The contract will be automatically renewed for this duration upon expiration.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_period = auto_renew_period
        return self

    def set_file_id(self, file_id: Optional[FileId]) -> "ContractUpdateTransaction":
        """
        Sets the new file ID containing the contract's bytecode.

        Args:
            file_id (Optional[FileId]): The new file ID containing the contract's bytecode.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.file_id = file_id
        return self

    def set_contract_memo(
        self, contract_memo: Optional[str]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new memo associated with the contract.

        Args:
            contract_memo (Optional[str]): The new memo for the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contract_memo = contract_memo
        return self

    def set_max_automatic_token_associations(
        self, max_automatic_token_associations: Optional[int]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new maximum number of tokens that can be automatically associated with the
        contract.

        Args:
            max_automatic_token_associations (Optional[int]): The new maximum number of tokens
                that can be automatically associated with the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.max_automatic_token_associations = max_automatic_token_associations
        return self

    def set_auto_renew_account_id(
        self, auto_renew_account_id: Optional[AccountId]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new account ID that will be charged for the contract's auto-renewal.

        Args:
            auto_renew_account_id (Optional[AccountId]): The new account ID that will be
                charged for the contract's auto-renewal.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_account_id = auto_renew_account_id
        return self

    def set_staked_node_id(
        self, staked_node_id: Optional[int]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new node ID to which the contract stakes.

        Args:
            staked_node_id (Optional[int]): The new node ID to which the contract stakes.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_node_id = staked_node_id
        return self

    def set_decline_reward(
        self, decline_reward: Optional[bool]
    ) -> "ContractUpdateTransaction":
        """
        Sets whether the contract declines staking rewards.

        Args:
            decline_reward (Optional[bool]): Whether the contract declines staking rewards.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.decline_reward = decline_reward
        return self

    def set_staked_account_id(
        self, staked_account_id: Optional[AccountId]
    ) -> "ContractUpdateTransaction":
        """
        Sets the new account ID to which the contract stakes.

        Args:
            staked_account_id (Optional[AccountId]): The new account ID to which the contract
                stakes.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_account_id = staked_account_id
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for contract update.

        Returns:
            TransactionBody: The protobuf transaction body containing the contract update details.

        Raises:
            ValueError: If required fields are missing.
        """
        if self.contract_id is None:
            raise ValueError("Missing required ContractID")

        transaction_body = self.build_base_transaction_body()
        transaction_body.contractUpdateInstance.CopyFrom(
            contract_update_pb2.ContractUpdateTransactionBody(
                contractID=self.contract_id._to_proto(),
                expirationTime=(
                    self.expiration_time._to_protobuf()
                    if self.expiration_time
                    else None
                ),
                adminKey=self.admin_key._to_proto() if self.admin_key else None,
                autoRenewPeriod=(
                    self.auto_renew_period._to_protobuf()
                    if self.auto_renew_period
                    else None
                ),
                fileID=self.file_id._to_proto() if self.file_id else None,
                staked_node_id=self.staked_node_id,
                memoWrapper=(
                    StringValue(value=self.contract_memo)
                    if self.contract_memo
                    else None
                ),
                max_automatic_token_associations=self.max_automatic_token_associations,
                auto_renew_account_id=(
                    self.auto_renew_account_id._to_proto()
                    if self.auto_renew_account_id
                    else None
                ),
                staked_account_id=(
                    self.staked_account_id._to_proto()
                    if self.staked_account_id
                    else None
                ),
                decline_reward=self.decline_reward,
            )
        )

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the contract update transaction.

        This internal method returns a _Method object containing the appropriate gRPC
        function to call when executing this transaction on the Hedera network.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: An object containing the transaction function to update a contract.
        """
        return _Method(
            transaction_func=channel.smart_contract.updateContract, query_func=None
        )
