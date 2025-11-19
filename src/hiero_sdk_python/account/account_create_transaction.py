"""
AccountCreateTransaction class.
"""

from typing import Optional, Union
import warnings

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import crypto_create_pb2, duration_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction

AUTO_RENEW_PERIOD = Duration(7890000)  # around 90 days in seconds
DEFAULT_TRANSACTION_FEE = Hbar(3).to_tinybars()  # 3 Hbars


class AccountCreateTransaction(Transaction):
    """
    Represents an account creation transaction on the Hedera network.
    """

    def __init__(
        self,
        key: Optional[PublicKey] = None,
        initial_balance: Union[Hbar, int] = 0,
        receiver_signature_required: Optional[bool] = None,
        auto_renew_period: Optional[Duration] = AUTO_RENEW_PERIOD,
        memo: Optional[str] = None,
        max_automatic_token_associations: Optional[int] = 0,
        alias: Optional[EvmAddress] = None,
        staked_account_id: Optional[AccountId] = None,
        staked_node_id: Optional[int] = None,
        decline_staking_reward: Optional[bool] = False
    ) -> None:
        """
        Initializes a new AccountCreateTransaction instance with default values
        or specified keyword arguments.

        Attributes:
            key (Optional[PublicKey]): The public key for the new account.
            initial_balance (Union[Hbar, int]): Initial balance in Hbar or tinybars.
            receiver_signature_required (Optional[bool]): Whether receiver signature is required.
            auto_renew_period (Duration): Auto-renew period in seconds (default is ~90 days).
            memo (Optional[str]): Memo for the account.
            max_automatic_token_associations (Optional[int]): The maximum number of tokens that 
                can be auto-associated.
            alias (Optional[EvmAddress]): The 20-byte EVM address to be used as the account's alias.
            staked_account_id (Optional[AccountId]): The account to which this account will stake.
            staked_node_id (Optional[int]): ID of the node this account is staked to.
            decline_staking_reward (Optional[bool]): If true, the account declines receiving a 
                staking reward (default is False).
        """
        super().__init__()
        self.key: Optional[PublicKey] = key
        self.initial_balance: Union[Hbar, int] = initial_balance
        self.receiver_signature_required: Optional[bool] = receiver_signature_required
        self.auto_renew_period: Optional[Duration] = auto_renew_period
        self.account_memo: Optional[str] = memo
        self.max_automatic_token_associations: Optional[int] = max_automatic_token_associations
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE
        self.alias: Optional[EvmAddress] = alias
        self.staked_account_id: Optional[AccountId] = staked_account_id
        self.staked_node_id: Optional[int] = staked_node_id
        self.decline_staking_reward = decline_staking_reward

    def set_key(self, key: PublicKey) -> "AccountCreateTransaction":
        """
        Sets the public key for the new account.

        Args:
            key (PublicKey): The public key to assign to the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        warnings.warn(
            "The 'set_key' method is deprecated, Use `set_key_without_alias` instead.",
            DeprecationWarning,
        )
        self._require_not_frozen()
        self.key = key
        return self

    def set_key_without_alias(self, key: PublicKey) -> "AccountCreateTransaction":
        """
        Sets the public key for the new account without alias.

        Args:
            key (PublicKey): The public key to assign to the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self.key = key
        return self

    def set_key_with_alias(
        self,
        key: PublicKey,
        ecdsa_key: Optional[PublicKey]=None
    ) -> "AccountCreateTransaction":
        """
        Sets the public key for the new account and assigns an alias derived from an ECDSA key.
        
        If `ecdsa_key` is provided, its corresponding EVM address will be used as the account alias.
        Otherwise, the alias will be derived from the provided `key`.

        Args:
            key (PublicKey): The public key to assign to the account.
            ecdsa_key (Optional[PublicKey]): An optional ECDSA public key used 
                to derive the account alias.

        Returns:
            AccountCreateTransaction: The current transaction instance to allow method chaining.
        """
        self._require_not_frozen()
        self.key = key
        self.alias = ecdsa_key.to_evm_address() if ecdsa_key is not None else key.to_evm_address()
        return self

    def set_initial_balance(self, balance: Union[Hbar, int]) -> "AccountCreateTransaction":
        """
        Sets the initial balance for the new account.

        Args:
            balance (Hbar or int): The initial balance in Hbar or tinybars.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if not isinstance(balance, (Hbar, int)):
            raise TypeError(
                "initial_balance must be either an instance of Hbar or an integer (tinybars)."
            )
        self.initial_balance = balance
        return self

    def set_receiver_signature_required(self, required: bool) -> "AccountCreateTransaction":
        """
        Sets whether a receiver signature is required.

        Args:
            required (bool): True if required, False otherwise.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self.receiver_signature_required = required
        return self

    def set_auto_renew_period(self, seconds: Union[int, Duration]) -> "AccountCreateTransaction":
        """
        Sets the auto-renew period in seconds.

        Args:
            seconds (int): The auto-renew period.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_account_memo(self, memo: str) -> "AccountCreateTransaction":
        """
        Sets the memo for the new account.

        Args:
            memo (str): The memo to associate with the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self.account_memo = memo
        return self

    def set_max_automatic_token_associations(self, max_assoc: int) -> "AccountCreateTransaction":
        """
        Sets the maximum number of automatic token associations for the account.

        Args:
            max_assoc (int): The maximum number of automatic 
                token associations to allow (default 0).

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        # FIX
        if max_assoc < -1:
            raise ValueError("max_automatic_token_associations must be -1 (unlimited) or a non-negative integer.")
        self.max_automatic_token_associations = max_assoc
        return self

    def set_alias(self, alias_evm_address: Union[EvmAddress, str]) -> "AccountCreateTransaction":
        """
        Sets the EVM Address alias for the account.

        Args:
            alias_evm_address (Union[EvmAddress, str]): The 20-byte EVM address to 
                be used as the account's alias.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(alias_evm_address, str):
            if len(alias_evm_address.removeprefix("0x")) == 40:
                self.alias = EvmAddress.from_string(alias_evm_address)
            else:
                raise ValueError("alias_evm_address must be a valid 20-byte EVM address")

        elif isinstance(alias_evm_address, EvmAddress):
            self.alias = alias_evm_address

        else:
            raise TypeError("alias_evm_address must be of type str or EvmAddress")

        return self

    def set_staked_account_id(
        self,
        account_id: Union[AccountId, str]
    ) -> "AccountCreateTransaction":
        """
        Sets the staked account id for the account.

        Args:
            account_id (Union[AccountId, str]): The account to which this account will stake.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(account_id, str):
            self.staked_account_id = AccountId.from_string(account_id)
        elif isinstance(account_id, AccountId):
            self.staked_account_id = account_id
        else:
            raise TypeError("account_id must be of type str or AccountId")

        return self

    def set_staked_node_id(self, node_id: int) -> "AccountCreateTransaction":
        """
        Sets the staked node id for the account.

        Args:
            node_id (int): The node to which this account will stake.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if not isinstance(node_id, int):
            raise TypeError("node_id must be of type int")

        self.staked_node_id = node_id
        return self

    def set_decline_staking_reward(
        self,
        decline_staking_reward: bool
    ) -> "AccountCreateTransaction":
        """
        Sets the decline staking reward for the account.

        Args:
            decline_staking_reward (bool): If true, the account declines 
            receiving a staking reward (default is False)

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if not isinstance(decline_staking_reward, bool):
            raise TypeError("decline_staking_reward must be of type bool")

        self.decline_staking_reward = decline_staking_reward
        return self

    def _build_proto_body(self) -> crypto_create_pb2.CryptoCreateTransactionBody:
        """
        Returns the protobuf body for the account create transaction.

        Returns:
            CryptoCreateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If required fields are missing.
            TypeError: If initial_balance is an invalid type.
        """
        if not self.key:
            raise ValueError("Key must be set before building the transaction.")

        if isinstance(self.initial_balance, Hbar):
            initial_balance_tinybars = self.initial_balance.to_tinybars()
        elif isinstance(self.initial_balance, int):
            initial_balance_tinybars = self.initial_balance
        else:
            raise TypeError("initial_balance must be Hbar or int (tinybars).")

        proto_body = crypto_create_pb2.CryptoCreateTransactionBody(
            key=self.key._to_proto(),
            initialBalance=initial_balance_tinybars,
            receiverSigRequired=self.receiver_signature_required,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds),
            memo=self.account_memo,
            max_automatic_token_associations=self.max_automatic_token_associations,
            alias=self.alias.address_bytes if self.alias else None,
            decline_reward=self.decline_staking_reward
        )

        if self.staked_account_id:
            proto_body.staked_account_id.CopyFrom(self.staked_account_id._to_proto())
        elif self.staked_node_id:
            proto_body.staked_node_id = self.staked_node_id

        return proto_body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for account creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the account creation details.
        """
        crypto_create_body = self._build_proto_body()
        transaction_body: transaction_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.cryptoCreateAccount.CopyFrom(crypto_create_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this account create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        crypto_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.cryptoCreateAccount.CopyFrom(crypto_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method for executing the account creation transaction.
        Args:
            channel (_Channel): The channel to use for the transaction.
        Returns:
            _Method: An instance of _Method containing the transaction and query functions.
        """
        return _Method(transaction_func=channel.crypto.createAccount, query_func=None)
