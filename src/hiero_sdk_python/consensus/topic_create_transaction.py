from typing import Union, Optional

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_create_topic_pb2, transaction_body_pb2, basic_types_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.account.account_id import AccountId

class TopicCreateTransaction(Transaction):
    def __init__(
        self,
        memo: Optional[str] = None,
        admin_key: Optional[basic_types_pb2.Key] = None,
        submit_key: Optional[basic_types_pb2.Key] = None,
        auto_renew_period: Duration = None,
        auto_renew_account: AccountId = None
    ) -> None:
        """
        Initializes a new instance of the TopicCreateTransaction class.
        Args:
            memo (str): Optional memo for the topic.
            admin_key (Key): Optional admin key for the topic.
            submit_key (Key): Optional submit key for the topic.
            auto_renew_period (Duration): Optional auto-renew period for the topic.
            auto_renew_account (AccountId): Optional account ID for auto-renewal.
        """
        super().__init__()
        self.memo = memo or ""
        self.admin_key: Optional[basic_types_pb2.Key] = admin_key
        self.submit_key: Optional[basic_types_pb2.Key] = submit_key
        self.auto_renew_period: Duration = auto_renew_period or Duration(7890000)
        self.auto_renew_account: AccountId = auto_renew_account
        self.transaction_fee: int = 10_000_000

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

    def set_admin_key(self, key: basic_types_pb2.Key) -> "TopicCreateTransaction":
        """
        Sets the admin key for the topic creation transaction.
        Args:
            key (basic_types_pb2.Key): The admin key to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key: basic_types_pb2.Key) -> "TopicCreateTransaction":
        """
        Sets the submit key for the topic creation transaction.
        Args:
            key (basic_types_pb2.Key): The submit key to set for the topic.
        Returns:
            TopicCreateTransaction: The current instance for method chaining.
        """
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Union[Duration,int]) -> "TopicCreateTransaction":
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

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for topic creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic creation details.

        Raises:
            ValueError: If required fields are missing.
        """
        transaction_body: transaction_body_pb2.TransactionBody = self.build_base_transaction_body()
        transaction_body.consensusCreateTopic.CopyFrom(consensus_create_topic_pb2.ConsensusCreateTopicTransactionBody(
            adminKey=self.admin_key._to_proto() if self.admin_key is not None else None,
            submitKey=self.submit_key._to_proto() if self.submit_key is not None else None,
            autoRenewPeriod=self.auto_renew_period._to_proto() if self.auto_renew_period is not None else None,
            autoRenewAccount=self.auto_renew_account._to_proto() if self.auto_renew_account is not None else None,
            memo=self.memo
        ))

        return transaction_body

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
