from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_create_topic_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TopicCreateTransaction(Transaction):
    def __init__(self, memo=None, admin_key=None, submit_key=None, auto_renew_period: Duration=None, auto_renew_account=None):
        super().__init__()
        self.memo = memo or ""
        self.admin_key = admin_key
        self.submit_key = submit_key
        self.auto_renew_period: Duration = auto_renew_period or Duration(7890000)
        self.auto_renew_account = auto_renew_account
        self.transaction_fee = 10_000_000

    def set_memo(self, memo):
        self._require_not_frozen()
        self.memo = memo
        return self

    def set_admin_key(self, key):
        self._require_not_frozen()
        self.admin_key = key
        return self

    def set_submit_key(self, key):
        self._require_not_frozen()
        self.submit_key = key
        return self

    def set_auto_renew_period(self, seconds: Duration | int):
        self._require_not_frozen()
        if isinstance(seconds, int):
            self.auto_renew_period = Duration(seconds)
        elif isinstance(seconds, Duration):
            self.auto_renew_period = seconds
        else:
            raise TypeError("Duration of invalid type")
        return self

    def set_auto_renew_account(self, account_id):
        self._require_not_frozen()
        self.auto_renew_account = account_id
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for topic creation.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic creation details.

        Raises:
            ValueError: If required fields are missing.
        """
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusCreateTopic.CopyFrom(consensus_create_topic_pb2.ConsensusCreateTopicTransactionBody(
            adminKey=self.admin_key._to_proto() if self.admin_key is not None else None,
            submitKey=self.submit_key._to_proto() if self.submit_key is not None else None,
            autoRenewPeriod=self.auto_renew_period._to_proto() if self.auto_renew_period is not None else None,
            autoRenewAccount=self.auto_renew_account._to_proto() if self.auto_renew_account is not None else None,
            memo=self.memo
        ))

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.topic.createTopic,
            query_func=None
        )
