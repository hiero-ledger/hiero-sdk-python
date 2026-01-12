"""
Usage:
uv run examples/tokens/token_create_transaction_nft_infinite.py
python examples/tokens/token_create_transaction_nft_infinite.py
"""


import sys
from hiero_sdk_python import (
    Client,
    PrivateKey,
    TokenCreateTransaction,
    TokenType,
    SupplyType,
)


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

""" 
2. Generate Keys On-the-Fly
"""


def keys_on_fly():
    print("\nGenerating new admin and supply keys for the NFT...")
    admin_key = PrivateKey.generate_ed25519()
    supply_key = PrivateKey.generate_ed25519()
    print("Keys generated successfully.")
    return admin_key, supply_key


""" 
3. Build and Execute Transaction
"""


def transaction(client, operator_id, operator_key, admin_key, supply_key):
    try:
        print("\nBuilding transaction to create an infinite NFT...")
        transaction = (
            TokenCreateTransaction()
            .set_token_name("Infinite NFT")
            .set_token_symbol("INFT")
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(operator_id)
            .set_initial_supply(0)  # NFTs must have an initial supply of 0
            .set_supply_type(SupplyType.INFINITE)  # Infinite supply
            .set_admin_key(admin_key)  # Generated admin key
            .set_supply_key(supply_key)  # Generated supply key
            .freeze_with(client)
        )

        # Sign the transaction with required keys
        print("Signing transaction...")
        transaction.sign(operator_key)  # Treasury account must sign
        transaction.sign(admin_key)  # Admin key must sign
        transaction.sign(supply_key)  # Supply key must sign

        # Execute the transaction
        print("Executing transaction...")
        receipt = transaction.execute(client)

        if receipt and receipt.token_id:
            print(
                f"Success! Infinite non-fungible token created with ID: {receipt.token_id}"
            )
            return receipt.token_id
        else:
            print("Token creation failed: Token ID not returned in receipt.")
            sys.exit(1)

    except Exception as e:
        print(f"Token creation failed: {e}")
        sys.exit(1)


"""
Creates an infinite NFT by generating admin and supply keys on the fly.
"""


def create_token_nft_infinite():
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key
    admin_key, supply_key = keys_on_fly()
    token_id = transaction(client, operator_id, operator_key, admin_key, supply_key)
    print(f"\nCreated token: {token_id}")


if __name__ == "__main__":
    create_token_nft_infinite()
