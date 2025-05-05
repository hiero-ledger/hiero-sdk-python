"""
This is a simple example of how to create an infinite fungible token using setting methods.

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
    TokenType,
    SupplyType
    )

# Load environment variables from .env file
load_dotenv()

def create_token_fungible_infinite():
    """Function to create an infinite fungible token."""

    # Network Setup
    network = Network(network='testnet')
    client = Client(network)

    # Operator credentials (must be present)
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))

    # Optional Token Keys
    admin_key = PrivateKey.from_string_ed25519(os.getenv('ADMIN_KEY'))# Optional
    supply_key = PrivateKey.from_string_ed25519(os.getenv('SUPPLY_KEY'))# Optional
    freeze_key = PrivateKey.from_string_ed25519(os.getenv('FREEZE_KEY'))# Optional

    # Set the operator for the client
    client.set_operator(operator_id, operator_key)

    # Create the token creation transaction
    # In this example, we set up a default empty token create transaction, then set the values
    transaction = (
        TokenCreateTransaction()
        .set_token_name("InfiniteFungibleToken")
        .set_token_symbol("IFT")
        .set_decimals(2)
        .set_initial_supply(10)  # TokenType.FUNGIBLE_COMMON must have >0 initial supply.
        .set_treasury_account_id(operator_id) # Also known as treasury account
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_max_supply(0) # SupplyType.INFINITE would require a max supply of 0
        .set_admin_key(admin_key) # Optional
        .set_supply_key(supply_key) # Optional
        .set_freeze_key(freeze_key) # Optional
        .freeze_with(client) # Freeze the transaction. Returns self so we can sign.
    )

    # Required signature by treasury (operator)
    transaction.sign(operator_key)

    # Sign with adminKey if provided
    if admin_key:
        transaction.sign(admin_key)

    try:

        # Execute the transaction and get the receipt
        receipt = transaction.execute(client)

        if receipt and receipt.tokenId:
            print(f"Infinite fungible token created with ID: {receipt.tokenId}")
        else:
            print("Infinite fungible token creation failed: Token ID not returned in receipt.")
            sys.exit(1)

    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    create_token_fungible_infinite()
