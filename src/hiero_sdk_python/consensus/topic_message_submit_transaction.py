"""
This module provides the `TopicMessageSubmitTransaction` class for submitting
messages to Hedera Consensus Service topics using the Hiero SDK.
"""
from typing import Optional

from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from hiero_sdk_python.hapi.services import consensus_submit_message_pb2
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method


class TopicMessageSubmitTransaction(Transaction):
    """
        Represents a transaction that submits a message to a Hedera Consensus Service topic.

        Allows setting the target topic ID and message, building the transaction body,
        and executing the submission through a network channel.
    """

    def __init__(
        self,
        topic_id: Optional[TopicId] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Initializes a new TopicMessageSubmitTransaction instance.
        Args:
            topic_id (Optional[TopicId]): The ID of the topic.
            message (Optional[str]): The message to submit.
        """
        super().__init__()
        self.topic_id: Optional[TopicId] = topic_id
        self.message: Optional[str] = message

    def set_topic_id(
        self, topic_id: TopicId
    ) -> "TopicMessageSubmitTransaction":
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

    def set_custom_fee_limits(
        self, custom_fee_limits: list["CustomFeeLimit"]
    ) -> "TopicMessageSubmitTransaction":
        """
        Sets the maximum custom fees that the user is willing to pay for the message.

        Args:
            custom_fee_limits (List[CustomFeeLimit]): The list of custom fee limits to set.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.custom_fee_limits = custom_fee_limits
        return self

    def add_custom_fee_limit(
        self, custom_fee_limit: "CustomFeeLimit"
    ) -> "TopicMessageSubmitTransaction":
        """
        Adds a maximum custom fee that the user is willing to pay for the message.

        Args:
            custom_fee_limit (CustomFeeLimit): The custom fee limit to add.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.custom_fee_limits.append(custom_fee_limit)
        return self

    def _build_proto_body(
        self,
    ) -> consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody:
        """
        Returns the protobuf body for the topic message submit transaction.
        
        Returns:
            ConsensusSubmitMessageTransactionBody: The protobuf body for this transaction.
            
        Raises:
            ValueError: If required fields (topic_id, message) are missing.
        """
        if self.topic_id is None:
            raise ValueError("Missing required fields: topic_id.")
        if self.message is None:
            raise ValueError("Missing required fields: message.")

        return consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
            topicID=self.topic_id._to_proto(),
            message=bytes(self.message, "utf-8"),
        )
    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for message submission.

        Returns:
            TransactionBody: The protobuf transaction body containing the message submission details.
        """
        consensus_submit_message_body = self._build_proto_body()
        transaction_body = self.build_base_transaction_body()
        transaction_body.consensusSubmitMessage.CopyFrom(consensus_submit_message_body)
        return transaction_body

    def build_scheduled_body(self) -> SchedulableTransactionBody:
        """
        Builds the scheduled transaction body for this topic message submit transaction.

        Returns:
            SchedulableTransactionBody: The built scheduled transaction body.
        """
        consensus_submit_message_body = self._build_proto_body()
        schedulable_body = self.build_base_scheduled_body()
        schedulable_body.consensusSubmitMessage.CopyFrom(consensus_submit_message_body)
        return schedulable_body

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the gRPC method for executing this transaction.

        Args:
            channel (_Channel): The channel used to access the network.

        Returns:
            _Method: The method object with bound transaction execution.
        """
        return _Method(
            transaction_func=channel.topic.submitMessage,
            query_func=None
        )
