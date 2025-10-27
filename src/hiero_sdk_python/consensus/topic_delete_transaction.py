"""
This module provides the `TopicDeleteTransaction` class for deleting consensus topics
on the Hedera network using the Hiero SDK.

It handles setting the target topic ID, building the protobuf transaction body, and
defining the execution method required to perform the deletion transaction.
"""

from typing import Optional
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.hapi.services import (
    consensus_delete_topic_pb2,
    transaction_pb2
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method


class TopicDeleteTransaction(Transaction):
    """
        Represents a transaction to delete an existing topic in the Hedera
        Consensus Service (HCS).

    """

    def __init__(self, topic_id: Optional[TopicId] = None) -> None:
        super().__init__()
        self.topic_id: Optional[TopicId] = topic_id
        self.transaction_fee: int = 10_000_000

    def set_topic_id(self, topic_id:TopicId ) -> "TopicDeleteTransaction":
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

    def _build_proto_body(self) -> consensus_delete_topic_pb2.ConsensusDeleteTopicTransactionBody:
        """
        Returns the protobuf body for the topic delete transaction.
        
        Returns:
            ConsensusDeleteTopicTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If required fields are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id")

        return consensus_delete_topic_pb2.ConsensusDeleteTopicTransactionBody(
            topicID=self.topic_id._to_proto()
        )

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for topic delete.

        Returns:
            TransactionBody: The protobuf transaction body containing the topic delete details.
        """
        consensus_delete_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusDeleteTopic.CopyFrom(consensus_delete_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this topic delete transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        consensus_delete_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.consensusDeleteTopic.CopyFrom(consensus_delete_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the method for executing the topic delete transaction.
        Args:
            channel (_Channel): The channel to use for the transaction.
        Returns:
            _Method: The method to execute the transaction.
        """
        return _Method(
            transaction_func=channel.topic.deleteTopic,
            query_func=None
        )
