"""
Query to get records about a specific account on the network.
"""

import traceback
from typing import List, Optional, Union

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import crypto_get_account_records_pb2, query_pb2, response_pb2
from hiero_sdk_python.hapi.services.crypto_get_account_records_pb2 import (
    CryptoGetAccountRecordsResponse,
)
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.transaction.transaction_record import TransactionRecord


class AccountRecordsQuery(Query):
    """
    A query to retrieve records about a specific Account.

    This class constructs and executes a query to retrieve records of all transactions
    against the specified account within the last 25 hours.
    """

    def __init__(self, account_id: Optional[AccountId] = None):
        """
        Initializes a new AccountRecordsQuery instance with an optional account_id.

        Args:
            account_id (Optional[AccountId]): The ID of the account to query.
        """
        super().__init__()
        self.account_id: Optional[AccountId] = account_id

    def set_account_id(self, account_id: Optional[AccountId]) -> "AccountRecordsQuery":
        """
        Sets the ID of the account to query.

        Args:
            account_id (Optional[AccountId]): The ID of the account.

        Returns:
            AccountRecordsQuery: Returns self for method chaining.
        """
        self.account_id = account_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the query.

        Builds a CryptoGetAccountRecordsQuery protobuf message with the
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

            crypto_records_query = crypto_get_account_records_pb2.CryptoGetAccountRecordsQuery()
            crypto_records_query.header.CopyFrom(query_header)
            crypto_records_query.accountID.CopyFrom(self.account_id._to_proto())

            query = query_pb2.Query()
            query.cryptoGetAccountRecords.CopyFrom(crypto_records_query)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the account records query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting account records.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(transaction_func=None, query_func=channel.crypto.getAccountRecords)

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> List[TransactionRecord]:
        """
        Executes the account records query.

        Sends the query to the Hedera network and processes the response
        to return a list of TransactionRecord objects.

        This function delegates the core logic to `_execute()`, and may propagate
        exceptions raised by it.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            List[TransactionRecord]: The account records from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        records = []
        for record in response.cryptoGetAccountRecords.records:
            records.append(TransactionRecord._from_proto(record))

        return records

    def _get_query_response(
        self, response: response_pb2.Response
    ) -> CryptoGetAccountRecordsResponse:
        """
        Extracts the account records response from the full response.

        Implements the abstract method from Query to extract the
        specific account records response object.

        Args:
            response: The full response from the network

        Returns:
            The crypto get account records response object
        """
        return response.cryptoGetAccountRecords
