"""
AccountCreateTransaction class.
"""

from typing import Optional, Union

from hiero_sdk_python.channels import _Channel
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
        max_automatic_token_associations: Optional[int] = 0 
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
        """
        super().__init__()
        self.key: Optional[PublicKey] = key
        self.initial_balance: Union[Hbar, int] = initial_balance
        self.receiver_signature_required: Optional[bool] = receiver_signature_required
        self.auto_renew_period: Optional[Duration] = auto_renew_period
        self.account_memo: Optional[str] = memo
        self.max_automatic_token_associations: Optional[int] = max_automatic_token_associations
        self._default_transaction_fee = DEFAULT_TRANSACTION_FEE

    def set_key(self, key: PublicKey) -> "AccountCreateTransaction":
        """
        Sets the public key for the new account.

        Args:
            key (PublicKey): The public key to assign to the account.

        Returns:
            AccountCreateTransaction: The current transaction instance for method chaining.
        """
        self._require_not_frozen()
        self.key = key
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
        """Sets the maximum number of automatic token associations for the account."""
        self._require_not_frozen()
        if max_assoc < 0:
            raise ValueError("max_automatic_token_associations must be a non-negative integer.")
        self.max_automatic_token_associations = max_assoc
        return self

    def _build_proto_body(self):
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

        return crypto_create_pb2.CryptoCreateTransactionBody(
            key=self.key._to_proto(),
            initialBalance=initial_balance_tinybars,
            receiverSigRequired=self.receiver_signature_required,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds),
            memo=self.account_memo,
            max_automatic_token_associations=self.max_automatic_token_associations
        )

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
