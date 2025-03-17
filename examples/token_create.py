"""
This is a simple example of how to create a token using setting methods.

It:
1. Loads environment variables.
2. Sets up a client and creates a token with the given parameters.
3. Executes the token creation and prints the result.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY (mandatory)
- ADMIN_KEY, SUPPLY_KEY, FREEZE_KEY (optional)

Dependencies:
- dotenv
- hiero_sdk_python
"""

# Adapt imports and paths as appropriate
import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    Network,
    TokenType
    )

# Load environment variables from .env file
load_dotenv()

def create_token():
    """Function to create a fungible token on the Hedera network."""

    # Network Setup
    network = Network(network='testnet')
    client = Client(network)

    # Operator credentials (must be present)
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))

    # Optional Token Keys
    admin_key = PrivateKey.from_string(os.getenv('ADMIN_KEY'))# Optional
    supply_key = PrivateKey.from_string(os.getenv('SUPPLY_KEY')) # Optional
    freeze_key = PrivateKey.from_string(os.getenv('FREEZE_KEY')) # Optional

    # Set the operator for the client
    client.set_operator(operator_id, operator_key)

    # Create the token creation transaction
    # In this example, we set up a default empty token create transaction, then set the values
    transaction = (
        TokenCreateTransaction()
        .set_token_name("MyToken")
        .set_token_symbol("MTK")
        .set_decimals(2) # 0 for NON_FUNGIBLE_UNIQUE
        .set_initial_supply(10) # 0 for NON_FUNGIBLE_UNIQUE
        .set_treasury_account_id(operator_id) # Also known as treasury account
        .set_token_type(TokenType.FUNGIBLE_COMMON) # or TokenType.NON_FUNGIBLE_UNIQUE
        .set_admin_key(admin_key) # Optional
        .set_supply_key(supply_key) # Optional
        .set_freeze_key(freeze_key) # Optional
        .freeze_with(client) # Freeze the transaction. Returns self so we can sign.
        .sign(operator_key) # Required signature of treasury account
        .sign(admin_key) if admin_key else None  # Only sign if admin_key is present. No need to sign with the supply or freeze keys to create the token.

    )

    try:

        # Execute the transaction and get the receipt
        receipt = transaction.execute(client)

        if receipt and receipt.tokenId:
            print(f"Token created with ID: {receipt.tokenId}")
        else:
            print("Token creation failed: Token ID not returned in receipt.")
            sys.exit(1)

    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_token()
