"""
Account Creation Example.

This module demonstrates how to create a new Hedera account using the Hiero Python SDK.
It shows the complete workflow from setting up a client with operator credentials
to creating a new account and handling the transaction response.

The example creates an account with:
- A generated Ed25519 key pair
- An initial balance of 1 HBAR (100,000,000 tinybars)
- A custom account memo

Usage:
    Run this script directly:
        python examples/account/account_create_transaction.py

    Or using uv:
        uv run examples/account/account_create_transaction.py

Requirements:
    - Environment variables OPERATOR_ID and OPERATOR_KEY must be set
    - A .env file with the operator credentials (recommended)
    - Sufficient HBAR balance in the operator account to pay for account creation

Environment Variables:
    OPERATOR_ID (str): The account ID of the operator (format: "0.0.xxxxx")
    OPERATOR_KEY (str): The private key of the operator account
    NETWORK (str, optional): Network to use (default: "testnet")
"""

import sys
from hiero_sdk_python import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
)


def create_new_account(client: Client) -> None:
    """
    Create a new Hedera account with generated keys and initial balance.

    This function generates a new Ed25519 key pair, creates an account creation
    transaction, signs it with the operator key, and executes it on the network.
    The new account is created with an initial balance and a custom memo.

    Args:
        client (Client): Configured Hedera client instance with operator set

    Returns:
        None:  This function doesn't return a value but prints the results

    Raises:
        Exception: If the transaction fails or the account ID is not found in the receipt
        SystemExit:  Calls sys.exit(1) if account creation fails

    Side Effects:
        - Prints transaction status and account details to stdout
        - Creates a new account on the Hedera network
        - Deducts transaction fees from the operator account
        - Exits the program with code 1 if creation fails

    Example Output:
        Transaction status: ResponseCode.SUCCESS
        Account creation successful. New Account ID: 0.0.123456
        New Account Private Key:  302e020100300506032b657004220420...
        New Account Public Key: 302a300506032b6570032100...
    """
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    # Get the operator key from the client for signing
    operator_key = client.operator_private_key

    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .set_account_memo("My new account")
    )

    try:
        # Explicit signing with key retrieved from client
        receipt = transaction.freeze_with(client).sign(operator_key).execute(client)
        print(f"Transaction status: {receipt.status}")

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise Exception(f"Transaction failed with status: {status_message}")

        new_account_id = receipt.account_id
        if new_account_id is not None:
            print(f"✅ Account creation successful. New Account ID: {new_account_id}")
            print(f"   New Account Private Key: {new_account_private_key.to_string()}")
            print(f"   New Account Public Key: {new_account_public_key.to_string()}")
        else:
            raise Exception(
                "AccountID not found in receipt.  Account may not have been created."
            )

    except Exception as e:
        print(f"❌ Account creation failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    client = Client.from_env()
    print(f"Operator: {client.operator_account_id}")
    create_new_account(client)
    client.close()
