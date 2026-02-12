from typing import Optional, Any, Union
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, response_pb2, token_get_nft_info_pb2
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.channels import _Channel
import traceback

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_nft_info import TokenNftInfo

class TokenNftInfoQuery(Query):
    """
    A query to retrieve information about a specific Hedera NFT.
    
    This class constructs and executes a query to retrieve information about a NFT
    on the Hedera network, including the NFT's properties and settings.
    
    """
    def __init__(self, nft_id: Optional[NftId] = None) -> None:
        """
        Initializes a new TokenNftInfoQuery instance with an optional nft_id.

        Args:
            nft_id (NftId, optional): The ID of the NFT to query.
        """
        super().__init__()
        self.nft_id: Optional[NftId] = nft_id

    def set_nft_id(self, nft_id: NftId) -> "TokenNftInfoQuery":
        """
        Sets the ID of the NFT to query.

        Args:
            nft_id (NftId): The ID of the NFT.
        """
        self.nft_id = nft_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.
        
        Builds a TokenGetNftInfoQuery protobuf message with the
        appropriate header and nft ID.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the nft ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.nft_id:
                raise ValueError("NFT ID must be set before making the request.")

            query_header = self._make_request_header()

            nft_info_query = token_get_nft_info_pb2.TokenGetNftInfoQuery()
            nft_info_query.header.CopyFrom(query_header)
            nft_info_query.nftID.CopyFrom(self.nft_id._to_proto())

            query = query_pb2.Query()
            query.tokenGetNftInfo.CopyFrom(nft_info_query)
                  
            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the nft info query.
        
        Implements the abstract method from Query to provide the specific
        gRPC method for getting nft information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.token.getTokenNftInfo
        )

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> TokenNftInfo:
        """
        Executes the nft info query.
        
        Sends the query to the Hedera network and processes the response
        to return a TokenNftInfo object.

        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            TokenNftInfo: The token nft info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        return TokenNftInfo._from_proto(response.tokenGetNftInfo.nft)

    def _get_query_response(self, response: response_pb2.Response) -> token_get_nft_info_pb2.TokenGetNftInfoResponse:
        """
        Extracts the nft info response from the full response.
        
        Implements the abstract method from Query to extract the
        specific nft info response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The token get nft info response object
        """
        return response.tokenGetNftInfo