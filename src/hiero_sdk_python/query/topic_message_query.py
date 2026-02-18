import time
import threading
import logging
from datetime import datetime
from typing import Optional, Callable, Union, Dict, List

from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message import TopicMessage
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.utils.subscription_handle import SubscriptionHandle
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.timestamp import Timestamp

# Setup logging
logger = logging.getLogger(__name__)


class TopicMessageQuery:
    """
    A query to subscribe to messages from a specific HCS topic, via a mirror node.

    If `chunking_enabled=True`, multi-chunk messages are automatically reassembled
    before invoking `on_message`.
    """

    def __init__(
        self,
        topic_id: Optional[Union[str, TopicId]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
        chunking_enabled: bool = False,
    ) -> None:
        """
        Initializes a TopicMessageQuery.
        """
        self._topic_id: Optional[basic_types_pb2.TopicID] = self._parse_topic_id(topic_id) if topic_id else None
        self._start_time: Optional[timestamp_pb2.Timestamp] = self._parse_timestamp(start_time) if start_time else None
        self._end_time: Optional[timestamp_pb2.Timestamp] = self._parse_timestamp(end_time) if end_time else None
        self._limit: Optional[int] = limit
        self._chunking_enabled: bool = chunking_enabled
        self._completion_handler: Optional[Callable[[], None]] = None

        self._max_attempts: int = 10
        self._max_backoff: float = 8.0

    def set_max_attempts(self, attempts: int) -> "TopicMessageQuery":
        """Sets the maximum number of attempts to reconnect on failure."""
        self._max_attempts = attempts
        return self

    def set_max_backoff(self, backoff: float) -> "TopicMessageQuery":
        """Sets the maximum backoff time in seconds for reconnection attempts."""
        self._max_backoff = backoff
        return self

    def set_completion_handler(self, handler: Callable[[], None]) -> "TopicMessageQuery":
        """Sets a completion handler that is called when the subscription completes."""
        self._completion_handler = handler
        return self

    def _parse_topic_id(self, topic_id: Union[str, TopicId]) -> basic_types_pb2.TopicID:
        """
        Parses a topic ID from a string or TopicId object into a protobuf TopicID.
        """
        if isinstance(topic_id, str):
            parts = topic_id.strip().split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid topic ID string: {topic_id}")
            shard, realm, topic = map(int, parts)
            return basic_types_pb2.TopicID(shardNum=shard, realmNum=realm, topicNum=topic)
        elif isinstance(topic_id, TopicId):
            return topic_id._to_proto()
        else:
            raise TypeError("Invalid topic_id format. Must be a string or TopicId.")

    def _parse_timestamp(self, dt: datetime) -> timestamp_pb2.Timestamp:
        """Converts a datetime object to a protobuf Timestamp."""
        return Timestamp.from_date(dt)._to_protobuf()

    def set_topic_id(self, topic_id: Union[str, TopicId]) -> "TopicMessageQuery":
        """Sets the topic ID for the query."""
        self._topic_id = self._parse_topic_id(topic_id)
        return self

    def set_start_time(self, dt: datetime) -> "TopicMessageQuery":
        """Sets the start time for the query."""
        self._start_time = self._parse_timestamp(dt)
        return self

    def set_end_time(self, dt: datetime) -> "TopicMessageQuery":
        """Sets the end time for the query."""
        self._end_time = self._parse_timestamp(dt)
        return self

    def set_limit(self, limit: int) -> "TopicMessageQuery":
        """Sets the maximum number of messages to return in the query."""
        self._limit = limit
        return self

    def set_chunking_enabled(self, enabled: bool) -> "TopicMessageQuery":
        """Enables or disables chunking for multi-chunk messages."""
        self._chunking_enabled = enabled
        return self

    def subscribe(
        self,
        client: Client,
        on_message: Callable[[TopicMessage], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> SubscriptionHandle:
        """Subscribes to messages from the specified topic."""

        if not self._topic_id:
            raise ValueError("Topic ID must be set before subscribing.")
        if not client.mirror_stub:
            raise ValueError("Client has no mirror_stub. Did you configure a mirror node address?")

        request = mirror_proto.ConsensusTopicQuery(topicID=self._topic_id)
        if self._start_time:
            request.consensusStartTime.CopyFrom(self._start_time)
        if self._end_time:
            request.consensusEndTime.CopyFrom(self._end_time)
        # Fix: only set limit if it's > 0. In Hedera, 0 is often used as 'no limit' in SDKs,
        # but the protobuf treats 0 as 0.
        if self._limit:
            request.limit = self._limit

        subscription_handle = SubscriptionHandle()
        
        # Track state for resumption
        last_received_timestamp: Optional[timestamp_pb2.Timestamp] = None
        received_count: int = 0

        pending_chunks: Dict[str, List[mirror_proto.ConsensusTopicResponse]] = {}

        def run_stream():
            nonlocal last_received_timestamp, received_count
            attempt = 0

            while attempt < self._max_attempts and not subscription_handle.is_cancelled():
                # Clear pending chunks on reconnection to avoid duplicates
                # because we resume from the last COMPLETE message timestamp.
                pending_chunks.clear()
                try:
                    # If we have received a message, resume from the next nanosecond
                    if last_received_timestamp:
                        resume_timestamp = Timestamp._from_protobuf(last_received_timestamp).plus_nanos(1)
                        request.consensusStartTime.CopyFrom(resume_timestamp._to_protobuf())
                    
                    # If we have a limit, adjust it for the remaining messages
                    if self._limit and received_count < self._limit:
                        request.limit = self._limit - received_count
                    elif self._limit and received_count >= self._limit:
                        # We hit the limit, stop.
                        if self._completion_handler:
                            self._completion_handler()
                        return

                    logger.debug(f"Subscribing to topic {self._topic_id.shardNum}.{self._topic_id.realmNum}.{self._topic_id.topicNum} "
                                 f"(Attempt {attempt + 1}, StartTime: {request.consensusStartTime.seconds}.{request.consensusStartTime.nanos})")
                    
                    message_stream = client.mirror_stub.subscribeTopic(request)

                    for response in message_stream:
                        if subscription_handle.is_cancelled():
                            logger.debug("Subscription cancelled, closing stream.")
                            return

                        # Process message
                        if (not self._chunking_enabled
                                or not response.HasField("chunkInfo")
                                or response.chunkInfo.total <= 1):
                            msg_obj = TopicMessage.of_single(response)
                            on_message(msg_obj)
                            
                            # Update resumption state
                            last_received_timestamp = response.consensusTimestamp
                            received_count += 1
                            attempt = 0 # Reset attempts on successful message
                            
                            if self._limit and received_count >= self._limit:
                                logger.debug(f"Reached message limit ({self._limit}), closing subscription.")
                                if self._completion_handler:
                                    self._completion_handler()
                                return
                            continue

                        # Handle chunking
                        initial_tx_id = TransactionId._from_proto(response.chunkInfo.initialTransactionID)
                        if initial_tx_id not in pending_chunks:
                            pending_chunks[initial_tx_id] = []
                        pending_chunks[initial_tx_id].append(response)

                        if len(pending_chunks[initial_tx_id]) == response.chunkInfo.total:
                            chunk_list = pending_chunks.pop(initial_tx_id)
                            msg_obj = TopicMessage.of_many(chunk_list)
                            on_message(msg_obj)
                            
                            # Update resumption state using the last chunk's timestamp
                            last_received_timestamp = response.consensusTimestamp
                            received_count += 1
                            attempt = 0 # Reset attempts on successful message
                            
                            if self._limit and received_count >= self._limit:
                                if self._completion_handler:
                                    self._completion_handler()
                                return

                    # Stream finished gracefully (e.g., reached end_time or connection reset)
                    if self._limit and received_count >= self._limit:
                         if self._completion_handler:
                             self._completion_handler()
                         return
                    
                    if self._end_time:
                         # If we have an end time, we check if we reached it
                         # But mirror node usually handles this by closing the stream.
                         if self._completion_handler:
                             self._completion_handler()
                         return

                    # Intermittent connection drop, try to reconnect
                    logger.warning("Mirror node subscription stream closed. Attempting to reconnect...")
                    attempt += 1

                except Exception as e:
                    if subscription_handle.is_cancelled():
                        return

                    attempt += 1
                    logger.error(f"Subscription error (Attempt {attempt}): {e}")
                    
                    if attempt >= self._max_attempts:
                        if on_error:
                            on_error(e)
                        return

                # Backoff before retry
                if attempt > 0:
                    delay = min(0.5 * (2 ** (attempt - 1)), self._max_backoff)
                    logger.debug(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        thread = threading.Thread(target=run_stream, daemon=True)
        subscription_handle.set_thread(thread)
        thread.start()

        return subscription_handle
