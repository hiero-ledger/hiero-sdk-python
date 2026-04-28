from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import grpc

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message import TopicMessage
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.utils.subscription_handle import SubscriptionHandle


logger = logging.getLogger(__name__)

RST_STREAM = re.compile(r"\brst[^0-9a-zA-Z]stream\b", re.IGNORECASE | re.DOTALL)


@dataclass
class SubscriptionState:
    attempt: int = 0
    count: int = 0
    last_message: mirror_proto.ConsensusTopicResponse | None = None
    pending_messages: dict[str, list[mirror_proto.ConsensusTopicResponse]] = field(default_factory=dict)


class TopicMessageQuery:
    """
    A query to subscribe to messages from a specific HCS topic, via a mirror node.

    If `chunking_enabled=True`, multi-chunk messages are automatically reassembled
    before invoking `on_message`.
    """

    def __init__(
        self,
        topic_id: str | TopicId | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
        chunking_enabled: bool = False,
    ) -> None:
        """Initializes a TopicMessageQuery."""
        self._topic_id: basic_types_pb2.TopicID | None = self._parse_topic_id(topic_id) if topic_id else None
        self._start_time: timestamp_pb2.Timestamp | None = self._parse_timestamp(start_time) if start_time else None
        self._end_time: timestamp_pb2.Timestamp | None = self._parse_timestamp(end_time) if end_time else None
        self._limit: int = limit if limit is not None else 0
        self._chunking_enabled: bool = chunking_enabled

        self._max_attempts: int = 10
        self._max_backoff: float = 8.0

        self._completion_handler: Callable[[], None] | None = self._on_complete
        self._error_handler: Callable[[], None] | None = self._on_error

    def set_max_attempts(self, attempts: int) -> TopicMessageQuery:
        """Sets the maximum number of attempts to reconnect on failure."""
        if attempts <= 0:
            raise ValueError("max_attempts must be greater than 0")

        self._max_attempts = attempts
        return self

    def set_max_backoff(self, backoff: float) -> TopicMessageQuery:
        """Sets the maximum backoff time in seconds for reconnection attempts."""
        if backoff < 0.5:
            raise ValueError("max_backoff must be at least 500 ms")

        self._max_backoff = backoff
        return self

    def set_completion_handler(self, handler: Callable[[], None]) -> TopicMessageQuery:
        """Sets a completion handler that is called when the subscription completes."""
        self._completion_handler = handler
        return self

    def set_error_handler(self, handler: Callable[[], None]) -> TopicMessageQuery:
        """Sets a completion handler that is called when the subscription completes."""
        self._error_handler = handler
        return self

    def set_topic_id(self, topic_id: str | TopicId) -> TopicMessageQuery:
        """Sets the topic ID for the query."""
        self._topic_id = self._parse_topic_id(topic_id)
        return self

    def set_start_time(self, dt: datetime) -> TopicMessageQuery:
        """Sets the start time for the query."""
        self._start_time = self._parse_timestamp(dt)
        return self

    def set_end_time(self, dt: datetime) -> TopicMessageQuery:
        """Sets the end time for the query."""
        self._end_time = self._parse_timestamp(dt)
        return self

    def set_limit(self, limit: int) -> TopicMessageQuery:
        """Sets the maximum number of messages to return in the query."""
        self._limit = limit
        return self

    def set_chunking_enabled(self, enabled: bool) -> TopicMessageQuery:
        """Enables or disables chunking for multi-chunk messages."""
        self._chunking_enabled = enabled
        return self

    def _on_complete(self) -> None:
        logger.info(f"Subscription to topic {self._topic_id} complete")

    def _on_error(self, err: Exception) -> None:
        if isinstance(err, grpc.RpcError) and err.code() == grpc.StatusCode.CANCELLED:
            logger.warning(f"Call is cancelled for topic {self._topic_id}")
        else:
            logger.error(f"Error attempting to subscribe to topic {self._topic_id}: {err}")

    def _should_retry(self, err: Exception) -> bool:
        if isinstance(err, grpc.RpcError):
            return err.code() in (
                grpc.StatusCode.NOT_FOUND,
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.RESOURCE_EXHAUSTED,
            ) or (err.code() == grpc.StatusCode.INTERNAL and bool(RST_STREAM.search(err.details())))

        return True

    def _parse_topic_id(self, topic_id: str | TopicId) -> basic_types_pb2.TopicID:
        """Parses a topic ID from a string or TopicId object into a protobuf TopicID."""
        if isinstance(topic_id, str):
            topic_id = TopicId.from_string(topic_id)

        if isinstance(topic_id, TopicId):
            return topic_id._to_proto()

        raise TypeError("Invalid topic_id format. Must be a string or TopicId.")

    def _parse_timestamp(self, dt: datetime) -> timestamp_pb2.Timestamp:
        """Converts a datetime object to a protobuf Timestamp."""
        seconds = int(dt.timestamp())
        nanos = int((dt.timestamp() - seconds) * 1e9)
        return timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)

    def _build_query_request(self, state: SubscriptionState) -> mirror_proto.ConsensusTopicQuery:
        """Build the request object based on current subscription state."""
        request = mirror_proto.ConsensusTopicQuery(topicID=self._topic_id)

        if self._end_time is not None:
            request.consensusEndTime.CopyFrom(self._end_time)

        if state.last_message is not None:
            last_message_time = state.last_message.consensusTimestamp

            seconds = last_message_time.seconds
            nanos = last_message_time.nanos + 1

            if nanos >= 1_000_000_000:
                seconds += 1
                nanos = 0

            request.consensusStartTime.seconds = seconds
            request.consensusStartTime.nanos = nanos

            if self._limit > 0:
                request.limit = max(0, self._limit - state.count)
        else:
            if self._start_time is not None:
                request.consensusStartTime.CopyFrom(self._start_time)
            request.limit = self._limit

        return request

    def _handle_response(self, response, state: SubscriptionState, on_message: Callable[[TopicMessage], None]) -> None:
        """Handles single or chunked messages."""
        state.count += 1
        state.last_message = response

        if not self._chunking_enabled or not response.HasField("chunkInfo") or response.chunkInfo.total <= 1:
            message = TopicMessage.of_single(response)
            on_message(message)
            return

        initial_tx_id = TransactionId._from_proto(response.chunkInfo.initialTransactionID)

        if initial_tx_id not in state.pending_messages:
            state.pending_messages[initial_tx_id] = []

        chunks = state.pending_messages[initial_tx_id]
        chunks.append(response)

        if len(chunks) == response.chunkInfo.total:
            del state.pending_messages[initial_tx_id]

            message = TopicMessage.of_many(chunks)
            on_message(message)

    def subscribe(
        self,
        client: Client,
        on_message: Callable[[TopicMessage], None],
        on_error: Callable[[Exception], None] | None = None,
    ) -> SubscriptionHandle:
        """Subscribes to messages from the specified topic."""
        if not self._topic_id:
            raise ValueError("Topic ID must be set before subscribing.")
        if not client.mirror_stub:
            raise ValueError("Client has no mirror_stub. Did you configure a mirror node address?")

        subscription_handle = SubscriptionHandle()
        state = SubscriptionState()

        def run_stream():
            while state.attempt < self._max_attempts and not subscription_handle.is_cancelled():
                request = self._build_query_request(state)

                try:
                    message_stream = client.mirror_stub.subscribeTopic(request)
                    subscription_handle._set_call(message_stream)

                    for response in message_stream:
                        if subscription_handle.is_cancelled():
                            return

                        self._handle_response(response, state, on_message)

                    if self._completion_handler:
                        self._completion_handler()
                    return

                except Exception as e:
                    if subscription_handle.is_cancelled():
                        return

                    if state.attempt >= self._max_attempts or not self._should_retry(e):
                        if self._error_handler:
                            self._error_handler(e)
                        if on_error:
                            on_error(e)
                        return

                    delay = min(0.5 * (2 ** (state.attempt)), self._max_backoff)
                    logger.warning(f"Error subscribing to topic attempt {state.attempt}. Retrying in {int(delay)}s...")

                    state.attempt += 1
                    time.sleep(delay)

        thread = threading.Thread(target=run_stream, daemon=True)
        subscription_handle.set_thread(thread)
        thread.start()

        return subscription_handle
