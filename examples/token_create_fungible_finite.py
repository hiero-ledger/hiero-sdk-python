"""
This is a simple example of how to create a finite fungible token using setting methods.
It:
1. Loads environment variables.
2. Sets up a client and creates a token with the given parameters.
3. Executes the token creation and prints the result.
Required environment variables:
- OPERATOR_ID, OPERATOR_KEY (mandatory)
- ADMIN_KEY, SUPPLY_KEY, FREEZE_KEY, PAUSE_KEY (optional)
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
)
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
# Load environment variables from .env file
load_dotenv()
def create_token_fungible_finite():
    """Function to create a finite fungible token."""
    # Network Setup
    network = Network(network='testnet')
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))

    def parse_optional_key(key_str):
        if not key_str or key_str.startswith('<') or key_str.endswith('>'):
            return None
        try:
            return PrivateKey.from_string_ed25519(key_str)
        except:
            return None
    
    admin_key = parse_optional_key(os.getenv('ADMIN_KEY'))
    supply_key = parse_optional_key(os.getenv('SUPPLY_KEY'))
    freeze_key = parse_optional_key(os.getenv('FREEZE_KEY'))
    pause_key = parse_optional_key(os.getenv('PAUSE_KEY'))
    # Set the operator for the client
    client.set_operator(operator_id, operator_key)
    # Create the token creation transaction
    # In this example, we set up a default empty token create transaction, then set the values
    transaction = (
        TokenCreateTransaction()
        .set_token_name("FiniteFungibleToken")
        .set_token_symbol("FFT")
        .set_decimals(2)
        .set_initial_supply(10)  # TokenType.FUNGIBLE_COMMON must have >0 initial supply. Cannot exceed max supply
        .set_treasury_account_id(operator_id) # Also known as treasury account
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .freeze_with(client) # Freeze the transaction. Returns self so we can sign.
    )
    
    # Add optional keys only if they exist
    if admin_key:
        transaction.set_admin_key(admin_key)
    if supply_key:
        transaction.set_supply_key(supply_key)
    if freeze_key:
        transaction.set_freeze_key(freeze_key)
    if pause_key:
        transaction.set_pause_key(pause_key)
    # Required signature by treasury (operator)
    transaction.sign(operator_key)
    # Sign with adminKey if provided
    if admin_key:
        transaction.sign(admin_key)
    try:
        # Execute the transaction and get the receipt
        receipt = transaction.execute(client)
        if receipt and receipt.token_id:
            print(f"Finite fungible token created with ID: {receipt.token_id}")
        else:
            print("Finite fungible token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception as e:
        print(f"Token creation failed: {str(e)}")
        sys.exit(1)
if __name__ == "__main__":
    create_token_fungible_finite()