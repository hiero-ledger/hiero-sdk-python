from typing import Optional, Any, Union
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, consensus_get_topic_info_pb2, response_pb2
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_info import TopicInfo
from hiero_sdk_python.executable import _Method, _ExecutionState
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.exceptions import PrecheckError
import traceback

class TopicInfoQuery(Query):
    """
    A query to retrieve information about a specific Hedera topic.
    
    This class constructs and executes a query to retrieve information about a topic
    on the Hedera network, including the topic's properties and settings.

    """

    def __init__(self, topic_id: Optional[TopicId] = None) -> None:
        """
        Initializes a new TopicInfoQuery instance with an optional topic_id.

        Args:
            topic_id (TopicId, optional): The ID of the topic to query.
        """
        super().__init__()
        self.topic_id: Optional[TopicId] = topic_id
        self._frozen: bool = False 

    def _require_not_frozen(self) -> None:
        """
        Ensures the query is not frozen before making changes.
        
        Raises:
            ValueError: If the query is frozen and cannot be modified.
        """
        if self._frozen:
            raise ValueError("This query is frozen and cannot be modified.")

    def set_topic_id(self, topic_id: TopicId) -> "TopicInfoQuery":
        """
        Sets the ID of the topic to query.

        Args:
            topic_id (TopicId): The ID of the topic.

        Returns:
            TopicInfoQuery: Returns self for method chaining.
            
        Raises:
            ValueError: If the query is frozen and cannot be modified.
        """
        self._require_not_frozen()
        self.topic_id = topic_id
        return self

    def freeze(self) -> "TopicInfoQuery":
        """
        Marks the query as frozen, preventing further modification.
        
        Once frozen, properties like topic_id cannot be changed.

        Returns:
            TopicInfoQuery: Returns self for chaining.
        """
        self._frozen = True
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.
        
        Builds a ConsensusGetTopicInfoQuery protobuf message with the
        appropriate header and topic ID.

        Returns:
            query_pb2.Query: The protobuf query message.

        Raises:
            ValueError: If the topic ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.topic_id:
                raise ValueError("Topic ID must be set before making the request.")

            query_header = self._make_request_header()

            topic_info_query = consensus_get_topic_info_pb2.ConsensusGetTopicInfoQuery()
            topic_info_query.header.CopyFrom(query_header)
            topic_info_query.topicID.CopyFrom(self.topic_id._to_proto())

            query = query_pb2.Query()
            query.consensusGetTopicInfo.CopyFrom(topic_info_query)
                  
            return query
        
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the topic info query.
        
        Implements the abstract method from Query to provide the specific
        gRPC method for getting topic information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.topic.getTopicInfo
        )

    def _should_retry(self, response: Any) -> _ExecutionState:
        """
        Determines whether the query should be retried based on the response.
        
        Implements the abstract method from Query to decide whether to retry
        the query based on the response status code.

        Args:
            response: The response from the network

        Returns:
            _ExecutionState: The execution state indicating what to do next
        """
        status = response.consensusGetTopicInfo.header.nodeTransactionPrecheckCode

        retryable_statuses = {
            ResponseCode.UNKNOWN,
            ResponseCode.BUSY,
            ResponseCode.PLATFORM_NOT_ACTIVE
        }
        
        if status == ResponseCode.OK:
            return _ExecutionState.FINISHED
        elif status in retryable_statuses:
            return _ExecutionState.RETRY
        else:
            return _ExecutionState.ERROR

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> TopicInfo:
        """
        Executes the topic info query.
        
        Sends the query to the Hedera network and processes the response
        to return a TopicInfo object.

        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TopicInfo: The topic info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)
        
        return TopicInfo._from_proto(response.consensusGetTopicInfo.topicInfo)

    def _get_query_response(self, response: Any) -> consensus_get_topic_info_pb2.ConsensusGetTopicInfoResponse:
        """
        Extracts the topic info response from the full response.
        
        Implements the abstract method from Query to extract the
        specific topic info response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The consensus get topic info response object
        """
        return response.consensusGetTopicInfo
