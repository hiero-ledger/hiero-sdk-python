from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_delete_topic_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TopicDeleteTransaction(Transaction):
    def __init__(self, topic_id=None):
        super().__init__()
        self.topic_id = topic_id
        self.transaction_fee = 10_000_000

    def set_topic_id(self, topic_id):
        """
        Sets the topic ID for the transaction.
        
        Args:
            topic_id: The topic ID to delete.

        Returns:
            TopicDeleteTransaction: Returns the instance for method chaining.
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def build_transaction_body(self):
        """
        Builds and returns the protobuf transaction body for topic delete.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic delete details.

        Raises:
            ValueError: If required fields are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id")
    
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusDeleteTopic.CopyFrom(consensus_delete_topic_pb2.ConsensusDeleteTopicTransactionBody(
            topicID=self.topic_id._to_proto()
        ))

        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.topic.deleteTopic,
            query_func=None
        )