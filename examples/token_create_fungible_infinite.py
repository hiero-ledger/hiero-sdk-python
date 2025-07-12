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
    SupplyType,
)

# Load environment variables from .env file
load_dotenv()


def create_token_fungible_infinite():
    """
    Creates an infinite fungible token by generating admin and supply keys on the fly.
    """
    # 1. Network and Operator Setup
    # =================================================================
    print("Connecting to Hedera testnet...")
    network = Network(network='testnet')
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

    # 2. Generate Keys On-the-Fly
    # =================================================================
    print("\nGenerating new admin and supply keys for the token...")
    admin_key = PrivateKey.generate_ed25519()
    supply_key = PrivateKey.generate_ed25519()
    print("✅ Keys generated successfully.")

    # 3. Build and Execute Transaction
    # =================================================================
    try:
        print("\nBuilding transaction to create an infinite fungible token...")
        transaction = (
            TokenCreateTransaction()
            .set_token_name("Infinite Fungible Token")
            .set_token_symbol("IFT")
            .set_decimals(2)
            .set_initial_supply(1000)  # Must have an initial supply > 0
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.INFINITE)
            # For infinite supply, max_supply is not set
            .set_admin_key(admin_key)    # Use the generated admin key
            .set_supply_key(supply_key)  # Use the generated supply key
            .freeze_with(client)
        )

        # Sign the transaction with all required keys
        print("Signing transaction...")
        transaction.sign(operator_key)  # Treasury account must sign
        transaction.sign(admin_key)     # The new admin key must sign
        transaction.sign(supply_key)    # The new supply key must sign

        # Execute the transaction
        print("Executing transaction...")
        receipt = transaction.execute(client)

        if receipt and receipt.token_id:
            print(f"✅ Success! Infinite fungible token created with ID: {receipt.token_id}")
        else:
            print("❌ Token creation failed: Token ID not returned in receipt.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Token creation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_token_fungible_infinite()