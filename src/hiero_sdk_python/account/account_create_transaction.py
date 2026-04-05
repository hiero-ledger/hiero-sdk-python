"""AccountCreateTransaction class."""

from __future__ import annotations

import ctypes
import warnings

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.evm_address import EvmAddress
from hiero_sdk_python.crypto.key import Key
from hiero_sdk_python.crypto.private_key import PrivateKey
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
    """Represents an account creation transaction on the Hedera network."""

    def __init__(
        self,
        key: Key | None = None,
        initial_balance: Hbar | int = 0,
        receiver_signature_required: bool | None = None,
        auto_renew_period: Duration | None = AUTO_RENEW_PERIOD,
        memo: str | None = None,
        max_automatic_token_associations: int | None = 0,
        alias: EvmAddress | None = None,
        staked_account_id: AccountId | None = None,
        staked_node_id: int | None = None,
        decline_staking_reward: bool | None = False,
    ) -> None:
        """
        Initializes a new AccountCreateTransaction instance with default values
        or specified keyword arguments.

        Attributes:
            key (PublicKey, optional): The public key for the new account.
            initial_balance (Hbar | int, optional): Initial balance in Hbar or tinybars.
            receiver_signature_required (bool, optional): Whether receiver signature is required.
            auto_renew_period (Duration): Auto-renew period in seconds (default is ~90 days).
            memo (str, optional): Memo for the account.
            max_automatic_token_associations (int, optional): The maximum number of tokens that
                can be auto-associated.
            alias (EvmAddress, optional): The 20-byte EVM address to be used as the account's alias.
            staked_account_id (AccountId, optional): The account to which this account will stake.
            staked_node_id (int, optional): ID of the node this account is staked to.
            decline_staking_reward (bool, optional): If true, the account declines receiving a
                staking reward (default is False).
        """
        super().__init__()
        self.key: Key | None = key
        self.initial_balance: Hbar | int = initial_balance
        self.receiver_signature_required: bool | None = receiver_signature_required
        self.auto_renew_period: Duration | None = auto_renew_period
        self.account_memo: str | None = memo
        self.max_automatic_token_associations: int | None = max_automatic_token_associations
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE
        self.alias: EvmAddress | None = alias
        self.staked_account_id: AccountId | None = staked_account_id
        self.staked_node_id: int | None = staked_node_id
        self.decline_staking_reward = decline_staking_reward

    def set_key(self, key: Key) -> AccountCreateTransaction:
        """
        Sets the key for the new account (accepts both PrivateKey or PublicKey).

        Args:
            key (Key): The key to assign to the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        warnings.warn(
            "The 'set_key' method is deprecated, Use `set_key_without_alias` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._require_not_frozen()
        self.key = key
        return self

    def set_key_without_alias(self, key: Key) -> AccountCreateTransaction:
        """
        Sets the key for the new account without alias (accepts both PrivateKey or PublicKey).

        Args:
            key (Key): The key to assign to the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self.key = key
        self.alias = None
        return self

    def set_key_with_alias(self, key: Key, ecdsa_key: Key | None = None) -> AccountCreateTransaction:
        """
        Sets the key for the new account and assigns an alias derived from an ECDSA key.

        If `ecdsa_key` is provided, its corresponding EVM address will be used as the account alias.
        Otherwise, the alias will be derived from the provided `key`.

        Args:
            key (Key): The key to assign to the account (PrivateKey or PublicKey).
            ecdsa_key (PublicKey, optional): An optional ECDSA public key used
                to derive the account alias.

        Returns:
            AccountCreateTransaction: The current transaction instance to allow method chaining.
        """
        self._require_not_frozen()
        self.key = key
        evm_source_key: Key = ecdsa_key if ecdsa_key is not None else key
        if isinstance(evm_source_key, PrivateKey):
            evm_source_key = evm_source_key.public_key()

        self.alias = evm_source_key.to_evm_address()
        return self

    def set_initial_balance(self, balance: Hbar | int) -> AccountCreateTransaction:
        """
        Sets the initial balance for the new account.

        Args:
            balance (Hbar or int): The initial balance in Hbar or tinybars.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if not isinstance(balance, (Hbar, int)):
            raise TypeError("initial_balance must be either an instance of Hbar or an integer (tinybars).")
        self.initial_balance = balance
        return self

    def set_receiver_signature_required(self, required: bool) -> AccountCreateTransaction:
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

    def set_auto_renew_period(self, seconds: int | Duration) -> AccountCreateTransaction:
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

    def set_account_memo(self, memo: str) -> AccountCreateTransaction:
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

    def set_max_automatic_token_associations(self, max_assoc: int) -> AccountCreateTransaction:
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

    def set_alias(self, alias_evm_address: EvmAddress | str) -> AccountCreateTransaction:
        """
        Sets the EVM Address alias for the account.

        Args:
            alias_evm_address (EvmAddress | str): The 20-byte EVM address to
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

    def set_staked_account_id(self, account_id: AccountId | str) -> AccountCreateTransaction:
        """
        Sets the staked account id for the account.

        Args:
            account_id (AccountId | str): The account to which this account will stake.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(account_id, str):
            account_id = AccountId.from_string(account_id)
        elif not isinstance(account_id, AccountId):
            raise TypeError("account_id must be of type str or AccountId")

        self.staked_account_id = account_id
        self.staked_node_id = None
        return self

    def set_staked_node_id(self, node_id: int) -> AccountCreateTransaction:
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
        self.staked_account_id = None
        return self

    def set_decline_staking_reward(self, decline_staking_reward: bool) -> AccountCreateTransaction:
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
        if isinstance(self.initial_balance, Hbar):
            initial_balance_tinybars = self.initial_balance.to_tinybars()
        elif isinstance(self.initial_balance, int):
            initial_balance_tinybars = self.initial_balance
        else:
            raise TypeError("initial_balance must be Hbar or int (tinybars).")

        # Check for overflow
        if initial_balance_tinybars >= (2**64):
            raise OverflowError(f"Value {initial_balance_tinybars} exceeds 64-bit unsigned integer limit.")

        proto_body = crypto_create_pb2.CryptoCreateTransactionBody(
            key=self.key.to_proto_key() if self.key is not None else None,
            # triggers an INVALID_INITIAL_BALANCE pre-check error instead of a local error.
            initialBalance=ctypes.c_uint64(initial_balance_tinybars).value,
            receiverSigRequired=self.receiver_signature_required,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds),
            memo=self.account_memo,
            max_automatic_token_associations=self.max_automatic_token_associations,
            alias=self.alias.address_bytes if self.alias else None,
            decline_reward=self.decline_staking_reward,
        )

        if self.staked_node_id is not None and self.staked_account_id is not None:
            raise ValueError("Specify either staked_node_id or staked_account_id, not both.")

        if self.staked_account_id is not None:
            proto_body.staked_account_id.CopyFrom(self.staked_account_id._to_proto())
        elif self.staked_node_id is not None:
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
