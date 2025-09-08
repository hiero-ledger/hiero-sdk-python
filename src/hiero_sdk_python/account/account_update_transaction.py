# pylint: disable=too-many-instance-attributes
"""
AccountUpdateTransaction class, which is used to update an account on the network.
"""

from dataclasses import dataclass
from typing import Optional

from google.protobuf.wrappers_pb2 import BoolValue, StringValue

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services.crypto_update_pb2 import CryptoUpdateTransactionBody
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction import Transaction

AUTO_RENEW_PERIOD = Duration(7890000)  # around 90 days in seconds


@dataclass
class AccountUpdateParams:
    """
    Represents account attributes that can be updated.

    Attributes:
        account_id (Optional[AccountId]): The account ID to update.
        key (Optional[PublicKey]): The new key for the account.
        auto_renew_period (Duration): The new auto-renew period.
        account_memo (Optional[str]): The new memo for the account.
        receiver_signature_required (Optional[bool]): Whether receiver signature is required.
        expiration_time (Optional[Timestamp]): The new expiration time for the account.
    """

    account_id: Optional[AccountId] = None
    key: Optional[PublicKey] = None
    auto_renew_period: Duration = AUTO_RENEW_PERIOD
    account_memo: Optional[str] = None
    receiver_signature_required: Optional[bool] = None
    expiration_time: Optional[Timestamp] = None


class AccountUpdateTransaction(Transaction):
    """
    Represents an account update transaction on the network.

    This transaction updates metadata and/or configuration of an existing account.
    If a given field is not set in the transaction body, the corresponding account
    attribute remains unchanged. Only appropriate signers may update account state.
    """

    def __init__(self, account_params: Optional[AccountUpdateParams] = None):
        """
        Initialize a new `AccountUpdateTransaction`.

        Args:
            account_params (Optional[AccountUpdateParams]): Optional bag of parameters
                to pre-populate the transaction. You may also set fields via setters.
        """
        super().__init__()
        params = account_params or AccountUpdateParams()
        self.account_id = params.account_id
        self.key = params.key
        self.auto_renew_period = params.auto_renew_period
        self.account_memo = params.account_memo
        self.receiver_signature_required = params.receiver_signature_required
        self.expiration_time = params.expiration_time

    def set_account_id(
        self, account_id: Optional[AccountId]
    ) -> "AccountUpdateTransaction":
        """
        Sets the `AccountId` that will be updated.

        Args:
            account_id (Optional[AccountId]): The ID of the account to update.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_id = account_id
        return self

    def set_key(self, key: Optional[PublicKey]) -> "AccountUpdateTransaction":
        """
        Sets the new account key (public key) for key rotation.

        Args:
            key (Optional[PublicKey]): The new public key for the account.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.key = key
        return self

    def set_auto_renew_period(
        self, auto_renew_period: Optional[Duration]
    ) -> "AccountUpdateTransaction":
        """
        Sets the auto-renew period for the account.

        Args:
            auto_renew_period (Optional[Duration]): The new auto-renew period.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.auto_renew_period = auto_renew_period
        return self

    def set_account_memo(
        self, account_memo: Optional[str]
    ) -> "AccountUpdateTransaction":
        """
        Sets the account memo (UTF-8, network enforced size limits apply).

        Args:
            account_memo (Optional[str]): The new account memo.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.account_memo = account_memo
        return self

    def set_receiver_signature_required(
        self, receiver_signature_required: Optional[bool]
    ) -> "AccountUpdateTransaction":
        """
        Sets whether the account requires receiver signatures for transfers.

        Args:
            receiver_signature_required (Optional[bool]): True if required, False otherwise.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.receiver_signature_required = receiver_signature_required
        return self

    def set_expiration_time(
        self, expiration_time: Optional[Timestamp]
    ) -> "AccountUpdateTransaction":
        """
        Sets the account expiration time.

        Args:
            expiration_time (Optional[Timestamp]): The new expiration timestamp.

        Returns:
            AccountUpdateTransaction: This transaction instance.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def _build_proto_body(self):
        """
        Returns the protobuf body for the account update transaction.

        Returns:
            CryptoUpdateTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If account_id is not set.
        """
        if self.account_id is None:
            raise ValueError("Missing required AccountID to update")

        return CryptoUpdateTransactionBody(
            accountIDToUpdate=self.account_id._to_proto(),
            key=self.key._to_proto() if self.key else None,
            memo=(
                StringValue(value=self.account_memo)
                if self.account_memo is not None
                else None
            ),
            autoRenewPeriod=(
                self.auto_renew_period._to_proto() if self.auto_renew_period else None
            ),
            expirationTime=(
                self.expiration_time._to_protobuf() if self.expiration_time else None
            ),
            receiverSigRequiredWrapper=(
                BoolValue(value=self.receiver_signature_required)
                if self.receiver_signature_required is not None
                else None
            ),
        )

    def build_transaction_body(self):
        """
        Builds the transaction body for this account update transaction.

        Returns:
            TransactionBody: The built protobuf `TransactionBody`.
        """
        crypto_update_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.cryptoUpdateAccount.CopyFrom(crypto_update_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this account update transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        crypto_update_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.cryptoUpdateAccount.CopyFrom(crypto_update_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Gets the method to execute the account update transaction.

        This internal method returns a `_Method` object containing the appropriate gRPC
        function to call when executing this transaction on the network.

        Args:
            channel (_Channel): The channel containing service stubs.

        Returns:
            _Method: An object containing the transaction function to update an account.
        """
        return _Method(transaction_func=channel.crypto.updateAccount, query_func=None)
