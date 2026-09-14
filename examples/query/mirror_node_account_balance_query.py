"""
Get Account Balance Example.

This script demonstrates how to:
1. Set up a client connection to the Hiero network
2. Query an account's HBAR balance using the mirror node

The mirror node balance query is free and does not require an operator
to be configured on the client.

Note:
    The mirror node is eventually consistent, so a balance read immediately
    after a transaction may lag the network by a few seconds.

Run with:
  uv run examples/query/account_balance_query.py
  python examples/query/account_balance_query.py
"""

import sys

from hiero_sdk_python import Client
from hiero_sdk_python.query.mirror_node_account_balance_query import MirrorNodeAccountBalanceQuery


def setup_client():
    """
    Initialize and configure the Hiero SDK client.

    Returns:
        Client: Configured client.

    Raises:
        ValueError: If the client cannot be configured.
    """
    try:
        client = Client.from_env()

        print(f"Client set up with operator id {client.operator_account_id}")

        return client

    except ValueError as e:
        print(f"Error setting up client: {e}")
        sys.exit(1)


def main():
    """Query and display the operator account's HBAR balance."""
    client = None

    try:
        print("Get Account Balance Example Start!")

        # Step 0:
        # Create and configure the SDK Client.
        #
        # Because MirrorNodeAccountBalanceQuery is a free query,
        # an operator is not required to execute the query.
        client = setup_client()

        # Step 1:
        # Execute MirrorNodeAccountBalanceQuery and output the
        # operator's account balance.
        #
        # Note: The mirror node is eventually consistent, so a balance
        # read immediately after a transaction may lag the network by
        # a few seconds.
        operator_id = client.operator_account_id

        operators_balance = MirrorNodeAccountBalanceQuery().set_account_id(operator_id).execute(client)

        print(f"Operator's Hbar account balance: {operators_balance.hbars}")

        print("Get Account Balance Example Complete!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
