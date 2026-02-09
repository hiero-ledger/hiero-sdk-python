import traceback
from typing import Optional, Any, Union
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.hapi.services import crypto_get_account_balance_pb2, query_pb2
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_balance import AccountBalance
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.contract.contract_id import ContractId


class CryptoGetAccountBalanceQuery(Query):
    """
    A query to retrieve the balance of a specific account from the Hedera network.

    This class constructs and executes a query to obtain the balance of an account,
    including hbars and tokens.
    """

    def __init__(
        self,
        account_id: Optional[AccountId] = None,
        contract_id: Optional[ContractId] = None,
    ) -> None:
        """
        Initializes a new instance of the CryptoGetAccountBalanceQuery class.

        Args:
            account_id (AccountId, optional): The ID of the account to retrieve the balance for.
            contract_id (ContractId, optional): The ID of the contract to retrieve the balance for.
        """
        super().__init__()
        self.account_id: Optional[AccountId] = None
        self.contract_id: Optional[ContractId] = None

        if account_id is not None:
            self.set_account_id(account_id)
        if contract_id is not None:
            self.set_contract_id(contract_id)

    def set_account_id(self, account_id: AccountId) -> "CryptoGetAccountBalanceQuery":
        """
        Sets the account ID for which to retrieve the balance.
        Resets to None the contract ID.

        Args:
            account_id (AccountId): The ID of the account.

        Returns:
            CryptoGetAccountBalanceQuery: The current instance for method chaining.
        """
        if not isinstance(account_id, AccountId):
            raise TypeError("account_id must be an AccountId.")
        self.contract_id = None
        self.account_id = account_id
        return self

    def set_contract_id(self, contract_id: ContractId) -> "CryptoGetAccountBalanceQuery":
        """
        Sets the contract ID for which to retrieve the balance.
        Resets to None the account ID.

        Args:
            contract_id (ContractId): The ID of the contract.

        Returns:
            CryptoGetAccountBalanceQuery: The current instance for method chaining.
        """
        if not isinstance(contract_id, ContractId):
            raise TypeError("contract_id must be a ContractId.")
        self.account_id = None
        self.contract_id = contract_id
        return self

    def _make_request(self) -> query_pb2.Query:
        """
        Constructs the protobuf request for the account balance query.

        Returns:
            query_pb2.Query: The protobuf Query object containing the account balance query.

        Raises:
            ValueError: If both the account ID and contract ID are not set.
            ValueError: If both the account ID and contract ID are set.
            AttributeError: If the Query protobuf structure is invalid.
            Exception: If any other error occurs during request construction.
        """
        try:
            if not self.account_id and not self.contract_id:
                raise ValueError("Either account_id or contract_id must be set before making the request.")

            if self.account_id and self.contract_id:
                raise ValueError("Specify either account_id or contract_id, not both.")

            query_header = self._make_request_header()
            crypto_get_balance = (
                crypto_get_account_balance_pb2.CryptoGetAccountBalanceQuery()
            )
            crypto_get_balance.header.CopyFrom(query_header)

            if self.account_id:
                crypto_get_balance.accountID.CopyFrom(self.account_id._to_proto())
            else:
                crypto_get_balance.contractID.CopyFrom(self.contract_id._to_proto())

            query = query_pb2.Query()
            if not hasattr(query, "cryptogetAccountBalance"):
                raise AttributeError(
                    "Query object has no attribute 'cryptogetAccountBalance'"
                )
            query.cryptogetAccountBalance.CopyFrom(crypto_get_balance)

            return query
        except Exception as e:
            print(f"Exception in _make_request: {e}")
            traceback.print_exc()
            raise

    def _get_method(self, channel: _Channel) -> _Method:
        """
        Returns the appropriate gRPC method for the account balance query.

        Implements the abstract method from Query to provide the specific
        gRPC method for getting account balances.

        Args:
            channel (_Channel): The channel containing service stubs

        Returns:
            _Method: The method wrapper containing the query function
        """
        return _Method(
            transaction_func=None, query_func=channel.crypto.cryptoGetBalance
        )

    def execute(self, client: Client, timeout: Optional[Union[int, float]] = None) -> AccountBalance:
        """
        Executes the account balance query.

        This function delegates the core logic to `_execute()`, and may propagate exceptions raised by it.

        Sends the query to the Hedera network and processes the response
        to return an AccountBalance object.

        Args:
            client (Client): The client instance to use for execution
            timeout (Optional[Union[int, float]]): The total execution timeout (in seconds) for this execution.

        Returns:
            AccountBalance: The account balance from the network

        Raises:
            PrecheckError: If the query fails with a non-retryable error
            MaxAttemptsError: If the query fails after the maximum number of attempts
            ReceiptStatusError: If the query fails with a receipt status error
        """
        self._before_execute(client)
        response = self._execute(client, timeout)

        return AccountBalance._from_proto(response.cryptogetAccountBalance)

    def _get_query_response(
        self, response: Any
    ) -> crypto_get_account_balance_pb2.CryptoGetAccountBalanceResponse:
        """
        Extracts the account balance response from the full response.

        Implements the abstract method from Query to extract the
        specific account balance response object.

        Args:
            response: The full response from the network

        Returns:
            The crypto get account balance response object
        """
        return response.cryptogetAccountBalance

    def _is_payment_required(self):
        """
        Account balance query does not require payment.

        Returns:
            bool: False
        """
        return False
