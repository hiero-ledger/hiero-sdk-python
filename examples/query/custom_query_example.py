"""
Custom Query Example

This script demonstrates how to create a custom query by subclassing the base Query class.
This is useful when you need to implement a query that isn't already supported by the SDK,
or if you want to wrap an existing query with custom logic.

In this example, we re-implement a simple version of AccountBalanceQuery to show
the internal mechanics of building a query.

Run with:
  python examples/query/custom_query_example.py
"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Network,
    Client,
    AccountId,
    PrivateKey,
    Hbar,
)
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.executable import _Method
from hiero_sdk_python.hapi.services import query_pb2, crypto_get_account_balance_pb2

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

class CustomAccountBalanceQuery(Query):
    """
    A custom implementation of AccountBalanceQuery to demonstrate subclassing Query.
    """
    def __init__(self, account_id):
        super().__init__()
        self.account_id = account_id

    def _make_request(self):
        """
        Builds the Protobuf request for the query.
        """
        # Create the header (includes payment logic)
        header = self._make_request_header()
        
        # Create the specific query body
        # We use the raw protobuf classes here
        body = crypto_get_account_balance_pb2.CryptoGetAccountBalanceQuery(
            header=header,
            accountID=self.account_id._to_proto()
        )
        
        # Wrap it in the main Query object
        return query_pb2.Query(cryptoGetAccountBalance=body)

    def _get_query_response(self, response):
        """
        Extracts the specific query response from the full network response.
        """
        return response.cryptoGetAccountBalance

    def _get_method(self, channel):
        """
        Returns the gRPC method to call.
        """
        return _Method(query_func=channel.crypto.get_account_balance)

def setup_client():
    """
    Initialize and configure the Hiero SDK client.
    """
    network = Network(network_name)
    client = Client(network)

    operator_id_str = os.getenv('OPERATOR_ID')
    operator_key_str = os.getenv('OPERATOR_KEY')

    if not operator_id_str or not operator_key_str:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY environment variables must be set")

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)
    client.set_operator(operator_id, operator_key)

    return client, operator_id

def main():
    try:
        print("Setting up client...")
        client, operator_id = setup_client()
        print(f"Client setup with operator: {operator_id}")

        # Create our custom query
        print(f"\nExecuting CustomAccountBalanceQuery for {operator_id}...")
        query = CustomAccountBalanceQuery(operator_id)
        
        # Execute the query
        # This will trigger the full execution flow:
        # _before_execute -> _make_request -> gRPC call -> _map_response
        balance_response = query.execute(client)
        
        # The response is the raw protobuf object because we didn't override _map_response
        # to convert it to a nice SDK object (like the official AccountBalanceQuery does).
        # So we access the protobuf fields directly.
        balance_tinybars = balance_response.balance
        balance_hbar = Hbar.from_tinybars(balance_tinybars)
        
        print(f"✓ Balance retrieved successfully")
        print(f"  Balance: {balance_hbar} ({balance_tinybars} tinybars)")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
