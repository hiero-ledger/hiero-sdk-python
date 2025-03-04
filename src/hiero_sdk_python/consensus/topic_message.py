from datetime import datetime
from typing import Optional, List, Union, Dict

from hiero_sdk_python import Timestamp
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto


class TopicMessageChunk:
    """
    Represents a single chunk within a chunked topic message.
    Mirrors the Java 'TopicMessageChunk'.
    """

    def __init__(self, response: mirror_proto.ConsensusTopicResponse):
        self.consensus_timestamp = Timestamp.from_protobuf(response.consensusTimestamp).to_date()
        self.content_size = len(response.message)
        self.running_hash = response.runningHash
        self.sequence_number = response.sequenceNumber


class TopicMessage:
    """
    Represents a Hedera TopicMessage, possibly composed of multiple chunks.
    """

    def __init__(
        self,
        consensus_timestamp: datetime,
        message_data: Dict[str, Union[bytes, int]],
        chunks: List[TopicMessageChunk],
        transaction_id: Optional[str] = None,
    ):
        """
        Args:
            consensus_timestamp: The final consensus timestamp.
            message_data: Dict with required fields:
                          {
                              "contents": bytes,
                              "running_hash": bytes,
                              "sequence_number": int
                          }
            chunks: All individual chunks that form this message.
            transaction_id: The transaction ID string if available.
        """
        self.consensus_timestamp = consensus_timestamp
        self.contents = message_data["contents"]
        self.running_hash = message_data["running_hash"]
        self.sequence_number = message_data["sequence_number"]
        self.chunks = chunks
        self.transaction_id = transaction_id

    @classmethod
    def of_single(cls, response: mirror_proto.ConsensusTopicResponse) -> "TopicMessage":
        """
        Build a TopicMessage from a single-chunk response.
        """
        chunk = TopicMessageChunk(response)
        consensus_timestamp = chunk.consensus_timestamp
        contents = response.message
        running_hash = response.runningHash
        sequence_number = chunk.sequence_number

        transaction_id = None
        if response.HasField("chunkInfo") and response.chunkInfo.HasField("initialTransactionID"):
            tx_id = response.chunkInfo.initialTransactionID
            transaction_id = (
                f"{tx_id.shardNum}.{tx_id.realmNum}.{tx_id.accountNum}-"
                f"{tx_id.transactionValidStart.seconds}.{tx_id.transactionValidStart.nanos}"
            )

        return cls(
            consensus_timestamp,
            {
                "contents": contents,
                "running_hash": running_hash,
                "sequence_number": sequence_number,
            },
            [chunk],
            transaction_id
        )

    @classmethod
    def of_many(cls, responses: List[mirror_proto.ConsensusTopicResponse]) -> "TopicMessage":
        """
        Reassemble multiple chunk responses into a single TopicMessage.
        """
        sorted_responses = sorted(responses, key=lambda r: r.chunkInfo.number)

        chunks = []
        total_size = 0
        transaction_id = None

        for r in sorted_responses:
            c = TopicMessageChunk(r)
            chunks.append(c)
            total_size += len(r.message)

            if (
                transaction_id is None
                and r.HasField("chunkInfo")
                and r.chunkInfo.HasField("initialTransactionID")
            ):
                tx_id = r.chunkInfo.initialTransactionID
                transaction_id = (
                    f"{tx_id.shardNum}.{tx_id.realmNum}.{tx_id.accountNum}-"
                    f"{tx_id.transactionValidStart.seconds}.{tx_id.transactionValidStart.nanos}"
                )

        contents = bytearray(total_size)
        offset = 0
        for r in sorted_responses:
            end = offset + len(r.message)
            contents[offset:end] = r.message
            offset = end

        last_r = sorted_responses[-1]
        consensus_timestamp = Timestamp.from_protobuf(last_r.consensusTimestamp).to_date()
        running_hash = last_r.runningHash
        sequence_number = last_r.sequenceNumber

        return cls(
            consensus_timestamp,
            {
                "contents": bytes(contents),
                "running_hash": running_hash,
                "sequence_number": sequence_number,
            },
            chunks,
            transaction_id
        )

    @classmethod
    def from_proto(
        cls,
        response_or_responses: Union[mirror_proto.ConsensusTopicResponse, List[mirror_proto.ConsensusTopicResponse]],
        chunking_enabled: bool = False
    ) -> "TopicMessage":
        """
        Creates a TopicMessage from either:
         - A single ConsensusTopicResponse
         - A list of responses (for multi-chunk)

        If chunking is enabled and multiple chunks are detected, they are reassembled
        into one combined TopicMessage. Otherwise, a single chunk is returned as-is.
        """
        if not isinstance(response_or_responses, mirror_proto.ConsensusTopicResponse):
            if not response_or_responses:
                raise ValueError("Empty response list provided to from_proto().")

            if not chunking_enabled and len(response_or_responses) == 1:
                return cls.of_single(response_or_responses[0])

            return cls.of_many(response_or_responses)

        response = response_or_responses
        if chunking_enabled and response.HasField("chunkInfo") and response.chunkInfo.total > 1:
            raise ValueError(
                "Cannot handle multi-chunk in a single response. Pass all chunk responses in a list."
            )
        return cls.of_single(response)

    def __str__(self):
        contents_str = self.contents.decode("utf-8", errors="replace")
        return (
            f"TopicMessage("
            f"consensus_timestamp={self.consensus_timestamp}, "
            f"sequence_number={self.sequence_number}, "
            f"contents='{contents_str[:40]}{'...' if len(contents_str) > 40 else ''}', "
            f"chunk_count={len(self.chunks)}, "
            f"transaction_id={self.transaction_id}"
            f")"
        )
