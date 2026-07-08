from __future__ import annotations

import math

from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import consensus_submit_message_pb2, transaction_pb2
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
            message (str or bytes, optional): The message to submit to the topic.
            chunk_size (int, optional): The maximum chunk size in bytes. Default: 1024.
            max_chunks (int, optional): The maximum number of chunks allowed. Default: 20.
        """
        super().__init__()
        self.topic_id: TopicId | None = topic_id
        self.message: bytes | str | None = message
        self.chunk_size: int = 1024
        self.max_chunks: int = 20
        if chunk_size is not None:
            self.set_chunk_size(chunk_size)

        if max_chunks is not None:
            self.set_max_chunks(max_chunks)

        self.message: str | None = message
        self.chunk_size: int = chunk_size or 1024
        self.max_chunks: int = max_chunks or 20

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
        self._initial_transaction_id: TransactionId | None = None
        self._current_chunk_index: int | None = None

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
            message (str or bytes): The message to submit to the topic.

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
        if not self.message:
            raise ValueError("Missing required fields: message.")

        content = self._message_as_bytes()

        if self._current_chunk_index is not None:
            chunk_info = consensus_submit_message_pb2.ConsensusMessageChunkInfo(
                initialTransactionID=self._initial_transaction_id._to_proto(),
                total=self._total_chunks,
                number=self._current_chunk_index + 1,
            )

            start_index = (self._current_chunk_index) * self.chunk_size
            end_index = min(start_index + self.chunk_size, len(content))

            chunk_content = content[start_index:end_index]

            return consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
                topicID=self.topic_id._to_proto() if self.topic_id else None,
                message=chunk_content,
                chunkInfo=chunk_info,
            )

        return consensus_submit_message_pb2.ConsensusSubmitMessageTransactionBody(
            topicID=self.topic_id._to_proto() if self.topic_id else None,
            message=content,
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
    def freeze_with(self, client: Client) -> TopicMessageSubmitTransaction:
        if self._transaction_body_bytes:
            return self

        self._resolve_transaction_id(client)
        self._resolve_node_ids(client)

        required_chunks = self.get_required_chunks()
        self._generate_transaction_ids(self._transaction_ids[0], required_chunks)

        self._initial_transaction_id = self._transaction_ids[0]

        for chunk in range(self.get_required_chunks()):
            self._current_transaction_id_index = chunk
            self._current_chunk_index = chunk

            node_bytes = {}

            for node_account_id in self.node_account_ids:
                self._node_account_id = node_account_id

                transaction_body = self.build_transaction_body()
                transaction_body.transactionID.CopyFrom(self._transaction_ids[chunk]._to_proto())
                transaction_body.nodeAccountID.CopyFrom(node_account_id._to_proto())

                node_bytes[node_account_id] = transaction_body.SerializeToString()

            self._transaction_body_bytes[self._transaction_ids[chunk]] = node_bytes

        return super().freeze_with(client)

    @overload
    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> TransactionReceipt: ...

    @overload
    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> TransactionResponse: ...

    def execute(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: bool = True,
        validate_status: bool = False,
    ) -> TransactionReceipt | TransactionResponse:
        """
        Executes the topic message submit transaction.

        For multi-chunk transactions, this method will execute all chunks sequentially and return first response.

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.
            wait_for_receipt (bool, optional): Whether to wait for consensus and return the receipt.
                If False, the method returns a TransactionResponse immediately after submission.
            validate_status: (bool):  Whether the query should automatically validate the transaction status (default False).

        Returns:
            TransactionReceipt: If wait_for_receipt is True (default)
            TransactionResponse: If wait_for_receipt is False
        """
        # Return the first response as the JS SDK does
        return self.execute_all(client, timeout, wait_for_receipt, validate_status)[0]

    @overload
    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[True] = True,
        validate_status: bool = False,
    ) -> list[TransactionReceipt]: ...

    @overload
    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: Literal[False] = False,
        validate_status: bool = False,
    ) -> list[TransactionResponse]: ...

    def execute_all(
        self,
        client: Client,
        timeout: int | float | None = None,
        wait_for_receipt: bool = True,
        validate_status: bool = False,
    ) -> list[TransactionReceipt] | list[TransactionResponse]:
        """
        Executes the topic message submit transaction.

        This method will execute all chunks sequentially and return list of all responses.

        Args:
            client: The client to execute the transaction with.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.
            wait_for_receipt (bool, optional): Whether to wait for consensus and return the receipt.
                If False, the method returns a TransactionResponse immediately after submission.
            validate_status: (bool):  Whether the query should automatically validate the transaction status (default False).

        Returns:
            List[TransactionReceipt]: If wait_for_receipt is True (default)
            List[TransactionResponse]: If wait_for_receipt is False
        """
        self._validate_chunking()

        if not self._transaction_body_bytes:
            self.freeze_with(client)

        if len(self._transaction_ids) == 1:
            return [super().execute(client, timeout, wait_for_receipt, validate_status)]

        # Multi-chunk transaction - execute all chunks
        responses = []
        self._current_transaction_id_index = 0
        for index in range(len(self._transaction_ids)):
            self._current_transaction_id_index = index
            response = super().execute(client, timeout, wait_for_receipt, validate_status)
            responses.append(response)

        return responses

    @property
    def body_size_all_chunks(self) -> list[int]:
        """Returns an array of body sizes for transactions with multiple chunks."""
        self._require_frozen()
        sizes = []

        original_transaction_index = self._current_transaction_id_index

        try:
            for i, _ in enumerate(self._transaction_ids):
                self._current_chunk_index = i
                self._current_transaction_id_index = i

                self._chunk_info = consensus_submit_message_pb2.ConsensusMessageChunkInfo(
                    initialTransactionID=self._initial_transaction_id._to_proto(),
                    total=self._total_chunks,
                    number=i + 1,
                )
                sizes.append(self.body_size)
        finally:
            self._current_transaction_id_index = original_transaction_index

        return sizes

    @classmethod
    def _from_protobuf(cls, transaction_body):
        transaction = super()._from_protobuf(transaction_body)

        if transaction_body.HasField("consensusSubmitMessage"):
            body = transaction_body.consensusSubmitMessage

            if body.HasField("topicID"):
                transaction.topic_id = TopicId._from_proto(body.topicID)
            transaction.message = body.message.decode("utf-8") if body.message else None
            transaction._total_chunks = transaction.get_required_chunks()

        return transaction
