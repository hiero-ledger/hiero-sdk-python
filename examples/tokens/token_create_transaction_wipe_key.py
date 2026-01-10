"""
This example demonstrates the Wipe Key privileges for token management using Hiero SDK Python.

It shows:
1. Creating a FUNGIBLE token WITHOUT a wipe key.
2. Attempting to wipe tokens (which fails because no wipe key exists).
3. Creating a FUNGIBLE token WITH a wipe key.
4. Associating and transferring tokens to a user account.
5. Wiping tokens from that user's account using the wipe key.
6. Verifying the total supply has decreased (effectively burning).
7. Creating an NFT (Non-Fungible) token with a wipe key.
8. Wiping a specific NFT Serial Number from a user account.

Required environment variables:
- OPERATOR_ID, OPERATOR_KEY

Usage:
uv run examples/tokens/token_create_transaction_wipe_key.py
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
    TokenWipeTransaction,
    TokenAssociateTransaction,
    TransferTransaction,
    AccountCreateTransaction,
    TokenInfoQuery,
    TokenMintTransaction,
    Hbar,
    NftId,  # <--- FIX 1: Added NftId import
)

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """
    Initialise and return a Hiero SDK client based on environment variables.
    """
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set-up with operator id {client.operator_account_id}.")
        return client, operator_id, operator_key

    except (TypeError, ValueError):
        print(
            "Error: please check OPERATOR_ID and OPERATOR_KEY in you environment file."
        )
        sys.exit(1)


def create_recipient_account(client):
    """
    Helper: Create a new account to hold tokens(wiped ones)
    """
    private_key = PrivateKey.generate_ed25519()
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(private_key.public_key())
        .set_initial_balance(Hbar(2))
    )
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"❌ Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"✅ Account created: {receipt.account_id}")
    return receipt.account_id, private_key


def associate_and_transfer(client, token_id, recipient_id, recipient_key, amount):
    """Helper: Associate token to recipient and transfer tokens to them"""

    associate_tx = (
        TokenAssociateTransaction()
        .set_account_id(recipient_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(recipient_key)
    )
    receipt_associate = associate_tx.execute(client)

    if receipt_associate.status != ResponseCode.SUCCESS:
        print(
            f"❌ Token association failed with status: {ResponseCode(receipt_associate.status).name}"
        )
        sys.exit(1)
    print(f"  --> Associated token {token_id} to account {recipient_id}.")

    transfer_tx = (
        TransferTransaction()
        .add_token_transfer(token_id, client.operator_account_id, -amount)
        .add_token_transfer(token_id, recipient_id, amount)
    )

    receipt_transfer = transfer_tx.execute(client)

    if receipt_transfer.status != ResponseCode.SUCCESS:
        print(
            f"❌ Token transfer failed with status: {ResponseCode(receipt_transfer.status).name}"
        )
        sys.exit(1)
    print(f"  --> Transferred {amount} tokens to account {recipient_id}.")


def create_token_no_wipe_key(client, operator_id, operator_key):
    """Create a token WITHOUT a wipe key."""
    print("\n--- Scenario 1: Token WITHOUT Wipe Key ---")
    print("Creating token WITHOUT a wipe key...")

    transaction = (
        TokenCreateTransaction()
        .set_token_name("No Wipe Token")
        .set_token_symbol("NWT")
        .set_decimals(0)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        # No wipe key set here
        .freeze_with(client)
    )
    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        print(f"✅ Token created: {receipt.token_id}")
        return receipt.token_id

    except Exception as e:
        print(f"❌ Token creation failed with error: {e}")
        sys.exit(1)


def demonstrate_wipe_fail(client, token_id, target_account_id):
    """Attempt to wipe tokens when no wipe key exists. Should FAIL."""
    print(f"Attempting to wipe tokens from {target_account_id} (Should FAIL)...")

    transaction = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(target_account_id)
        .set_amount(10)
        .freeze_with(client)
    )

    try:
        # Since no wipe key exists on the token, Hiero will reject this.
        receipt = transaction.execute(client)
        if receipt.status == ResponseCode.TOKEN_HAS_NO_WIPE_KEY:
            print(
                f"✅ Wipe failed as expected! Token has no wipe key with status: {ResponseCode(receipt.status).name}."
            )
        else:
            print(
                f"❌ Wipe unexpectedly succeeded or failed with status: {ResponseCode(receipt.status).name}"
            )

    except Exception as e:
        print(f"✅ Wipe failed as expected with error: {e}")


def create_token_with_wipe_key(client, operator_id, operator_key):
    """Create a token WITH a wipe key."""
    print("\n--- Scenario 2: Token WITH Wipe Key ---")
    print("Creating token WITH a wipe key...")
    wipe_key = PrivateKey.generate_ed25519()

    transaction = (
        TokenCreateTransaction()
        .set_token_name("With Wipe Token")
        .set_token_symbol("WWT")
        .set_decimals(0)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_wipe_key(wipe_key)  # Setting the wipe key
        .freeze_with(client)
    )
    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"❌ Token creation failed with status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        print(f"✅ Token created: {receipt.token_id}")
        return receipt.token_id, wipe_key

    except Exception as e:
        print(f"❌ Token creation failed with error: {e}")
        sys.exit(1)


def demonstrate_wipe_success(client, token_id, target_account_id, wipe_key):
    """Wipe tokens using the valid wipe key."""
    print(f"Wiping 10 tokens from {target_account_id} using Wipe Key...")

    transaction = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(target_account_id)
        .set_amount(10)
        .freeze_with(client)
    )

    # Critical: Sign with the wipe key
    transaction.sign(wipe_key)

    receipt = transaction.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Wipe failed with status: {ResponseCode(receipt.status).name}")
        return False

    print(f"✅ Wipe Successful!")
    return True


def verify_supply(client, token_id):
    """Check the total supply to verify burn occurred."""
    info = TokenInfoQuery().set_token_id(token_id).execute(client)
    print(f"   -> New Total Supply: {info.total_supply} (Should be 990)")


def demonstrate_nft_wipe_scenario(client, operator_id, operator_key, user_id, user_key):
    """
    Scenario 3: Create an NFT, Mint it, Transfer it, and then Wipe it.
    This demonstrates that Wipe Key works for NON_FUNGIBLE_UNIQUE tokens as well.
    """
    print("\n--- Scenario 3: NFT Wipe with Wipe Key ---")
    print("Creating an NFT Collection with a Wipe Key...")

    wipe_key = PrivateKey.generate_ed25519()
    supply_key = PrivateKey.generate_ed25519()  # Needed to mint the NFT first

    # 1. Create the NFT Token
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Wipeable NFT")
        .set_token_symbol("W-NFT")
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_initial_supply(0)
        .set_treasury_account_id(operator_id)
        .set_admin_key(operator_key)
        .set_supply_key(supply_key)  # Required to mint
        .set_wipe_key(wipe_key)  # Required to wipe
        .freeze_with(client)
    )
    transaction.sign(operator_key)

    receipt = transaction.execute(client)
    nft_token_id = receipt.token_id
    print(f"✅ NFT Token created: {nft_token_id}")

    # 2. Mint an NFT (Serial #1)
    print("Minting NFT Serial #1...")
    mint_tx = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata([b"Metadata for NFT 1"])
        .freeze_with(client)
    )
    mint_tx.sign(supply_key)
    mint_receipt = mint_tx.execute(client)
    serial_number = mint_receipt.serial_numbers[0]
    print(f"✅ Minted NFT Serial: {serial_number}")

    # 3. Associate User and Transfer NFT to them
    print(f"Transferring NFT #{serial_number} to user {user_id}...")

    # Associate
    associate_tx = (
        TokenAssociateTransaction()
        .set_account_id(user_id)
        .add_token_id(nft_token_id)
        .freeze_with(client)
        .sign(user_key)
    ).execute(client)

    # Transfer
    # FIX 2: Use NftId(token_id, serial_number)
    transfer_tx = (
        TransferTransaction()
        .add_nft_transfer(NftId(nft_token_id, serial_number), operator_id, user_id)
        .execute(client)
    )
    print(f"✅ Transfer complete.")

    # 4. Wipe the NFT from the User
    print(f"Attempting to WIPE NFT #{serial_number} from user {user_id}...")

    wipe_tx = (
        TokenWipeTransaction()
        .set_token_id(nft_token_id)
        .set_account_id(user_id)
        .set_serial([serial_number])
        .freeze_with(client)
    )
    wipe_tx.sign(wipe_key)  # Sign with Wipe Key

    wipe_receipt = wipe_tx.execute(client)

    if wipe_receipt.status == ResponseCode.SUCCESS:
        print(
            "✅ NFT Wipe Successful! The NFT has been effectively burned from the user's account."
        )
    else:
        print(f"❌ NFT Wipe Failed: {ResponseCode(wipe_receipt.status).name}")


def main():
    """
    Main execution flow:
    1. Setup Client
    2. Create a recipient account
    3. Scenario 1: Fail to wipe without key (Fungible)
    4. Scenario 2: Successfully wipe with key (Fungible)
    5. Scenario 3: Successfully wipe with key (NFT)
    """
    client, operator_id, operator_key = setup_client()

    # Create a generic user to hold tokens
    print("\nCreating a user account to hold tokens...")
    user_id, user_key = create_recipient_account(client)
    print(f"User created: {user_id}")

    # --- Scenario 1: No Wipe Key (Fungible) ---
    token_id_no_key = create_token_no_wipe_key(client, operator_id, operator_key)
    associate_and_transfer(client, token_id_no_key, user_id, user_key, 50)
    demonstrate_wipe_fail(client, token_id_no_key, user_id)

    # --- Scenario 2: With Wipe Key (Fungible) ---
    token_id_with_key, wipe_key = create_token_with_wipe_key(
        client, operator_id, operator_key
    )
    associate_and_transfer(client, token_id_with_key, user_id, user_key, 50)

    if demonstrate_wipe_success(client, token_id_with_key, user_id, wipe_key):
        verify_supply(client, token_id_with_key)

    # --- Scenario 3: NFT Wipe (Non-Fungible) ---
    demonstrate_nft_wipe_scenario(client, operator_id, operator_key, user_id, user_key)

    print("\n🎉 Wipe key demonstration completed!")


if __name__ == "__main__":
    main()
