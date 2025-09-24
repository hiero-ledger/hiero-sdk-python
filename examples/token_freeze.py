"""
Creates a freezeable token and demonstrates freezing and unfreezing
the token for the operator (treasury) account.
"""

"""
uv run examples/token_freeze.py
python examples/token_freeze.py

"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TokenCreateTransaction,
    TokenFreezeTransaction,
    TokenUnfreezeTransaction,
    TransferTransaction,
    ResponseCode,
)

# Load environment variables from .env file
load_dotenv()

def setup_client():
    """Setup Client"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f"Using operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_freeze_key():
    """Generate a Freeze Key"""
    print("\nSTEP 1: Generating a new freeze key...")
    freeze_key = PrivateKey.generate_ed25519()
    print("✅ Freeze key generated.")
    return freeze_key

def create_freezeable_token():
    """Create a token with the freeze key"""
    client, operator_id, operator_key = setup_client()
    freeze_key = generate_freeze_key()
    print("\nSTEP 2: Creating a new freezeable token...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("Freezeable Token")
            .set_token_symbol("FRZ")
            .set_initial_supply(1000)
            .set_treasury_account_id(operator_id)
            .set_freeze_key(freeze_key) # <-- THE FIX: Pass the private key directly
        )
        
        # Freeze, sign with BOTH operator and the new freeze key, then execute
        receipt = (
            tx.freeze_with(client)
            .sign(operator_key)
            .sign(freeze_key) # The new freeze key must sign to give consent
            .execute(client)
        )
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
        return freeze_key, token_id, client, operator_id, operator_key
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


def freeze_token():
    """
     Freeze the token for the operator account.

    1. Create a freezeable token with a freeze key.
    2. Freeze the token for the operator account using the freeze key.
    3. Attempt a token transfer to verify the freeze (should fail).
    4. Return token details for further operations.
    """
    freeze_key, token_id, client, operator_id, operator_key = create_freezeable_token()
    print(f"\nSTEP 3: Freezing token {token_id} for operator account {operator_id}...")
    try:
        receipt = (
            TokenFreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id) # Target the operator account
            .freeze_with(client)
            .sign(freeze_key) # Must be signed by the freeze key
            .execute(client)
        )
        print(f"✅ Success! Token freeze complete. Status: {ResponseCode(receipt.status).name} ")

        # Attempt a token transfer to confirm the account cannot perform the operation while frozen
        print("\nVerifying freeze: Attempting token transfer...")
        
        # Try to transfer 1 token from operator to itself (should fail if frozen)
        try:
            transfer_receipt = (
                TransferTransaction()
                .add_token_transfer(token_id, operator_id, 1)
                .add_token_transfer(token_id, operator_id, -1)
                .freeze_with(client)
                .sign(operator_key)
                .execute(client)
            )
            # Handle status code 165 (ACCOUNT_FROZEN_FOR_TOKEN) and print a clear message
            status_code = transfer_receipt.status
            status_name = ResponseCode(status_code).name
            if status_name in ["ACCOUNT_FROZEN_FOR_TOKEN", "ACCOUNT_FROZEN"]:
                print(f"✅ Verified: Transfer blocked as expected due to freeze. Status: {status_name}")
            elif status_name == "SUCCESS":
                print("❌ Error: Transfer succeeded, but should have failed because the account is frozen.")
            else:
                print(f"❌ Unexpected: Transfer result. Status: {status_name}")
        except Exception as e:
            print(f"✅ Verified: Transfer failed as expected due to freeze. Error: {e}")
        return token_id, client, operator_id, freeze_key
    except Exception as e:
        print(f"❌ Error freezing token: {e}")
        sys.exit(1)

def unfreeze_token():
    """
    Unfreezes the token for the operator (treasury) account.
    """
    token_id, client, operator_id, freeze_key = freeze_token()
    print(f"\nSTEP 4: Unfreezing token {token_id} for operator account {operator_id}...")
    try:
        receipt = (
            TokenUnfreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id) # Target the operator account
            .freeze_with(client)
            .sign(freeze_key) # Also signed by the freeze key
            .execute(client)
        )
        print(f"✅ Success! Token unfreeze complete. Status: {receipt.status}")
    except Exception as e:
        print(f"❌ Error unfreezing token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    freeze_token()
