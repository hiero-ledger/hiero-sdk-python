import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    Network,
)
from hiero_sdk_python.logger.logger import Logger
from hiero_sdk_python.logger.log_level import LogLevel

load_dotenv()

def show_logging_workflow():
    """Function to demonstrate logging functionality in the Hiero SDK."""

    # Retrieving network type from environment variable HEDERA_NETWORK
    network_name = os.getenv('HEDERA_NETWORK', 'testnet')
    
    # Network setup
    network = Network(network_name)
    client = Client(network)
    
    # The client comes with default logger.
    # We can create logger and replace the default logger of this client.
    # Create a custom logger with DEBUG level
    logger = Logger(level=LogLevel.DEBUG, name="hiero_sdk_python")
    # Replace the default logger
    client.logger = logger
    
    # Set the logging level for this client's logger
    client.logger.set_level(LogLevel.TRACE)
    
    # Retrieving operator ID from environment variable OPERATOR_ID
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    
    # Retrieving operator key from environment variable OPERATOR_KEY
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    
    # Setting the client operator ID and key
    client.set_operator(operator_id, operator_key)
    
    # Generate new key to use with new account
    new_key = PrivateKey.generate()
    
    print(f"Private key: {new_key.to_string()}")
    print(f"Public key: {new_key.public_key().to_string()}")
    
    # Transaction used to show trace level logging functionality from client
    transaction = (
        AccountCreateTransaction()
        .set_key(new_key.public_key())
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .freeze_with(client)
        .sign(operator_key)
    )
    
    try:
        receipt = transaction.execute(client)
        print(f"Account creation with client trace level logging successful. Account ID: {receipt.accountId}")
    except Exception as e:
        print(f"Account creation failed: {str(e)}")
    
    # Logger can be disabled
    client.logger.set_silent(True)
    
    # Create account transaction used with disabled logger
    transaction = (
        AccountCreateTransaction()
        .set_key(new_key.public_key())
        .set_initial_balance(100000000)  # 1 HBAR in tinybars
        .freeze_with(client)
        .sign(operator_key)
    )
    
    try:
        receipt = transaction.execute(client)
        print(f"Account creation with disabled logging successful. Account ID: {receipt.accountId}")
    except Exception as e:
        print(f"Account creation failed: {str(e)}")

if __name__ == "__main__":
    show_logging_workflow()
