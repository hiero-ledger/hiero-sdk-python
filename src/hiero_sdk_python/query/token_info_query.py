from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, token_get_info_pb2
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_info import TokenInfo

class TokenInfoQuery(Query): 
    """
    A query to retrive information about a specific Token.
    """

    def __init__(self, token_id=None):
        """
        Initalizes a new TokenInfoQuery istance with a token_id.
        
        Args: 
            token_id (TokenID): The ID of the token to query. 
        """
        super().__init__()
        self.token_id = token_id
        self._frozen = False
    
    def _require_not_frozen(self):
        """
        Ensures the query is not frozen before making changes.
        """

        if self._frozen:
            raise ValueError("This query is frozen and cannot be modified.")

    def set_token_id(self, token_id: TokenId):
        """
        Sets the ID of the token to query. 

        Args: 
            token_id (TokenID): The ID of the token. 

        Returns:
            TokenInfoQuery: Returns self for method chaining. 
        """
        self._require_not_frozen()
        self.token_id = token_id
        return self
    
    def freeze(self): 
        """
        Marks the query as frozen, preventing further modificatoin. 

        Returns: 
            TokenInfoQuery: Returns self for chaining. 
        """

        self._frozen = True
        return self

    def _make_request(self):
        """
        Constrcuts the protobuf request for the query.

        Returns: 
            Query: The protobuf query message. 
        
        Raises: 
            ValueError: If the token ID is not set. 
        """

        if not self.token_id:
            raise ValueError("Token ID must be set before making the request. ")
        
        query_header = self._make_request_header()

        token_info_query = token_get_info_pb2.TokenGetInfoQuery()
        token_info_query.header.CopyFrom(query_header)
        token_info_query.token.CopyFrom(slef.token_id.to_proto())

        query = query_pb2.Query()
        query.tokenGetInfo.CopyFrom(token_info_query)
        return query 
    
    def _get_status_from_response(self, response):
        """
        Extracts the status from the query response. 

        Args:
            response: The response protobuf message. 

        Returns: 
            ResponseCode: The status code from the response. 
        """

        return response.tokenGetInfo.header.nodeTransactionPrecheckCode
    
    def _map_response(self, response):
        """
        Maps the protobuf response to a TokenInfo instance.

        Args: 
            response: The response protobuf message. 

        Returns:
            TokenInfo: The token info.
        
        Raises:
            Exception: If no tokenInfo is returned in the response. 
        """

        if not response.tokenGetInfo.tokenInfo:
            raise Exception("No tokenInfo retured in the response.")
        
        proto_token_info = response.tokenGetInfo.tokenInfo
        return TokenInfo.from_proto(proto_token_info)
    
    def execute(self, client):
        """
        Sends the TokenInfoQuery to the network via the given client and returns TokenInfo.

        Args:
            client: The client object to execute the query.

        Returns:
            TokenInfo: The queried token information.
        """
        self.freeze()  # prevent further modifications
        request = self._make_request()
        response = client.send_query(request)  # You need this method in your client
        status = self._get_status_from_response(response)

        if status != 0:  # assuming 0 is OK; adjust based on your ResponseCode enum
            raise Exception(f"Query failed with status: {status}")

        return self._map_response(response)