"""
Get Account Balance Example.

This script demonstrates how to:

1. Set up a client connection to the Hiero network.
2. Query an account's HBAR balance using the mirror node.

The mirror node balance query is free and does not require an operator
to be configured on the client.

Note:
The mirror node is eventually consistent, so a balance read immediately
after a transaction may lag the network by a few seconds.

Run with:
uv run python examples/query/mirror_node_account_balance_query.py
python examples/query/mirror_node_account_balance_query.py
"""

import sys

from hiero_sdk_python import Client, Hbar
from hiero_sdk_python.query.mirror_node_account_balance_query import (
    MirrorNodeAccountBalanceQuery,
)


def setup_client():
    """
    Initialize and configure the Hiero SDK client.

    ```
    Returns:
        Client: Configured client.

    Raises:
        ValueError: If the client cannot be configured.
    """
    try:
        client = Client.from_env()

        print(f"Client set up with operator id {client.operator_account_id}")

        return client

    except ValueError as exc:
        print(f"Error setting up client: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    """Query and display the operator account's HBAR balance."""
    client = None

    try:
        print("Get Account Balance Example Start!")

        # Step 0:
        # Create and configure the SDK client.
        client = setup_client()

        # Step 1:
        # Build the mirror-node account balance query.
        operator_id = client.operator_account_id
        query = MirrorNodeAccountBalanceQuery(operator_id)

        # Step 2:
        # Build the mirror-node URL and fetch the JSON response.
        #
        # The current MirrorNodeAccountBalance model has an incomplete
        # public conversion API, so this example reads the balance from
        # the mirror-node response directly.
        url = query._build_url(client)

        timeout = getattr(client, "request_timeout", 30.0)

        body = query._fetch_body(url, timeout)

        # Step 3:
        # Extract the account balance from the mirror-node response.
        balances = body.get("balances")

        if not balances:
            raise ValueError(f"Mirror node returned no balance for account {operator_id}")

        balance_tinybars = balances[0].get("balance")

        if balance_tinybars is None:
            raise ValueError(f"Mirror node response contained no balance for account {operator_id}")

        operators_balance = Hbar.from_tinybars(int(balance_tinybars))

        print(f"Operator's Hbar account balance: {operators_balance}")

        print("Get Account Balance Example Complete!")

    except Exception as exc:
        print(f"✗ Error: {exc}", file=sys.stderr)
        sys.exit(1)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
