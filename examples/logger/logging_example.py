"""
Logging Example - Demonstrates logging functionality in the Hiero SDK

This example shows how to:
- Set up a client with custom logging
- Configure different logging levels
- Create accounts with logging enabled/disabled

Usage:
    uv run examples/logger/logging_example.py
    python examples/logger/logging_example.py
"""

import os
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    Network,
    Logger,
    LogLevel,
)

load_dotenv()


def setup_client():
    """
    Set up and configure the Hiero client with network and operator credentials.

    Returns:
        Client: Configured Hiero client ready for use
    """
    # Retrieving network type from environment variable HEDERA_NETWORK
    network_name = os.getenv("HEDERA_NETWORK", "testnet")

    # Network setup
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # Retrieving operator credentials from environment variables
    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))

    # Setting the client operator ID and key
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def set_up_logging_level(client):
    """
    Configure custom logging for the client.

    Args:
        client (Client): The Hiero client to configure logging for
    """
    # The client comes with default logger.
    # We can create logger and replace the default logger of this client.
    # Create a custom logger with DEBUG level
    logger = Logger(level=LogLevel.DEBUG, name="hiero_sdk_python")

    # Replace the default logger
    client.logger = logger

    # Set the logging level for this client's logger to TRACE for detailed output
    client.logger.set_level(LogLevel.TRACE)

    print(" Custom logger configured with TRACE level")


def create_key():
    """
    Generate a new key pair for account creation.

    Returns:
        PrivateKey: Generated private key for the new account
    """
    # Generate new key to use with new account
    new_key = PrivateKey.generate()

    print(f"Generated new key pair:")
    print(f"  Private key: {new_key.to_string()}")
    print(f"  Public key: {new_key.public_key().to_string()}")

    return new_key


def create_account(client, new_key, description=""):
    """
    Create a new account using the provided client and key.

    Args:
        client (Client): The Hiero client to use for the transaction
        new_key (PrivateKey): The private key for the new account
        description (str): Description for logging purposes

    Returns:
        str: The created account ID, or None if creation failed
    """
    # Get operator key for signing
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))

    # Create account transaction
    transaction = (
        AccountCreateTransaction()
        .set_key(new_key.public_key())
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        account_id = receipt.account_id
        print(f" Account creation {description}successful. Account ID: {account_id}")
        return str(account_id)
    except Exception as e:
        print(f" Account creation {description}failed: {str(e)}")
        return None


def logging_status(client):
    """
    Display the current logging status of the client.

    Args:
        client (Client): The client to check logging status for
    """
    if hasattr(client.logger, "_silent") and client.logger._silent:
        print(" Logging is currently DISABLED")
    else:
        print(f" Logging is currently ENABLED (Level: {client.logger.level})")


def show_logging_workflow():
    """
    Main function to demonstrate logging functionality in the Hiero SDK.

    This function orchestrates the entire logging demonstration workflow:
    1. Sets up the client
    2. Configures custom logging
    3. Creates an account with logging enabled
    4. Disables logging
    5. Creates another account with logging disabled
    """
    print("=== Hiero SDK Logging Example ===")
    print()

    # Step 1: Set up client
    print("1. Setting up client...")
    client = setup_client()
    print(" Client setup complete")
    print()

    # Step 2: Configure logging
    print("2. Configuring custom logging...")
    set_up_logging_level(client)
    logging_status(client)
    print()

    # Step 3: Generate key
    print("3. Generating new key pair...")
    new_key = create_key()
    print()

    # Step 4: Create account with logging enabled
    print("4. Creating account with TRACE logging enabled...")
    logging_status(client)
    account_id_1 = create_account(client, new_key, "with trace logging ")
    print()

    # Step 5: Disable logging
    print("5. Disabling logging...")
    client.logger.set_silent(True)
    logging_status(client)
    print()

    # Step 6: Create account with logging disabled
    print("6. Creating account with logging disabled...")
    account_id_2 = create_account(client, new_key, "with disabled logging ")
    print()

    # Summary
    print("=== Summary ===")
    if account_id_1:
        print(f" Account created with logging: {account_id_1}")
    if account_id_2:
        print(f" Account created without logging: {account_id_2}")
    print(" Logging workflow demonstration complete!")


if __name__ == "__main__":
    show_logging_workflow()
