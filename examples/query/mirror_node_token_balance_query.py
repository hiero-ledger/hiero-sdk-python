"""
MirrorNodeTokenBalanceQuery Example.

This script demonstrates how to:

1. Set up a client connection to the Hiero network.
2. Query an account's balance for a single token using the mirror node.

The mirror node token balance query is free and does not require an
operator to be configured on the client; the client only supplies the
network's mirror node URL. No transaction is sent.

Set TOKEN_ID in the environment to a token the operator account holds to
see a non-zero balance. Otherwise the example queries 0.0.1000 and shows
the "not associated" result.

Note:
The mirror node is eventually consistent, so a balance read immediately
after a transfer may lag the network by a few seconds.

Run with:
uv run python examples/query/mirror_node_token_balance_query.py
python examples/query/mirror_node_token_balance_query.py
"""

import os
import sys

from hiero_sdk_python import Client, TokenId
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query.mirror_node_token_balance_query import (
    MirrorNodeTokenBalanceQuery,
)


DEFAULT_TOKEN_ID = "0.0.1000"


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

    except ValueError as exc:
        print(f"Error setting up client: {exc}", file=sys.stderr)
        sys.exit(1)


def main():
    """Query and display the operator account's balance for one token."""
    client = None

    try:
        print("Get Token Balance Example Start!")

        # Step 0:
        # Create and configure the SDK client.
        client = setup_client()

        # Step 1:
        # Query the operator account's balance for the token.
        operator_id = client.operator_account_id
        token_id = TokenId.from_string(os.getenv("TOKEN_ID") or DEFAULT_TOKEN_ID)

        balance = MirrorNodeTokenBalanceQuery().set_account_id(operator_id).set_token_id(token_id).execute(client)

        # Step 2:
        # Display the token balance.
        print(f"Token ID:   {balance.token_id}")
        print(f"Balance:    {balance.balance}")
        print(f"Decimals:   {balance.decimals}")
        print(f"Associated: {balance.associated}")

        if not balance.associated:
            print("The account has no relationship with this token.")

        print("Get Token Balance Example Complete!")

    except PrecheckError as exc:
        print(
            f"✗ Account not found on the mirror node ({exc.status.name}). "
            "If it was just created, the mirror node may not have indexed it yet.",
            file=sys.stderr,
        )
        sys.exit(1)

    except Exception as exc:
        print(f"✗ Error: {exc}", file=sys.stderr)
        sys.exit(1)

    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
