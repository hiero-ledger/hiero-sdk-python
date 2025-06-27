from typing import Union

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import (
    basic_types_pb2, 
    consensus_update_topic_pb2,
    duration_pb2, 
    timestamp_pb2, 
    transaction_body_pb2
)
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.account.account_id import AccountId

class TopicUpdateTransaction(Transaction):
    def __init__(
        self,
        topic_id: basic_types_pb2.TopicID =None,
        memo: str = None,
        admin_key: basic_types_pb2.Key = None,
        submit_key: basic_types_pb2.Key = None,
        auto_renew_period: Duration = Duration(7890000),
        auto_renew_account: AccountId = None,
        expiration_time: timestamp_pb2.Timestamp = None,
    ) -> None:
        """
        Initializes a new instance of the TopicUpdateTransaction class.
        Args:
            topic_id (basic_types_pb2.TopicID): The ID of the topic to update.
            memo (str): The memo associated with the topic.
            admin_key (basic_types_pb2.Key): The admin key for the topic.
            submit_key (basic_types_pb2.Key): The submit key for the topic.
            auto_renew_period (Duration): The auto-renew period for the topic.
            auto_renew_account (AccountId): The account ID for auto-renewal.
            expiration_time (timestamp_pb2.Timestamp): The expiration time of the topic.
        """
        super().__init__()
        self.topic_id: basic_types_pb2.TopicID = topic_id
        self.memo: str = memo or ""
        self.admin_key: basic_types_pb2.Key = admin_key
        self.submit_key: basic_types_pb2.Key = submit_key
        self.auto_renew_period: Duration = auto_renew_period
        self.auto_renew_account: AccountId = auto_renew_account
        self.expiration_time: timestamp_pb2.Timestamp = expiration_time
        self.transaction_fee: int = 10_000_000

    def set_topic_id(self, topic_id: basic_types_pb2.TopicID) -> "TopicUpdateTransaction":
        """
        Sets the topic ID for the transaction.

        Args:
            topic_id: The topic ID to update.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def set_memo(self, memo: str) -> "TopicUpdateTransaction":
        """
        Sets the memo for the topic.

        Args:
            memo: The memo to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.memo = memo
        return self

    def set_admin_key(self, key: basic_types_pb2.Key) -> "TopicUpdateTransaction":
        """
        Sets the admin key for the topic.

        Args:
            key: The admin key to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key: basic_types_pb2.Key) -> "TopicUpdateTransaction":
        """
        Sets the submit key for the topic.

        Args:
            key: The submit key to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Union[Duration, int]) -> "TopicUpdateTransaction":
        """
        Sets the auto-renew period for the topic.

        Args:
            seconds: The auto-renew period in seconds.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_auto_renew_account(self, account_id: AccountId) -> "TopicUpdateTransaction":
        """
        Sets the auto-renew account for the topic.

        Args:
            account_id: The account ID to set as the auto-renew account.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.auto_renew_account = account_id
        return self

    def set_expiration_time(self, expiration_time: timestamp_pb2.Timestamp) -> "TopicUpdateTransaction":
        """
        Sets the expiration time for the topic.

        Args:
            expiration_time: The expiration time to set.

        Returns:
            TopicUpdateTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.expiration_time = expiration_time
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for topic update.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic update details.

        Raises:
            ValueError: If required fields are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id")

        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusUpdateTopic.CopyFrom(consensus_update_topic_pb2.ConsensusUpdateTopicTransactionBody(
            topicID=self.topic_id._to_proto(),
            adminKey=self.admin_key._to_proto() if self.admin_key else None,
            submitKey=self.submit_key._to_proto() if self.submit_key else None,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds) if self.auto_renew_period else None,
            autoRenewAccount=self.auto_renew_account._to_proto() if self.auto_renew_account else None,
            expirationTime=self.expiration_time._to_proto() if self.expiration_time else None,
            memo=_wrappers_pb2.StringValue(value=self.memo) if self.memo else None
        ))

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method for executing the topic update transaction.
        Args:
            channel (_Channel): The channel to use for the transaction.
        Returns:
            _Method: The method to execute the transaction.
        """
        return _Method(
            transaction_func=channel.topic.updateTopic,
            query_func=None
        )
