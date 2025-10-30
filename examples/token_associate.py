"""
uv run examples/token_associate.py
python examples/token_associate.py

A modular example demonstrating token association on Hedera testnet.
This script shows the complete workflow: client setup, account creation,
token creation, token association, and verification.
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountInfoQuery,
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
    AccountCreateTransaction,
    TokenCreateTransaction,
    TokenAssociateTransaction,
    ResponseCode,
)

# Load environment variables from .env file
load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()


def setup_client():
    """
    Initialize and set up the client with operator account.

    Returns:
        tuple: Configured client, operator account ID, and operator private key

    Raises:
        SystemExit: If operator credentials are invalid or missing
    """
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
        print(f"✅ Client configured with operator account: {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def create_test_account(client, operator_key):
    """
    Create a new test account for demonstration.

    Args:
        client: Configured Hedera client instance
        operator_key: Operator's private key for signing the transaction

    Returns:
        tuple: New account ID and private key

    Raises:
        SystemExit: If account creation fails
    """
    new_account_private_key = PrivateKey.generate_ed25519()
    new_account_public_key = new_account_private_key.public_key()

    try:
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .set_account_memo("Test account for token association demo")
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Account creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)
        new_account_id = receipt.account_id
        print(f"✅ Success! Created new account with ID: {new_account_id}")
        return new_account_id, new_account_private_key
    except Exception as e:
        print(f"❌ Error creating new account: {e}")
        sys.exit(1)

def create_fungible_token(client, operator_id, operator_key):
    """
    Create a fungible token for association with test account.

    Args:
        client: Configured Hedera client instance
        operator_id: Operator account ID to use as token treasury
        operator_key: Operator's private key for signing the transaction

    Returns:
        TokenId: The created token's ID

    Raises:
        SystemExit: If token creation fails
    """
    try:
        receipt = (
            TokenCreateTransaction()
            .set_token_name("DemoToken")
            .set_token_symbol("DTK")
            .set_decimals(2)
            .set_initial_supply(100000)  # 1000.00 tokens with 2 decimals
            .set_treasury_account_id(operator_id)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)
        token_id = receipt.token_id
        print(f"✅ Success! Created token with ID: {token_id}")
        print(f"   Treasury: {operator_id}")
        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

def associate_token_with_account(client, token_id, account_id, account_key):
    """
    Associate the token with the test account.

    Args:
        client: Configured Hedera client instance
        token_id: Token ID to associate
        account_id: Account ID to associate the token with
        account_key: Account's private key for signing the transaction

    Raises:
        SystemExit: If token association fails
    """
    try:
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(client)
            .sign(account_key)
            .execute(client)
        )
    
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token association failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)
        print(f"✅ Success! Token association complete.")
        print(f"   Account {account_id} can now hold and transfer token {token_id}")
    except Exception as e:
        print(f"❌ Error associating token with account: {e}")
        sys.exit(1)

def verify_token_association(client, account_id, token_id):
    """
    Verify that a token is properly associated with an account.

    Args:
        client: Configured Hedera client instance
        account_id: Account ID to check
        token_id: Token ID to verify association for

    Returns:
        bool: True if token is associated, False otherwise
    """
    try:
        # Query account information
        info = AccountInfoQuery(account_id).execute(client)

        # Check if the token is in the account's token relationships
        if info.token_relationships:
            for relationship in info.token_relationships:
                if str(relationship.token_id) == str(token_id):
                    print(f"✅ Verification Successful!")
                    print(
                        f"   Token {token_id} is associated with account {account_id}"
                    )
                    print(f"   Balance: {relationship.balance}")
                    return True
        print(f"❌ Verification Failed!")
        print(f"   Token {token_id} is NOT associated with account {account_id}")
        if info.token_relationships:
            associated_tokens = [str(rel.token_id) for rel in info.token_relationships]
            print(f"   Associated tokens found: {associated_tokens}")
        else:
            print(f"   No token associations found for this account")
        return False
    except Exception as e:
        print(f"❌ Error verifying token association: {e}")
        return False


def main():
    """
    Demonstrate the complete token association workflow.

    Steps:
    1. Set up client with operator credentials
    2. Create a new test account
    3. Create a fungible token
    4. Associate the token with the test account
    5. Verify the token association was successful
    """
    print("🚀 Starting Token Association Demo")
    print("=" * 50)

    # Step 1: Set up client
    print("\nSTEP 1: Setting up client...")
    client, operator_id, operator_key = setup_client()

    # Step 2: Create a new account
    print("\nSTEP 2: Creating a new account...")
    account_id, account_private_key = create_test_account(client, operator_key)

    # Step 3: Create a new token
    print("\nSTEP 3: Creating a new fungible token...")
    token_id = create_fungible_token(client, operator_id, operator_key)

    # Step 4: Associate the token with the new account
    print(f"\nSTEP 4: Associating token {token_id} with account {account_id}...")
    associate_token_with_account(client, token_id, account_id, account_private_key)

    # Step 5: Verify the token association
    print(f"\nSTEP 5: Verifying token association...")
    is_associated = verify_token_association(client, account_id, token_id)

    # Summary
    print("\n" + "=" * 50)
    print("🎉 Token Association Demo Completed Successfully!")
    print(f"   New Account: {account_id}")
    print(f"   New Token: {token_id}")
    print(f"   Association: {'✅ VERIFIED' if is_associated else '❌ FAILED'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
