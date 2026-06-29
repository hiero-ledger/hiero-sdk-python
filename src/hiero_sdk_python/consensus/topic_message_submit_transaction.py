from __future__ import annotations

import math

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import consensus_submit_message_pb2, transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.transaction.chunked_transaction import ChunkedTransaction
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit


class TopicMessageSubmitTransaction(ChunkedTransaction):
    """
    Represents a transaction that submits a message to a Hedera Consensus Service topic.

    Allows setting the target topic ID and message, building the transaction body,
    and executing the submission through a network channel.

    Supports automatic chunking for large messages.
    """

    def __init__(
        self,
        topic_id: TopicId | None = None,
        message: bytes | str | None = None,
        chunk_size: int | None = None,
        max_chunks: int | None = None,
    ) -> None:
        """
        Initializes a new TopicMessageSubmitTransaction instance.

        Args:
            topic_id (TopicId, optional): The ID of the topic.
            message (str, optional): The message to submit.
            chunk_size (int, optional): The maximum chunk size in bytes. Default: 1024.
            max_chunks (int, optional): The maximum number of chunks allowed. Default: 20.
        """
        super().__init__()
        self.topic_id: TopicId | None = topic_id
        self.message: bytes | str | None = message
        self.chunk_size: int = 1024
        self.max_chunks: int = 20
        if chunk_size is not None:
            super().set_chunk_size(chunk_size)

        if max_chunks is not None:
            super().set_max_chunks(max_chunks)

        self._total_chunks = self.get_required_chunks()

    def _message_as_bytes(self) -> bytes:
        """
        Returns the message encoded as bytes for chunking and protobuf serialization.

        Returns:
            bytes: The message as bytes.
        """
        if self.message is None:
            return b""

        return self.message.encode("utf-8") if isinstance(self.message, str) else self.message

    def get_required_chunks(self) -> int:
        """
        Returns the number of chunks required for the current message.

        Returns:
            int: Number of chunks required.
        """
        if not self.message:
            return 1

        content = self._message_as_bytes()
        return math.ceil(len(content) / self.chunk_size)

    def set_topic_id(self, topic_id: TopicId) -> TopicMessageSubmitTransaction:
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

    def set_message(self, message: bytes | str) -> TopicMessageSubmitTransaction:
        """
        Sets the message to submit to the topic.

        Args:
            message (str): The message to submit to the topic.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.message = message
        self._total_chunks = self.get_required_chunks()
        return self

    def set_chunk_size(self, chunk_size: int) -> TopicMessageSubmitTransaction:
        """
        Set maximum chunk size in bytes.

        Args:
            chunk_size (int): The size of each chunk in bytes.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        super().set_chunk_size(chunk_size)
        self._total_chunks = self.get_required_chunks()
        return self

    def set_max_chunks(self, max_chunks: int) -> TopicMessageSubmitTransaction:
        """
        Set maximum allowed chunks.

        Args:
            max_chunks (int): The maximum number of chunks allowed.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        super().set_max_chunks(max_chunks)
        return self

    def set_custom_fee_limits(self, custom_fee_limits: list[CustomFeeLimit]) -> TopicMessageSubmitTransaction:
        """
        Sets the maximum custom fees that the user is willing to pay for the message.

        Args:
            custom_fee_limits (list[CustomFeeLimit]): The list of custom fee limits to set.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        self.custom_fee_limits = custom_fee_limits
        return self

    def add_custom_fee_limit(self, custom_fee_limit: CustomFeeLimit) -> TopicMessageSubmitTransaction:
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

    def _build_proto_body(self) -> consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody:
        """
        Returns the protobuf body for the topic message submit transaction.

        Returns:
            ConsensusSubmitMessageTransactionBody: The protobuf body for this transaction.

        Raises:
            ValueError: If required fields (message) are missing.
        """
        if self.message is None or self.message == "":
            raise ValueError("Missing required fields: message.")

        content = self._message_as_bytes()

        start_index = self._current_chunk_index * self.chunk_size
        end_index = min(start_index + self.chunk_size, len(content))
        chunk_content = content[start_index:end_index]

        body = consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
            topicID=self.topic_id._to_proto() if self.topic_id else None, message=chunk_content
        )

        # Multi-chunk metadata
        if self._total_chunks > 1:
            body.chunkInfo.CopyFrom(
                consensus_submit_message_pb2.ConsensusMessageChunkInfo(
                    initialTransactionID=self._initial_transaction_id._to_proto(),
                    total=self._total_chunks,
                    number=self._current_chunk_index + 1,
                )
            )

        return body

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
        return _Method(transaction_func=channel.topic.submitMessage, query_func=None)

    def sign(self, private_key: PrivateKey) -> TopicMessageSubmitTransaction:
        """
        Signs the transaction using the provided private key.

        Args:
            private_key (PrivateKey): The private key to sign the transaction with.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        super().sign(private_key)
        return self
