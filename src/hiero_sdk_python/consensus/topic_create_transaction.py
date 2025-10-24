"""
This module defines the TopicCreateTransaction class for creating topics
on the Hedera Consensus Service (HCS) using the Hiero Python SDK.

It provides methods to set properties such as memo, admin key, submit key,
auto-renew period, and auto-renew account, and to build the protobuf
transaction body for submission to the Hedera network .
"""

from typing import List, Union, Optional
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import (
    consensus_create_topic_pb2,
    transaction_pb2)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.public_key import PublicKey


class TopicCreateTransaction(Transaction):
    """
        Represents a transaction to create a new topic in the Hedera
        Consensus Service (HCS).

        This transaction can optionally define an admin key, submit key,
        auto-renew period, auto-renew account, and memo.
    """
    def __init__(
        self,
        memo: Optional[str] = None,
        admin_key: Optional[PublicKey] = None,
        submit_key: Optional[PublicKey] = None,
        auto_renew_period: Optional[Duration] = None,
        auto_renew_account: Optional[AccountId] = None,
        custom_fees: Optional[List[CustomFixedFee]] = None,
        fee_schedule_key: Optional[PublicKey] = None,
        fee_exempt_keys: Optional[List[PublicKey]] = None,
    ) -> None:
        """
        Initializes a new instance of the TopicCreateTransaction class.

        Args:
            memo (Optional[str]): Optional memo for the topic.
            admin_key (Optional[PublicKey]): Optional public admin key for the topic.
            submit_key (Optional[PublicKey]): Optional public submit key for the topic.
            auto_renew_period (Optional[Duration]): Optional auto-renew period for the topic.
            auto_renew_account (Optional[AccountId]): Optional account ID for auto-renewal.
            custom_fees (list[CustomFixedFee]): Optional list of custom fees for the topic.
            fee_schedule_key (PublicKey): Optional fee schedule key for the topic.
            fee_exempt_keys (list[PublicKey]): Optional list of fee exempt keys for the topic.
        """
        super().__init__()
        self.memo: str = memo or ""
        self.admin_key: Optional[PublicKey] = admin_key
        self.submit_key: Optional[PublicKey] = submit_key
        self.auto_renew_period: Duration = auto_renew_period or Duration(7890000)
        self.auto_renew_account: Optional[AccountId] = auto_renew_account
        self.transaction_fee: Optional[int] = 2_000_000_000 # 20 Hbars
        self.custom_fees: List[CustomFixedFee] = custom_fees or []
        self.fee_exempt_keys: List[PublicKey] = fee_exempt_keys or []
        self.fee_schedule_key: PublicKey = fee_schedule_key

    def set_memo(self, memo: str) -> "TopicCreateTransaction":
        """
        Sets the memo for the topic creation transaction.
        Args:
            memo (str): The memo to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.memo = memo
        return self

    def set_admin_key(self, key: PublicKey) -> "TopicCreateTransaction":
        """
        Sets the admin key for the topic creation transaction.
        Args:
            key (PublicKey): The public admin key to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key: PublicKey) -> "TopicCreateTransaction":
        """
        Sets the submit key for the topic creation transaction.
        Args:
            key (PublicKey): The public submit key to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Union[Duration, int]) -> "TopicCreateTransaction":
        """
        Sets the auto-renew period for the topic creation transaction.
        Args:
            seconds (Union[Duration, int]): The auto-renew period in seconds or a Duration object.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        Raises:
            TypeError: If the provided duration is of an invalid type.
        """
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_auto_renew_account(self, account_id: AccountId) -> "TopicCreateTransaction":
        """
        Sets the account ID for auto-renewal of the topic.
        Args:
            account_id (AccountId): The account ID to set for auto-renewal.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.auto_renew_account = account_id
        return self

    def set_custom_fees(self, custom_fees: List[CustomFixedFee]) -> "TopicCreateTransaction":
        """
        Sets the custom fees for the topic creation transaction.
        Args:
            custom_fees (List[CustomFixedFee]): The custom fees to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.custom_fees = custom_fees
        return self


    def set_fee_schedule_key(self, key: PublicKey) -> "TopicCreateTransaction":
        """
        Sets the fee schedule key for the topic creation transaction.
        Args:
            key (PublicKey): The fee schedule key to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.fee_schedule_key = key
        return self

    def set_fee_exempt_keys(self, keys: List[PublicKey]) -> "TopicCreateTransaction":
        """
        Sets the fee exempt keys for the topic creation transaction.
        Args:
            keys (List[PublicKey]): The fee exempt keys to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.fee_exempt_keys = keys
        return self

    def _build_proto_body(self) -> consensus_create_topic_pb2.ConsensusCreateTopicTransactionBody:
        """
        Returns the protobuf body for the topic create transaction.
        
        Returns:
            ConsensusCreateTopicTransactionBody: The protobuf body for this transaction.
        """
        return consensus_create_topic_pb2.ConsensusCreateTopicTransactionBody(
            adminKey=(
                self.admin_key._to_proto()
                if self.admin_key is not None
                else None),
            submitKey=(
                self.submit_key._to_proto()
                if self.submit_key is not None
                else None),
            autoRenewPeriod=(
                self.auto_renew_period._to_proto()
                if self.auto_renew_period is not None
                else None),
            autoRenewAccount=(
                self.auto_renew_account._to_proto()
                if self.auto_renew_account is not None
                else None),
            memo=self.memo,
            custom_fees=[custom_fee._to_topic_fee_proto() for custom_fee in self.custom_fees],
            fee_schedule_key=self.fee_schedule_key._to_proto() if self.fee_schedule_key else None,
            fee_exempt_key_list=[key._to_proto() for key in self.fee_exempt_keys],
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for topic creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic creation details.
        """
        consensus_create_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusCreateTopic.CopyFrom(consensus_create_body)
        return transaction_body
    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this topic create transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        consensus_create_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.consensusCreateTopic.CopyFrom(consensus_create_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method to be used for executing the transaction.
        Args:
            channel (_Channel): The channel to be used for the transaction.
        Returns:
            _Method: The method for executing the transaction.
        """
        return _Method(
            transaction_func=channel.topic.createTopic,
            query_func=None
        )
