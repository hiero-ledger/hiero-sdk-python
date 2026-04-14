# pylint: disable=too-many-instance-attributes
"""Transaction to update a contract's properties, metadata, or keys on the network."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.protobuf.wrappers_pb2 import BoolValue, Int32Value, StringValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import contract_update_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction


@dataclass
class ContractUpdateParams:
    """
    Represents contract attributes that can be updated.

    Attributes:
        contract_id (ContractId, optional): The contract ID to update.
        expiration_time (Timestamp, optional): The new expiration time for the contract.
        admin_key (PublicKey, optional): The new admin key for the contract.
        auto_renew_period (Duration, optional): The new auto-renew period for the contract.
        contract_memo (str, optional): The new memo for the contract.
        max_automatic_token_associations (int, optional): The new maximum number of
            automatic token associations for the contract.
        auto_renew_account_id (AccountId, optional): The new account to be charged for auto-renewal.
        staked_node_id (int, optional): The node ID to which the contract will be staked.
        staked_account_id (AccountId, optional): The account ID to which
            the contract will be staked.
        decline_reward (bool, optional): Whether the contract should decline staking rewards.
    """

    contract_id: ContractId | None = None
    expiration_time: Timestamp | None = None
    admin_key: PublicKey | None = None
    auto_renew_period: Duration | None = None
    contract_memo: str | None = None
    max_automatic_token_associations: int | None = None
    auto_renew_account_id: AccountId | None = None
    staked_node_id: int | None = None
    staked_account_id: AccountId | None = None
    decline_reward: bool | None = None


class ContractUpdateTransaction(Transaction):
    """
    Represents a contract update transaction on the network.

    This transaction updates the metadata and/or properties of a smart contract. If a field is
    not set
    in the transaction body, the corresponding contract attribute will be unchanged. This
    transaction must be signed by the admin key of the contract being updated.
    If the admin key itself is being updated, then the transaction must
    also be signed by the new admin key.

    Inherits from the base Transaction class and implements the required methods
    to build and execute a contract update transaction.
    """

    def __init__(
        self,
        contract_params: ContractUpdateParams | None = None,
    ) -> None:
        """
        Initializes a new ContractUpdateTransaction instance with the specified parameters.

        Args:
            contract_params (ContractUpdateParams, optional): The contract update
                parameters containing all the fields that can be updated.
                If not provided, defaults to an empty ContractUpdateParams instance.
        """
        super().__init__()
        params = contract_params or ContractUpdateParams()
        self.contract_id: ContractId | None = params.contract_id
        self.expiration_time: Timestamp | None = params.expiration_time
        self.admin_key: PublicKey | None = params.admin_key
        self.auto_renew_period: Duration | None = params.auto_renew_period
        self.contract_memo: str | None = params.contract_memo
        self.max_automatic_token_associations: int | None = params.max_automatic_token_associations
        self.auto_renew_account_id: AccountId | None = params.auto_renew_account_id
        self.staked_node_id: int | None = params.staked_node_id
        self.staked_account_id: AccountId | None = params.staked_account_id
        self.decline_reward: bool | None = params.decline_reward
        self._default_transaction_fee = Hbar(20).to_tinybars()

    def set_contract_id(self, contract_id: ContractId) -> ContractUpdateTransaction:
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

    def set_expiration_time(self, expiration_time: Timestamp | None) -> ContractUpdateTransaction:
        """
        Sets the new expiration time for the contract.

        Args:
            expiration_time (Timestamp | None): The new expiration time for the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def set_admin_key(self, admin_key: PublicKey | None) -> ContractUpdateTransaction:
        """
        Sets the new admin key for the contract.

        Args:
            admin_key (PublicKey | None): The new admin key for the contract.
                This key can update or delete the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_auto_renew_period(self, auto_renew_period: Duration | None) -> ContractUpdateTransaction:
        """
        Sets the new auto-renewal period for the contract.

        Args:
            auto_renew_period (Duration | None): The new auto-renewal period for the contract.
                The contract will be automatically renewed for this duration upon expiration.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_period = auto_renew_period
        return self

    def set_contract_memo(self, contract_memo: str | None) -> ContractUpdateTransaction:
        """
        Sets the new memo associated with the contract.

        Args:
            contract_memo (str | None): The new memo for the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contract_memo = contract_memo
        return self

    def set_max_automatic_token_associations(
        self, max_automatic_token_associations: int | None
    ) -> ContractUpdateTransaction:
        """
        Sets the new maximum number of tokens that can be automatically associated with the
        contract.

        Args:
            max_automatic_token_associations (int | None): The new maximum number of tokens
                that can be automatically associated with the contract.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.max_automatic_token_associations = max_automatic_token_associations
        return self

    def set_auto_renew_account_id(self, auto_renew_account_id: AccountId | None) -> ContractUpdateTransaction:
        """
        Sets the new account ID that will be charged for the contract's auto-renewal.

        Args:
            auto_renew_account_id (AccountId | None): The new account ID that will be
                charged for the contract's auto-renewal.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_account_id = auto_renew_account_id
        return self

    def set_staked_node_id(self, staked_node_id: int | None) -> ContractUpdateTransaction:
        """
        Sets the new node ID to which the contract stakes.

        Args:
            staked_node_id (int | None): The new node ID to which the contract stakes.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_node_id = staked_node_id
        return self

    def set_decline_reward(self, decline_reward: bool | None) -> ContractUpdateTransaction:
        """
        Sets whether the contract declines staking rewards.

        Args:
            decline_reward (bool | None): Whether the contract declines staking rewards.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.decline_reward = decline_reward
        return self

    def set_staked_account_id(self, staked_account_id: AccountId | None) -> ContractUpdateTransaction:
        """
        Sets the new account ID to which the contract stakes.

        Args:
            staked_account_id (AccountId | None): The new account ID to which the contract
                stakes.

        Returns:
            ContractUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_account_id = staked_account_id
        return self

    def _convert_to_proto(self, obj: Any | None) -> Any:
        """Convert object to proto if it exists, otherwise return None."""
        return obj._to_proto() if obj else None

    def _build_proto_body(self):
        """
        Returns the protobuf body for the contract update transaction.

        Returns:
            ContractUpdateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If contract_id is not set.
        """
        if self.contract_id is None:
            raise ValueError("Missing required ContractID")

        return contract_update_pb2.ContractUpdateTransactionBody(
            contractID=self.contract_id._to_proto(),
            expirationTime=(self.expiration_time._to_protobuf() if self.expiration_time else None),
            adminKey=self._convert_to_proto(self.admin_key),
            autoRenewPeriod=self._convert_to_proto(self.auto_renew_period),
            staked_node_id=self.staked_node_id,
            memoWrapper=(StringValue(value=self.contract_memo) if self.contract_memo is not None else None),
            max_automatic_token_associations=(
                Int32Value(value=self.max_automatic_token_associations)
                if self.max_automatic_token_associations is not None
                else None
            ),
            staked_account_id=self._convert_to_proto(self.staked_account_id),
            auto_renew_account_id=self._convert_to_proto(self.auto_renew_account_id),
            decline_reward=(BoolValue(value=self.decline_reward) if self.decline_reward is not None else None),
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for contract update.

        Returns:
            TransactionBody: The protobuf transaction body containing the contract update details.
        """
        contract_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.contractUpdateInstance.CopyFrom(contract_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this contract update transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        contract_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.contractUpdateInstance.CopyFrom(contract_update_body)
        return schedulable_body

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
        return _Method(transaction_func=channel.smart_contract.updateContract, query_func=None)
