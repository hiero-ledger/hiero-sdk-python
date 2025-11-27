import math
from typing import List, Optional
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.custom_fee_limit import CustomFeeLimit
from hiero_sdk_python.hapi.services import consensus_submit_message_pb2, timestamp_pb2
from hiero_sdk_python.hapi.services import transaction_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.transaction.transaction_id import TransactionId


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
        chunk_size: Optional[int] = None,
        max_chunks: Optional[int] = None
    ) -> None:
        """
        Initializes a new TopicMessageSubmitTransaction instance.
        Args:
            topic_id (Optional[TopicId]): The ID of the topic.
            message (Optional[str]): The message to submit.
            chunk_size (Optional[int]): The maximum chunk size in bytes, Default: 1024.
            max_chunks (Optional[int]): The maximum number of chunks allowed, Default: 20.
        """
        super().__init__()
        self.topic_id: Optional[TopicId] = topic_id
        self.message: Optional[str] = message
        self.chunk_size: int = chunk_size or 1024
        self.max_chunks: int = max_chunks or 20

        self._current_index = 0
        self._total_chunks = self.get_required_chunks()
        self._initial_transaction_id: Optional[TransactionId] = None
        self._transaction_ids: List[TransactionId] = []
        self._signing_keys: List["PrivateKey"] = []

    def get_required_chunks(self) -> int:
        """
        Returns the number of chunks required for the current message.
        
        Returns:
            int: Number of chunks required.
        """
        if not self.message:
            return 1

        content = self.message.encode("utf-8")
        return math.ceil(len(content) / self.chunk_size)

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
        self._total_chunks = self.get_required_chunks()
        return self

    def set_chunk_size(self, chunk_size: int) -> "TopicMessageSubmitTransaction":
        """
        Set maximum chunk size in bytes.
        
        Args:
            chunk_size (int):  The size of each chunk in bytes.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self.chunk_size = chunk_size
        self._total_chunks = self.get_required_chunks()
        return self

    def set_max_chunks(self, max_chunks: int) -> "TopicMessageSubmitTransaction":
        """
        Set maximum allowed chunks.

        Args:
            max_chunks (int): The maximum number of chunks allowed.

        Returns:
            TopicMessageSubmitTransaction: This transaction instance (for chaining).
        """
        self._require_not_frozen()
        if max_chunks <= 0:
            raise ValueError("max_chunks must be positive")

        self.max_chunks = max_chunks
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

    def _validate_chunking(self) -> None:
        """
        Validates that chunk count does not exceed max_chunks.

        Raises:
            ValueError: If chunk count exceeds `max_chunks`.
        """
        required = self.get_required_chunks()

        if self.max_chunks and required > self.max_chunks:
            raise ValueError(
                f"Message requires {required} chunks but max_chunks={self.max_chunks}. "
                f"Increase limit with set_max_chunks()."
            )

    def _build_proto_body(self) -> consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody:
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

        content = self.message.encode("utf-8")

        start_index = self._current_index * self.chunk_size
        end_index = min(start_index + self.chunk_size, len(content))
        chunk_content = content[start_index:end_index]


        body = consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
            topicID=self.topic_id._to_proto(),
            message=chunk_content
        )

        # Multi-chunk metadata
        if self._total_chunks > 1:
            body.chunkInfo.CopyFrom(consensus_submit_message_pb2.ConsensusMessageChunkInfo(
                initialTransactionID=self._initial_transaction_id._to_proto(),
                total=self._total_chunks,
                number=self._current_index + 1
            ))

        return body

    def build_transaction_body(self) -> transaction_pb2.TransactionBody:
        """
        Builds and returns the protobuf transaction body for message submission.

        Returns:
            TransactionBody: The protobuf transaction body containing 
                the message submission details.
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

    def freeze_with(self, client: "Client") -> "TopicMessageSubmitTransaction":
        if self._transaction_body_bytes:
            return self

        if self.transaction_id is None:
            self.transaction_id = client.generate_transaction_id()

        if not self._transaction_ids:
            base_timestamp = self.transaction_id.valid_start

            for i in range(self.get_required_chunks()):
                if i == 0:
                    if self._initial_transaction_id is None:
                        self._initial_transaction_id = self.transaction_id

                    chunk_transaction_id = self.transaction_id
                else:
                    chunk_valid_start = timestamp_pb2.Timestamp(
                        seconds=base_timestamp.seconds,
                        nanos=base_timestamp.nanos + i
                    )
                    chunk_transaction_id = TransactionId(
                        account_id=self.transaction_id.account_id,
                        valid_start=chunk_valid_start
                    )

                self._transaction_ids.append(chunk_transaction_id)

        return super().freeze_with(client)


    def execute(self, client: "Client"):
        self._validate_chunking()

        if self.get_required_chunks() == 1:
            return super().execute(client)

        # Multi-chunk transaction - execute all chunks
        responses = []

        for chunk_index in range(self.get_required_chunks()):
            self._current_index = chunk_index

            if self._transaction_ids and chunk_index < len(self._transaction_ids):
                self.transaction_id = self._transaction_ids[chunk_index]

            self._transaction_body_bytes.clear()
            self._signature_map.clear()

            self.freeze_with(client)

            for signing_key in self._signing_keys:
                super().sign(signing_key)

            # Execute the chunk
            response = super().execute(client)
            responses.append(response)

        # Return the first response as the JS SDK does
        return responses[0] if responses else None

    def sign(self, private_key: "PrivateKey"):
        """
        Signs the transaction using the provided private key.
            
        For multi-chunk transactions, this stores the signing key for later use.
        
        Args:
            private_key (PrivateKey): The private key to sign the transaction with.
        """
        if private_key not in self._signing_keys:
            self._signing_keys.append(private_key)

        super().sign(private_key)
        return self
