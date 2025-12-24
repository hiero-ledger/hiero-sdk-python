"""
uv run examples/tokens/token_associate_transaction.py
python examples/tokens/token_associate_transaction.py

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
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """
    Initialize and set up the client with operator account.

    Returns:
        tuple: Configured client, operator account ID, and operator private key

    Raises:
        SystemExit: If operator credentials are invalid or missing
    """
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
            .set_key_without_alias(new_account_public_key)
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


def associate_two_tokens_mixed_types_with_set_token_ids(
    client, token_id_1, token_id_2, account_id, account_key
):
    """
    Associate two tokens using set_token_ids() with mixed types:
    - first as TokenId
    - second as string
    """
    try:
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .set_token_ids(
                [
                    token_id_1,  # TokenId instance
                    str(token_id_2),  # string representation → converted internally
                ]
            )
            .freeze_with(client)
            .sign(account_key)
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token association (mixed types) failed with status: "
                f"{ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        print("✅ Success! Token association completed.")
        print(
            f"   Account {account_id} can now hold and transfer tokens {token_id_1} and {token_id_2}"
        )
    except Exception as e:
        print(f"❌ Error in while associating tokens: {e}")
        sys.exit(1)


def demonstrate_invalid_set_token_ids_usage(client, account_id, account_key):
    """
    Example 4: demonstrate that set_token_ids() rejects invalid types,
    i.e. values that are neither TokenId nor string.
    """
    print("`set_token_ids()` only accepts a list of TokenId or strings (also mixed)")
    invalid_value = 123  # ❌ This type is not supported from `set_token_ids()`
    print(f"Trying to associate a token using a list of {type(invalid_value)}")

    try:
        receipt = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .set_token_ids([invalid_value])  # this should fail
            .freeze_with(client)
            .sign(account_key)
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

    except Exception as e:
        if (
            type(e) == TypeError
            and "Invalid token_id type: expected TokenId or str, got" in e.args[0]
        ):
            print(
                "✅ Correct behavior: invalid token_id type was rejected from `set_token_ids`"
            )
            print(f"   Error: {e}")
        else:
            print(f"❌ Unexpected error while creating transaction: {e}")
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

    # step 3: How to not use set_token_ids
    print("\nSTEP 3: Demonstrating invalid input handling in set_token_ids...")
    demonstrate_invalid_set_token_ids_usage(client, account_id, account_private_key)

    # Step 4: new tokens
    print("\nSTEP 4: Creating new fungible tokens...")
    token_id_0 = create_fungible_token(client, operator_id, operator_key)
    token_id_1 = create_fungible_token(client, operator_id, operator_key)
    token_id_2 = create_fungible_token(client, operator_id, operator_key)

    # Step 5: Associate a single token with the new account
    print(f"\nSTEP 5: Associating token {token_id_0} with account {account_id}...")
    associate_token_with_account(client, token_id_0, account_id, account_private_key)

    # Step 6: Associate multiple tokens with the new account
    print(
        f"\nSTEP 6: Associating token {token_id_1} and token {token_id_2} with account {account_id}..."
    )
    associate_two_tokens_mixed_types_with_set_token_ids(
        client, token_id_1, token_id_2, account_id, account_private_key
    )

    # Step 7: Verify the token association
    print(f"\nSTEP 7: Verifying token association...")
    is_associated = verify_token_association(client, account_id, token_id_0)
    is_associated = verify_token_association(client, account_id, token_id_1)
    is_associated = verify_token_association(client, account_id, token_id_2)

    tokens = [token_id_0, token_id_1, token_id_2]
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Token Association Demo Completed Successfully!")
    print(f"   New Account: {account_id}")
    print("   New Tokens:")

    for token in tokens:
        print(f"    -{token}")
    print(f"   Association: {'✅ VERIFIED' if is_associated else '❌ FAILED'}")
    print("=" * 50)


if __name__ == "__main__":
    main()
