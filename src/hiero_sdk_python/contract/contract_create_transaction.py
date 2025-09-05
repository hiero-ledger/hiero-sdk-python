# pylint: disable=too-many-instance-attributes
"""
ContractCreateTransaction class.
"""

from dataclasses import dataclass
from typing import Optional

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services.contract_create_pb2 import (
    ContractCreateTransactionBody,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction

DEFAULT_AUTO_RENEW_PERIOD = 90 * 24 * 60 * 60  # 90 days in seconds


@dataclass
class ContractCreateParams:
    """
    Represents contract creation parameters.

    Attributes:
        bytecode_file_id (Optional[FileId]): The FileId of the file containing
            the contract bytecode.
        proxy_account_id (Optional[AccountId]): The AccountId of the proxy account.
        admin_key (Optional[PublicKey]): The admin key for the contract.
        gas (Optional[int]): The gas limit for contract creation.
        initial_balance (Optional[int]): The initial balance for the contract
            in tinybars.
        auto_renew_period (Duration): The auto-renewal period for the contract.
        parameters (Optional[bytes]): ABI-encoded constructor parameters to be
            passed to the smart contract upon creation.
        contract_memo (Optional[str]): The memo for the contract.
        bytecode (Optional[bytes]): The bytecode for the contract.
        auto_renew_account_id (Optional[AccountId]): The AccountId that will pay
            for auto-renewal.
        max_automatic_token_associations (Optional[int]): Maximum number of
            automatic token associations.
        staked_account_id (Optional[AccountId]): The AccountId to stake to.
        staked_node_id (Optional[int]): The node ID to stake to.
        decline_reward (Optional[bool]): Whether to decline staking rewards.
    """

    bytecode_file_id: Optional[FileId] = None
    proxy_account_id: Optional[AccountId] = None
    admin_key: Optional[PublicKey] = None
    gas: Optional[int] = None
    initial_balance: Optional[int] = None
    auto_renew_period: Duration = Duration(DEFAULT_AUTO_RENEW_PERIOD)
    parameters: Optional[bytes] = None
    contract_memo: Optional[str] = None
    bytecode: Optional[bytes] = None
    auto_renew_account_id: Optional[AccountId] = None
    max_automatic_token_associations: Optional[int] = None
    staked_account_id: Optional[AccountId] = None
    staked_node_id: Optional[int] = None
    decline_reward: Optional[bool] = None


class ContractCreateTransaction(Transaction):
    """
    A transaction that creates a new smart contract.

    This transaction can be used to create a new smart contract on the network.
    The contract can be created from bytecode stored in a file or from
    bytecode provided directly.

    Args:
        contract_params (ContractCreateParams, optional): Parameters for
            contract creation.
    """

    def __init__(self, contract_params: Optional[ContractCreateParams] = None):
        """
        Initializes a new ContractCreateTransaction instance.

        Args:
            contract_params (ContractCreateParams, optional): Parameters for
                contract creation.
        """
        super().__init__()

        params = contract_params or ContractCreateParams()
        self.bytecode_file_id: Optional[FileId] = params.bytecode_file_id
        self.proxy_account_id: Optional[AccountId] = params.proxy_account_id
        self.admin_key: Optional[PublicKey] = params.admin_key
        self.gas: Optional[int] = params.gas
        self.initial_balance: Optional[int] = params.initial_balance
        self.auto_renew_period: Duration = params.auto_renew_period
        self.parameters: Optional[bytes] = params.parameters
        self.contract_memo: Optional[str] = params.contract_memo
        self.bytecode: Optional[bytes] = params.bytecode
        self.auto_renew_account_id: Optional[AccountId] = params.auto_renew_account_id
        self.max_automatic_token_associations: Optional[int] = (
            params.max_automatic_token_associations
        )
        self.staked_account_id: Optional[AccountId] = params.staked_account_id
        self.staked_node_id: Optional[int] = params.staked_node_id
        self.decline_reward: Optional[bool] = params.decline_reward

        self._default_transaction_fee = Hbar(20).to_tinybars()

    def set_bytecode_file_id(
        self, bytecode_file_id: Optional[FileId]
    ) -> "ContractCreateTransaction":
        """
        Sets the FileID of the file containing the contract bytecode.

        Args:
            bytecode_file_id (Optional[FileId]): The FileID of the
                bytecode file.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.bytecode_file_id = bytecode_file_id
        return self

    def set_bytecode(self, code: Optional[bytes]) -> "ContractCreateTransaction":
        """
        Sets the bytecode for the contract.

        If the bytecode is small enough, it may be stored directly in the
        transaction, otherwise it should be stored in a file.

        Args:
            code (Optional[bytes]): The contract bytecode.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.bytecode = code
        self.bytecode_file_id = None
        return self

    def set_proxy_account_id(
        self, proxy_account_id: Optional[AccountId]
    ) -> "ContractCreateTransaction":
        """
        Sets the proxy account ID for the contract.

        Args:
            proxy_account_id (Optional[AccountId]): The proxy account ID.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.proxy_account_id = proxy_account_id
        return self

    def set_admin_key(
        self, admin_key: Optional[PublicKey]
    ) -> "ContractCreateTransaction":
        """
        Sets the admin key for the contract.

        Args:
            admin_key (Optional[PublicKey]): The admin key.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.admin_key = admin_key
        return self

    def set_gas(self, gas: Optional[int]) -> "ContractCreateTransaction":
        """
        Sets the gas limit for contract creation.

        Args:
            gas (Optional[int]): The gas limit.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.gas = gas
        return self

    def set_initial_balance(
        self, initial_balance: Optional[int]
    ) -> "ContractCreateTransaction":
        """
        Sets the initial balance for the contract in tinybars.

        Args:
            initial_balance (Optional[int]): The initial balance in tinybars.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.initial_balance = initial_balance
        return self

    def set_auto_renew_period(
        self, auto_renew_period: Duration
    ) -> "ContractCreateTransaction":
        """
        Sets the auto-renewal period for the contract.

        Args:
            auto_renew_period (Duration): The auto-renewal period.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_period = auto_renew_period
        return self

    def set_constructor_parameters(
        self, parameters: Optional[ContractFunctionParameters | bytes]
    ) -> "ContractCreateTransaction":
        """
        Sets the constructor parameters for the contract.

        Args:
            parameters (Optional[ContractFunctionParameters | bytes]): The
                constructor parameters.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        if isinstance(parameters, ContractFunctionParameters):
            self.parameters = parameters.to_bytes()
        else:
            self.parameters = parameters
        return self

    def set_contract_memo(
        self, contract_memo: Optional[str]
    ) -> "ContractCreateTransaction":
        """
        Sets the contract_memo for the contract.

        Args:
            contract_memo (Optional[str]): The contract_memo.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.contract_memo = contract_memo
        return self

    def set_auto_renew_account_id(
        self, auto_renew_account_id: Optional[AccountId]
    ) -> "ContractCreateTransaction":
        """
        Sets the account ID that will pay for auto-renewal.

        Args:
            auto_renew_account_id (Optional[AccountId]): The auto-renewal
                account ID.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_account_id = auto_renew_account_id
        return self

    def set_max_automatic_token_associations(
        self, max_automatic_token_associations: Optional[int]
    ) -> "ContractCreateTransaction":
        """
        Sets the maximum number of automatic token associations.

        Args:
            max_automatic_token_associations (Optional[int]): The maximum
                number of automatic token associations.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.max_automatic_token_associations = max_automatic_token_associations
        return self

    def set_staked_account_id(
        self, staked_account_id: Optional[AccountId]
    ) -> "ContractCreateTransaction":
        """
        Sets the account ID to stake to.

        Args:
            staked_account_id (Optional[AccountId]): The staked account ID.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_account_id = staked_account_id
        return self

    def set_staked_node_id(
        self, staked_node_id: Optional[int]
    ) -> "ContractCreateTransaction":
        """
        Sets the node ID to stake to.

        Args:
            staked_node_id (Optional[int]): The staked node ID.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.staked_node_id = staked_node_id
        return self

    def set_decline_reward(
        self, decline_reward: Optional[bool]
    ) -> "ContractCreateTransaction":
        """
        Sets whether to decline staking rewards.

        Args:
            decline_reward (Optional[bool]): Whether to decline staking
                rewards.

        Returns:
            ContractCreateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.decline_reward = decline_reward
        return self

    def _validate_parameters(self):
        """
        Validates the parameters for the contract creation transaction.
        """
        if self.bytecode_file_id is None and self.bytecode is None:
            raise ValueError("Either bytecode_file_id or bytecode must be provided")

        if self.gas is None:
            raise ValueError("Gas limit must be provided")

    def _build_proto_body(self):
        """
        Returns the protobuf body for the contract create transaction.

        Returns:
            ContractCreateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If required fields are missing.
        """
        self._validate_parameters()

        return ContractCreateTransactionBody(
            gas=self.gas,
            initialBalance=self.initial_balance,
            constructorParameters=self.parameters,
            memo=self.contract_memo,
            max_automatic_token_associations=self.max_automatic_token_associations,
            decline_reward=(
                self.decline_reward if self.decline_reward is not None else False
            ),
            auto_renew_account_id=(
                self.auto_renew_account_id._to_proto()
                if self.auto_renew_account_id
                else None
            ),
            staked_account_id=(
                self.staked_account_id._to_proto() if self.staked_account_id else None
            ),
            staked_node_id=self.staked_node_id,
            autoRenewPeriod=self.auto_renew_period._to_proto(),
            proxyAccountID=(
                self.proxy_account_id._to_proto() if self.proxy_account_id else None
            ),
            adminKey=(self.admin_key._to_proto() if self.admin_key else None),
            fileID=self.bytecode_file_id._to_proto() if self.bytecode_file_id else None,
            initcode=self.bytecode,
        )

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for contract creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the
                contract creation details.
        """
        contract_create_body = self._build_proto_body()

        transaction_body = self.build_base_transaction_body()
        transaction_body.contractCreateInstance.CopyFrom(contract_create_body)

        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this contract create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        contract_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.contractCreateInstance.CopyFrom(contract_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the contract create transaction.

        Args:
            channel (_Channel): The channel containing service stubs.

        Returns:
            _Method: An object containing the transaction function to
                create contracts.
        """
        return _Method(
            transaction_func=channel.smart_contract.createContract, query_func=None
        )
