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
        python examples/account_create.py
    
    Or using uv:
        uv run examples/account_create.py

Requirements:
    - Environment variables OPERATOR_ID and OPERATOR_KEY must be set
    - A .env file with the operator credentials (recommended)
    - Sufficient HBAR balance in the operator account to pay for account creation
"""
import os
import sys
from typing import Tuple
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

def setup_client() -> Tuple[Client, PrivateKey]:
    """
    Set up and configure a Hedera client for testnet operations.
    
    Creates a client instance connected to the Hedera testnet and configures it
    with operator credentials from environment variables. The operator account
    is used to pay for transactions and sign them.
    
    Returns:
        tuple: A tuple containing:
            - Client: Configured Hedera client instance
            - PrivateKey: The operator's private key for signing transactions
    
    Raises:
        ValueError: If OPERATOR_ID or OPERATOR_KEY environment variables are not set
        Exception: If there's an error parsing the operator credentials
    
    Environment Variables:
        OPERATOR_ID (str): The account ID of the operator (format: "0.0.xxxxx")
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
    Create a new Hedera account with generated keys and initial balance.
    
    This function generates a new Ed25519 key pair, creates an account creation
    transaction, signs it with the operator key, and executes it on the network.
    The new account is created with an initial balance and a custom memo.
    
    Args:
        client (Client): Configured Hedera client instance for network communication
        operator_key (PrivateKey): The operator's private key for signing the transaction
    
    Returns:
        None: This function doesn't return a value but prints the results
    
    Raises:
        Exception: If the transaction fails or the account ID is not found in the receipt
        SystemExit: Calls sys.exit(1) if account creation fails
    
    Side Effects:
        - Prints transaction status and account details to stdout
        - Creates a new account on the Hedera network
        - Deducts transaction fees from the operator account
        - Exits the program with code 1 if creation fails
    
    Example Output:
        Transaction status: ResponseCode.SUCCESS
        Account creation successful. New Account ID: 0.0.123456
        New Account Private Key: 302e020100300506032b657004220420...
        New Account Public Key: 302a300506032b6570032100...
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
