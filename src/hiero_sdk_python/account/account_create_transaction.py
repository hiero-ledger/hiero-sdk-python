from typing import Union

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import crypto_create_pb2, duration_pb2, transaction_body_pb2
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.transaction.transaction import Transaction


class AccountCreateTransaction(Transaction):
    """
    Represents an account creation transaction on the Hedera network.
    """

    def __init__(
        self,
        key: PublicKey = None,
        initial_balance: Union[Hbar, int] = 0,
        receiver_signature_required: bool = False,
        auto_renew_period: Duration = Duration(7890000),  # 90 days in seconds
        memo: str = ""
     ) -> None:
        """
        Initializes a new AccountCreateTransaction instance with default values or specified keyword arguments.

        Args:
            key (PublicKey, optional): The public key for the new account.
            initial_balance (Hbar or int, optional): Initial balance in Hbar or tinybars.
            receiver_signature_required (bool, optional): Whether receiver signature is required.
            auto_renew_period (int, optional): Auto-renew period in seconds (default is ~90 days).
            memo (str, optional): Memo for the account.
        """
        super().__init__()
        self.key = key
        self.initial_balance = initial_balance
        self.receiver_signature_required = receiver_signature_required
        self.auto_renew_period = auto_renew_period
        self.account_memo = memo
        self._default_transaction_fee = 300_000_000

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

    def set_auto_renew_period(self, seconds: Union[int,Duration]) -> "AccountCreateTransaction":
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

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for account creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the account creation details.

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

        crypto_create_body = crypto_create_pb2.CryptoCreateTransactionBody(
            key=self.key._to_proto(),
            initialBalance=initial_balance_tinybars,
            receiverSigRequired=self.receiver_signature_required,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds),
            memo=self.account_memo
        )

        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.cryptoCreateAccount.CopyFrom(crypto_create_body)

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method for executing the account creation transaction.
        Args:
            channel (_Channel): The channel to use for the transaction.
        Returns:
            _Method: An instance of _Method containing the transaction and query functions.
        """
        return _Method(
            transaction_func=channel.crypto.createAccount,
            query_func=None
        )