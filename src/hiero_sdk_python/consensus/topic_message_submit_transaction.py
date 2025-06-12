from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import consensus_submit_message_pb2, basic_types_pb2, transaction_body_pb2
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method

class TopicMessageSubmitTransaction(Transaction):
    def __init__(self, topic_id: basic_types_pb2.TopicID = None, message: str = None) -> None:
        """
        Initializes a new TopicMessageSubmitTransaction instance.
        
        Args:
            topic_id (TopicId, optional): The ID of the topic.
            message (str, optional): The message to submit.
        """
        super().__init__()
        self.topic_id: basic_types_pb2.TopicID = topic_id
        self.message: str = message

    def set_topic_id(self, topic_id: basic_types_pb2.TopicID) -> "TopicMessageSubmitTransaction":
        """
        Sets the topic ID for the message submission.

        Args:
            topic_id (TopicId): The ID of the topic to which the message is submitted.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def set_message(self, message: str) -> "TopicMessageSubmitTransaction":
        """
        Sets the message to submit to the topic.

        Args:
            message (str): The message to submit to the topic.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.message = message
        return self

    def build_transaction_body(self) -> transaction_body_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for message submission.
        Raises ValueError if required fields (topic_id, message) are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id.")
        if self.message is None:
            raise ValueError("Missing required fields: message.")

        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusSubmitMessage.CopyFrom(
            consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
                topicID=self.topic_id._to_proto(),
                message=bytes(self.message, 'utf-8')
            )
        )
        return transaction_body

    def _get_method(self, channel: _Channel) -> _Method:
        return _Method(
            transaction_func=channel.topic.submitMessage,
            query_func=None
        )
