from typing import Optional, Union
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, token_get_info_pb2, response_pb2
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client

from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_info import TokenInfo

class TokenInfoQuery(Query):
    """
    A query to retrieve information about a specific Token.
    
    This class constructs and executes a query to retrieve information 
    about a fungible or non-fungible token on the network,
    including the token's properties and settings.
    
    """
    def __init__(self, token_id: Optional[TokenId] = None) -> None:
        """
        Initializes a new TokenInfoQuery instance with an optional token_id.

        Args:
            token_id (TokenId, optional): The ID of the token to query.
        """
        super().__init__()
        self.token_id: Optional[TokenId] = token_id

    def set_token_id(self, token_id: TokenId) -> "TokenInfoQuery":
        """
        Sets the ID of the token to query. 

        Args: 
            token_id (TokenID): The ID of the token. 

        Returns:
            TokenInfoQuery: Returns self for method chaining. 
        """
        self.token_id = token_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.
        
        Builds a TokenGetInfoQuery protobuf message with the
        appropriate header and token ID.

        Returns:
            query_pb2.Query: The protobuf query message.

        Raises:
            ValueError: If the token ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.token_id:
                raise ValueError("Token ID must be set before making the request.")

            query_header = self._make_request_header()

            token_info_query = token_get_info_pb2.TokenGetInfoQuery()
            token_info_query.header.CopyFrom(query_header)
            token_info_query.token.CopyFrom(self.token_id._to_proto())

            query = query_pb2.Query()
            query.tokenGetInfo.CopyFrom(token_info_query)
                  
            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the token info query.
        
        Implements the abstract method from Query to provide the specific
        gRPC method for getting token information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.token.getTokenInfo
        )

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> TokenInfo:
        """
        Executes the token info query.
        
        Sends the query to the Hedera network and processes the response
        to return a TokenInfo object.

        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TokenInfo: The token info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        return TokenInfo._from_proto(response.tokenGetInfo.tokenInfo)

    def _get_query_response(self, response: response_pb2.Response) -> token_get_info_pb2.TokenGetInfoResponse:
        """
        Extracts the token info response from the full response.
        
        Implements the abstract method from Query to extract the
        specific token info response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The token get info response object
        """
        return response.tokenGetInfo