from hiero_sdk_python.duration import Duration
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_update_topic_pb2, duration_pb2
from google.protobuf import wrappers_pb2 as _wrappers_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TopicUpdateTransaction(Transaction):
    def __init__(
        self,
        topic_id=None,
        memo=None,
        admin_key=None,
        submit_key=None,
        auto_renew_period: Duration = Duration(7890000),
        auto_renew_account=None,
        expiration_time=None,
    ):
        super().__init__()
        self.topic_id = topic_id
        self.memo = memo or ""
        self.admin_key = admin_key
        self.submit_key = submit_key
        self.auto_renew_period:Duration = auto_renew_period
        self.auto_renew_account = auto_renew_account
        self.expiration_time = expiration_time
        self.transaction_fee = 10_000_000

    def set_topic_id(self, topic_id):
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

    def set_memo(self, memo):
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

    def set_admin_key(self, key):
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

    def set_submit_key(self, key):
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

    def set_auto_renew_period(self, seconds: Duration | int):
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

    def set_auto_renew_account(self, account_id):
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

    def set_expiration_time(self, expiration_time):
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

    def build_transaction_body(self):
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
            topicID=self.topic_id.to_proto(),
            adminKey=self.admin_key.to_proto() if self.admin_key else None,
            submitKey=self.submit_key.to_proto() if self.submit_key else None,
            autoRenewPeriod=duration_pb2.Duration(seconds=self.auto_renew_period.seconds) if self.auto_renew_period else None,
            autoRenewAccount=self.auto_renew_account.to_proto() if self.auto_renew_account else None,
            expirationTime=self.expiration_time.to_proto() if self.expiration_time else None,
            memo=_wrappers_pb2.StringValue(value=self.memo) if self.memo else None
        ))

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.topic.updateTopic,
            query_func=None
        )
