import time
import threading
from datetime import datetime
from typing import Optional, Callable, Union, Dict, List

from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto
from hiero_sdk_python.hapi.services import basic_types_pb2, timestamp_pb2
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message import TopicMessage
from hiero_sdk_python.utils.subscription_handle import SubscriptionHandle
from hiero_sdk_python import Client


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
    ):
        self._topic_id = self._parse_topic_id(topic_id) if topic_id else None
        self._start_time = self._parse_timestamp(start_time) if start_time else None
        self._end_time = self._parse_timestamp(end_time) if end_time else None
        self._limit = limit
        self._chunking_enabled = chunking_enabled
        self._completion_handler: Optional[Callable[[], None]] = None

        self._max_attempts = 10
        self._max_backoff = 8.0

    def set_max_attempts(self, attempts: int):
        self._max_attempts = attempts
        return self

    def set_max_backoff(self, backoff: float):
        self._max_backoff = backoff
        return self

    def set_completion_handler(self, handler: Callable[[], None]):
        self._completion_handler = handler
        return self

    def _parse_topic_id(self, topic_id: Union[str, TopicId]):
        if isinstance(topic_id, str):
            parts = topic_id.strip().split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid topic ID string: {topic_id}")
            shard, realm, topic = map(int, parts)
            return basic_types_pb2.TopicID(shardNum=shard, realmNum=realm, topicNum=topic)
        elif isinstance(topic_id, TopicId):
            return topic_id.to_proto()
        else:
            raise TypeError("Invalid topic_id format. Must be a string or TopicId.")

    def _parse_timestamp(self, dt: datetime):
        seconds = int(dt.timestamp())
        nanos = int((dt.timestamp() - seconds) * 1e9)
        return timestamp_pb2.Timestamp(seconds=seconds, nanos=nanos)

    def set_topic_id(self, topic_id: Union[str, TopicId]):
        self._topic_id = self._parse_topic_id(topic_id)
        return self

    def set_start_time(self, dt: datetime):
        self._start_time = self._parse_timestamp(dt)
        return self

    def set_end_time(self, dt: datetime):
        self._end_time = self._parse_timestamp(dt)
        return self

    def set_limit(self, limit: int):
        self._limit = limit
        return self

    def set_chunking_enabled(self, enabled: bool):
        self._chunking_enabled = enabled
        return self

    def subscribe(
        self,
        client: Client,
        on_message: Callable[[TopicMessage], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> SubscriptionHandle:

        if not self._topic_id:
            raise ValueError("Topic ID must be set before subscribing.")
        if not client.mirror_stub:
            raise ValueError("Client has no mirror_stub. Did you configure a mirror node address?")

        request = mirror_proto.ConsensusTopicQuery(topicID=self._topic_id)
        if self._start_time:
            request.consensusStartTime.CopyFrom(self._start_time)
        if self._end_time:
            request.consensusEndTime.CopyFrom(self._end_time)
        if self._limit is not None:
            request.limit = self._limit

        subscription_handle = SubscriptionHandle()

        pending_chunks: Dict[str, List[mirror_proto.ConsensusTopicResponse]] = {}

        def run_stream():
            attempt = 0
            while attempt < self._max_attempts and not subscription_handle.is_cancelled():
                try:
                    message_stream = client.mirror_stub.subscribeTopic(request)

                    for response in message_stream:
                        if subscription_handle.is_cancelled():
                            return

                        if (not self._chunking_enabled
                                or not response.HasField("chunkInfo")
                                or response.chunkInfo.total <= 1):
                            msg_obj = TopicMessage.of_single(response)
                            on_message(msg_obj)
                            continue

                        initial_tx_id = response.chunkInfo.initialTransactionID
                        tx_id_str = (f"{initial_tx_id.shardNum}."
                                     f"{initial_tx_id.realmNum}."
                                     f"{initial_tx_id.accountNum}-"
                                     f"{initial_tx_id.transactionValidStart.seconds}."
                                     f"{initial_tx_id.transactionValidStart.nanos}")
                        if tx_id_str not in pending_chunks:
                            pending_chunks[tx_id_str] = []
                        pending_chunks[tx_id_str].append(response)

                        if len(pending_chunks[tx_id_str]) == response.chunkInfo.total:
                            chunk_list = pending_chunks.pop(tx_id_str)
                            msg_obj = TopicMessage.of_many(chunk_list)
                            on_message(msg_obj)

                    if self._completion_handler:
                        self._completion_handler()
                    return

                except Exception as e:
                    if subscription_handle.is_cancelled():
                        return

                    attempt += 1
                    if attempt >= self._max_attempts:
                        if on_error:
                            on_error(e)
                        return

                    delay = min(0.5 * (2 ** (attempt - 1)), self._max_backoff)
                    time.sleep(delay)

        thread = threading.Thread(target=run_stream, daemon=True)
        subscription_handle.set_thread(thread)
        thread.start()

        return subscription_handle
