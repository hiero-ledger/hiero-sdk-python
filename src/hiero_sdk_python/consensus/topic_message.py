"""
This module provides the `TopicMessage` and `TopicMessageChunk` classes for handling
Hedera Consensus Service topic messages using the Hiero SDK.
"""

from __future__ import annotations

from datetime import datetime

from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.transaction.transaction_id import TransactionId


class TopicMessageChunk:
    """
    Represents a single chunk within a chunked topic message.
    Mirrors the Java 'TopicMessageChunk'.
    """

    def __init__(self, response: mirror_proto.ConsensusTopicResponse) -> None:  # type: ignore
        """
        Initializes a TopicMessageChunk from a ConsensusTopicResponse.

        Args:
            response: The ConsensusTopicResponse containing chunk data.
        """
        self.consensus_timestamp: datetime = Timestamp._from_protobuf(response.consensusTimestamp).to_date()
        self.content_size: int = len(response.message)
        self.running_hash: bytes | int = response.runningHash
        self.sequence_number: bytes | int = response.sequenceNumber


class TopicMessage:
    """Represents a Hedera TopicMessage, possibly composed of multiple chunks."""

    def __init__(
        self,
        consensus_timestamp: datetime,
        message_data: dict[str, bytes | int],
        chunks: list[TopicMessageChunk],
        transaction_id: TransactionId | None = None,
    ) -> None:
        """
        Args:
            consensus_timestamp (datetime): The final consensus timestamp.
            message_data (dict[str, bytes | int]): Dict with required fields:
                          {
                              "contents": bytes,
                              "running_hash": bytes,
                              "sequence_number": int
                          }
            chunks (list[TopicMessageChunk]): All individual chunks that form this message.
            transaction_id (Transaction, optional): The transaction ID if available.
        """
        self.consensus_timestamp: datetime = consensus_timestamp
        self.contents: bytes | int = message_data["contents"]
        self.running_hash: bytes | int = message_data["running_hash"]
        self.sequence_number: bytes | int = message_data["sequence_number"]
        self.chunks: list[TopicMessageChunk] = chunks
        self.transaction_id: TransactionId | None = transaction_id

    @classmethod
    def of_single(cls, response: mirror_proto.ConsensusTopicResponse) -> TopicMessage:  # type: ignore
        """Build a TopicMessage from a single-chunk response."""
        chunk: TopicMessageChunk = TopicMessageChunk(response)
        consensus_timestamp: datetime = chunk.consensus_timestamp
        contents: bytes | int = response.message
        running_hash: bytes | int = response.runningHash
        sequence_number: bytes | int = chunk.sequence_number

        transaction_id: TransactionId | None = None
        if response.HasField("chunkInfo") and response.chunkInfo.HasField("initialTransactionID"):
            transaction_id = TransactionId._from_proto(response.chunkInfo.initialTransactionID)

        return cls(
            consensus_timestamp,
            {
                "contents": contents,
                "running_hash": running_hash,
                "sequence_number": sequence_number,
            },
            [chunk],
            transaction_id,
        )

    @classmethod
    def of_many(cls, responses: list[mirror_proto.ConsensusTopicResponse]) -> TopicMessage:  # type: ignore
        """Reassemble multiple chunk responses into a single TopicMessage."""
        sorted_responses: list[mirror_proto.ConsensusTopicResponse] = sorted(
            responses, key=lambda r: r.chunkInfo.number
        )

        chunks: list[TopicMessageChunk] = []
        total_size: int = 0
        transaction_id: TransactionId | None = None

        for r in sorted_responses:
            c = TopicMessageChunk(r)
            chunks.append(c)

            total_size += len(r.message)

            if transaction_id is None and r.HasField("chunkInfo") and r.chunkInfo.HasField("initialTransactionID"):
                transaction_id = TransactionId._from_proto(r.chunkInfo.initialTransactionID)

        contents = bytearray(total_size)

        offset: int = 0
        for r in sorted_responses:
            end = offset + len(r.message)
            contents[offset:end] = r.message
            offset = end

        last_r: mirror_proto.ConsensusTopicResponse = sorted_responses[-1]
        consensus_timestamp: datetime = Timestamp._from_protobuf(last_r.consensusTimestamp).to_date()
        running_hash: bytes = last_r.runningHash
        sequence_number: int = last_r.sequenceNumber

        return cls(
            consensus_timestamp,
            {
                "contents": bytes(contents),
                "running_hash": running_hash,
                "sequence_number": sequence_number,
            },
            chunks,
            transaction_id,
        )

    @classmethod
    def _from_proto(
        cls,
        response_or_responses: mirror_proto.ConsensusTopicResponse | list[mirror_proto.ConsensusTopicResponse],
        chunking_enabled: bool = False,
    ) -> TopicMessage:
        """
        Creates a TopicMessage from either:
         - A single ConsensusTopicResponse
         - A list of responses (for multi-chunk).

        If chunking is enabled and multiple chunks are detected, they are reassembled
        into one combined TopicMessage. Otherwise, a single chunk is returned as-is.
        """
        if not isinstance(response_or_responses, mirror_proto.ConsensusTopicResponse):
            if not response_or_responses:
                raise ValueError("Empty response list provided to _from_proto().")

            if not chunking_enabled and len(response_or_responses) == 1:
                return cls.of_single(response_or_responses[0])

            return cls.of_many(response_or_responses)

        response: mirror_proto.ConsensusTopicResponse = response_or_responses
        if chunking_enabled and response.HasField("chunkInfo") and response.chunkInfo.total > 1:
            raise ValueError("Cannot handle multi-chunk in a single response. Pass all chunk responses in a list.")
        return cls.of_single(response)

    def __str__(self) -> str:
        contents_str: str
        if isinstance(self.contents, bytes):
            contents_str = self.contents.decode("utf-8", errors="replace")
        else:
            contents_str = str(self.contents)
        return (
            f"TopicMessage("
            f"consensus_timestamp={self.consensus_timestamp}, "
            f"sequence_number={self.sequence_number}, "
            f"contents='{contents_str[:40]}{'...' if len(contents_str) > 40 else ''}', "
            f"chunk_count={len(self.chunks)}, "
            f"transaction_id={self.transaction_id}"
            f")"
        )
