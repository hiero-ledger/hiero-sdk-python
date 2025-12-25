"""
This example demonstrates the admin key privileges for token management using Hiero SDK Python.

It shows:
1. Creating a token with an admin key
2. Demonstrating admin-only operations like updating token memo and deleting the token
3. Attempting to add a supply key (which fails because admin key cannot add new keys)
4. Updating existing keys using admin key authorization
5. Verifying operations using TokenInfoQuery

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY

Usage:
uv run examples/tokens/token_create_transaction_admin_key.py
python examples/tokens/token_create_transaction_admin_key.py
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
    TokenUpdateTransaction,
    TokenDeleteTransaction,
    TokenInfoQuery,
)

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_id, operator_key

    except (TypeError, ValueError):
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_admin_key():
    """Generate a new admin key for the token."""
    print("\nGenerating a new admin key for the token...")
    admin_key = PrivateKey.generate_ed25519()
    print("Admin key generated successfully.")
    return admin_key


def create_token_with_admin_key(client, operator_id, operator_key, admin_key):
    """
    Create a fungible token with only an admin key.
    The admin key grants privileges to update token properties and delete the token.
    """
    print("\nCreating a fungible token with admin key...")

    transaction = (
        TokenCreateTransaction()
        .set_token_name("Admin Key Demo Token")
        .set_token_symbol("AKDT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_admin_key(admin_key)  # Only admin key is set
        .freeze_with(client)
    )

    # Sign with operator (treasury) and admin key
    transaction.sign(operator_key)
    transaction.sign(admin_key)

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"✅ Token created successfully with ID: {token_id}")
    return token_id


def demonstrate_admin_update_memo(client, token_id, admin_key):
    """Demonstrate updating token memo using admin key."""
    print(f"\nUpdating token memo for {token_id} using admin key...")

    transaction = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_token_memo("Updated by admin key")
        .freeze_with(client)
        .sign(admin_key)  # Only admin key signature needed for updates
    )

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token update failed with status: {ResponseCode(receipt.status).name}")
        return False

    print("✅ Token memo updated successfully using admin key")
    return True


def demonstrate_failed_supply_key_addition(client, token_id, admin_key):
    """
    Demonstrate that admin key cannot add a new supply key if none was present during creation.
    This shows the limitation of admin key privileges.
    """
    print(f"\nAttempting to add supply key to {token_id} (this should fail)...")

    new_supply_key = PrivateKey.generate_ed25519()

    transaction = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_supply_key(new_supply_key)  # Trying to add supply key that wasn't present
        .freeze_with(client)
        .sign(admin_key)  # Admin key cannot authorize adding new keys
    )

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ As expected, adding supply key failed: {ResponseCode(receipt.status).name}"
            )
            print(
                "   Admin key cannot authorize adding keys that were not present during token creation."
            )
            return True  # Expected failure
        else:
            print("⚠️  Unexpectedly succeeded - this shouldn't happen")
            return False
    except Exception as e:
        print(f"❌ As expected, adding supply key failed with exception: {e}")
        return True


def demonstrate_admin_key_update(client, token_id, admin_key, operator_key):
    """
    Demonstrate updating the admin key itself using current admin key authorization.
    This shows admin key can change itself.
    """
    print(f"\nUpdating admin key for {token_id} to operator key...")

    transaction = (
        TokenUpdateTransaction()
        .set_token_id(token_id)
        .set_admin_key(operator_key)  # Change admin key to operator key
        .freeze_with(client)
        .sign(admin_key)  # Current admin key authorizes the change
        .sign(operator_key)  # New admin key must also sign
    )

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Admin key update failed with status: {ResponseCode(receipt.status).name}"
        )
        return False

    print("✅ Admin key updated successfully")
    return True


def demonstrate_token_deletion(client, token_id, operator_key):
    """
    Demonstrate deleting the token using admin key (now operator key).
    Note: Since we updated admin key to operator_key, we use that.
    """
    print(f"\nDeleting token {token_id} using admin key...")

    transaction = (
        TokenDeleteTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(operator_key)  # Admin key (now operator_key) signs the deletion
    )

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token deletion failed with status: {ResponseCode(receipt.status).name}")
        return False

    print("✅ Token deleted successfully using admin key")
    return True


def get_token_info(client, token_id):
    """Query and display token information."""
    try:
        info = TokenInfoQuery().set_token_id(token_id).execute(client)
        print(f"\nToken Info for {token_id}:")
        print(f"  Name: {info.name}")
        print(f"  Symbol: {info.symbol}")
        print(f"  Memo: {info.memo}")
        print(f"  Admin Key: {info.admin_key}")
        print(f"  Supply Key: {info.supply_key}")
        return info
    except Exception as e:
        print(f"Failed to get token info: {e}")
        return None


def main():
    """
    Main function demonstrating admin key capabilities:
    1. Create token with admin key
    2. Update token memo (admin privilege)
    3. Attempt to add supply key (should fail)
    4. Update admin key itself
    5. Delete token (admin privilege)
    """
    client, operator_id, operator_key = setup_client()
    admin_key = generate_admin_key()

    # Step 1: Create token with admin key
    token_id = create_token_with_admin_key(client, operator_id, operator_key, admin_key)

    # Get initial token info
    get_token_info(client, token_id)

    # Step 2: Demonstrate admin-only update
    if demonstrate_admin_update_memo(client, token_id, admin_key):
        get_token_info(client, token_id)  # Verify the update

    # Step 3: Show limitation - cannot add new keys
    demonstrate_failed_supply_key_addition(client, token_id, admin_key)

    # Step 4: Update admin key itself
    if demonstrate_admin_key_update(client, token_id, admin_key, operator_key):
        get_token_info(client, token_id)  # Verify admin key changed

    # Step 5: Delete token using admin privilege
    demonstrate_token_deletion(client, token_id, operator_key)

    print("\n🎉 Admin key demonstration completed!")


if __name__ == "__main__":
    main()
