"""
Account Creation Example.

This example demonstrates how to create a new account on the Hiero network.
It shows the complete process of setting up a client, generating new keys,
creating an account transaction, and handling the response.

The example creates an account with:
- A newly generated ED25519 key pair
- An initial balance of 1 HBAR (100,000,000 tinybars)
- A custom account memo

Usage:
    uv run examples/account_create.py
    python examples/account_create.py

Environment Variables Required:
    OPERATOR_ID: The account ID of the operator (e.g., "0.0.123")
    OPERATOR_KEY: The private key of the operator account
"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
)

load_dotenv()

def setup_client() -> tuple[Client, PrivateKey]:
    """
    Set up and configure a Hiero client for testnet operations.

    This function initializes a client connection to the Hiero testnet,
    configures the operator account using environment variables, and
    returns the configured client along with the operator's private key.

    The operator account is used to pay for transaction fees and sign
    transactions that require authorization.

    Returns:
        tuple[Client, PrivateKey]: A tuple containing:
            - Client: Configured Hiero client connected to testnet
            - PrivateKey: The operator account's private key for signing

    Raises:
        ValueError: If OPERATOR_ID or OPERATOR_KEY environment variables
            are not set or are invalid.
        Exception: If the client fails to connect to the network.

    Environment Variables:
        OPERATOR_ID (str): The account ID of the operator (e.g., "0.0.123")
        OPERATOR_KEY (str): The private key of the operator account
    """
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)

    return client, operator_key

def create_new_account(client: Client, operator_key: PrivateKey) -> None:
    """
    Create a new account on the Hiero network.

    This function generates a new ED25519 key pair, creates an account
    creation transaction with an initial balance and memo, signs it with
    the operator key, and executes it on the network.

    The new account will be created with:
    - A newly generated ED25519 key pair
    - An initial balance of 1 HBAR (100,000,000 tinybars)
    - A custom memo: "My new account"

    Args:
        client (Client): The configured Hiero client to execute the transaction.
        operator_key (PrivateKey): The operator's private key used to sign
            and authorize the account creation transaction.

    Returns:
        None: This function prints the results and exits on failure.

    Raises:
        Exception: If the transaction fails or returns a non-SUCCESS status.
        Exception: If the account ID is not found in the transaction receipt.
        SystemExit: Calls sys.exit(1) if account creation fails.

    Example:
        >>> client, operator_key = setup_client()
        >>> create_new_account(client, operator_key)
        Transaction status: ResponseCode.SUCCESS
        Account creation successful. New Account ID: 0.0.12345
        New Account Private Key: 302e...
        New Account Public Key: 302a...
    """
    new_account_private_key = PrivateKey.generate("ed25519")
    new_account_public_key = new_account_private_key.public_key()

    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .set_account_memo("My new account")
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        print(f"Transaction status: {receipt.status}")

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise Exception(f"Transaction failed with status: {status_message}")

        new_account_id = receipt.account_id
        if new_account_id is not None:
            print(f"Account creation successful. New Account ID: {new_account_id}")
            print(f"New Account Private Key: {new_account_private_key.to_string()}")
            print(f"New Account Public Key: {new_account_public_key.to_string()}")
        else:
            raise Exception("AccountID not found in receipt. Account may not have been created.")

    except Exception as e:
        print(f"Account creation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    client, operator_key = setup_client()
    create_new_account(client, operator_key)
