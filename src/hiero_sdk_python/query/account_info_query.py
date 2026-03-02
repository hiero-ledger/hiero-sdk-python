from typing import Optional, Union
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import query_pb2, crypto_get_info_pb2
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.channels import _Channel

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_info import AccountInfo


class AccountInfoQuery(Query):
    """
    A query to retrieve information about a specific Account.
    
    This class constructs and executes a query to retrieve information 
    about an account on the network, including the account's properties 
    and settings.
    
    """
    def __init__(self, account_id: Optional[AccountId] = None):
        """
        Initializes a new AccountInfoQuery instance with an optional account_id.

        Args:
            account_id (Optional[AccountId], optional): The ID of the account to query.
        """
        super().__init__()
        self.account_id : Optional[AccountId] = account_id
        
    def set_account_id(self, account_id: AccountId):
        """
        Sets the ID of the account to query. 

        Args: 
            account_id (AccountId): The ID of the account. 

        Returns:
            AccountInfoQuery: Returns self for method chaining. 
        """
        self.account_id = account_id
        return self
    
    def _make_request(self):
        """
        Constructs the protobuf request for the query.
        
        Builds a CryptoGetInfoQuery protobuf message with the
        appropriate header and account ID.

        Returns:
            Query: The protobuf query message.

        Raises:
            ValueError: If the account ID is not set.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.account_id:
                raise ValueError("Account ID must be set before making the request.")

            query_header = self._make_request_header()

            crypto_info_query = crypto_get_info_pb2.CryptoGetInfoQuery()
            crypto_info_query.header.CopyFrom(query_header)
            crypto_info_query.accountID.CopyFrom(self.account_id._to_proto())

            query = query_pb2.Query()
            query.cryptoGetInfo.CopyFrom(crypto_info_query)
                  
            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            raise
        
    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the account info query.
        
        Implements the abstract method from Query to provide the specific
        gRPC method for getting account information.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None,
            query_func=channel.crypto.getAccountInfo
        )

    def execute(self, client, timeout: Optional[Union[int, float]] = None):
        """
        Executes the account info query.
        
        Sends the query to the Hedera network and processes the response
        to return an AccountInfo object.

        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            AccountInfo: The account info from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        return AccountInfo._from_proto(response.cryptoGetInfo.accountInfo)

    def _get_query_response(self, response):
        """
        Extracts the account info response from the full response.
        
        Implements the abstract method from Query to extract the
        specific account info response object.
        
        Args:
            response: The full response from the network
            
        Returns:
            The crypto get info response object
        """
        return response.cryptoGetInfo