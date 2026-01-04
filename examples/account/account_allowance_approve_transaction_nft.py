"""
Example: Approving an NFT allowance and transferring the NFT using it.

Why:
    This example demonstrates how to use the Hiero Python SDK to approve and
    execute an NFT allowance when interacting with the Hedera network.

Key Concepts:
    - Owner: The account that owns the NFT and grants the allowance.
    - Spender: The account approved to transfer the Owner's NFT.
    - Receiver: The account that will receive the NFT.
    - NFT Allowance: Permission granted by the Owner to the Spender to transfer NFTs.

High-Level Steps:
    Pre-requisites:
        1. Create Owner, Spender, and Receiver accounts.
        2. Create and mint an NFT to the Owner.

    Required:
        3. Approve the Spender to transfer the Owner's NFT.

    Demonstration:
        4. Associate the NFT with the Receiver account.
        5. Transfer the NFT using the approved allowance.

Usage:
    uv run examples/account/account_allowance_approve_transaction_nft.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
    ResponseCode,
    TokenCreateTransaction,
    TokenType,
    SupplyType,
    TokenMintTransaction,
    NftId,
    TokenAssociateTransaction,
    AccountAllowanceApproveTransaction,
    TransferTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    if os.getenv("OPERATOR_ID") is None or os.getenv("OPERATOR_KEY") is None:
        print("Environment variables OPERATOR_ID and OPERATOR_KEY must be set")
        sys.exit(1)

    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id_str = os.getenv("OPERATOR_ID")
    operator_key_str = os.getenv("OPERATOR_KEY")
    assert operator_id_str is not None and operator_key_str is not None

    operator_id = AccountId.from_string(operator_id_str)
    operator_key = PrivateKey.from_string(operator_key_str)

    client.set_operator(operator_id, operator_key)
    print(f"Client setup for NFT Owner (Operator): {client.operator_account_id}")
    return client, operator_id, operator_key


def create_account(client, memo="Test Account"):
    """Create a new Hedera account with an initial balance."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    tx = (
        AccountCreateTransaction()
        .set_key(public_key)
        .set_initial_balance(Hbar(10))
        .set_account_memo(memo)
        .execute(client)
    )

    if tx.status != ResponseCode.SUCCESS:
        print(f"Account creation failed: {ResponseCode(tx.status).name}")
        sys.exit(1)

    account_id = tx.account_id
    print(f"Created new account ({memo}): {account_id}")
    return account_id, private_key


def create_nft_token(client, owner_id, owner_key):
    """Create a new non-fungible token (NFT) with the owner as treasury."""

    tx = (
        TokenCreateTransaction()
        .set_token_name("ApproveTest NFT")
        .set_token_symbol("ATNFT")
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(owner_id)
        .set_supply_type(SupplyType.INFINITE)
        .set_admin_key(owner_key)
        .set_supply_key(owner_key)
        .freeze_with(client)
        .sign(owner_key)
    )

    receipt = tx.execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT Owner ({owner_id}) created NFT Token: {receipt.token_id}")
    return receipt.token_id


def mint_nft(client, token_id, metadata_list):
    """Mint NFT(s) with metadata."""
    tx = (
        TokenMintTransaction()
        .set_token_id(token_id)
        .set_metadata(metadata_list)
        .execute(client)
    )

    if tx.status != ResponseCode.SUCCESS:
        print(f"Mint failed: {ResponseCode(tx.status).name}")
        sys.exit(1)

    serials = tx.serial_numbers
    print(
        f"NFT Owner ({client.operator_account_id}) minted {len(serials)} NFT(s) for Token {token_id}: {serials}"
    )
    return [NftId(token_id, s) for s in serials]


def associate_token_with_account(client, account_id, private_key, token_id):
    """Associate a token with an account."""
    tx = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(private_key)
        .execute(client)
    )

    if tx.status != ResponseCode.SUCCESS:
        print(f"Association failed: {ResponseCode(tx.status).name}")
        sys.exit(1)

    print(f"Associated token {token_id} with Receiver account {account_id}")


def approve_nft_allowance(client, nft_id, owner_id, spender_id, owner_key):
    """Approve NFT allowance for a spender."""
    tx = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(nft_id.token_id, owner_id, spender_id)
        .freeze_with(client)
        .sign(owner_key)
        .execute(client)
    )

    if tx.status != ResponseCode.SUCCESS:
        print(f"Approval failed: {ResponseCode(tx.status).name}")
        sys.exit(1)

    print(
        f"NFT Owner ({owner_id}) approved Spender ({spender_id}) for NFT {nft_id.token_id} (all serials)"
    )


def transfer_nft_using_allowance(spender_client, nft_id, owner_id, receiver_id):
    """Transfer an NFT using approved allowance via the spender client."""
    print(
        f"Spender ({spender_client.operator_account_id}) transferring NFT {nft_id} from Owner ({owner_id})..."
    )

    tx = (
        TransferTransaction()
        .add_approved_nft_transfer(nft_id, owner_id, receiver_id)
        .execute(spender_client)
    )

    if tx.status != ResponseCode.SUCCESS:
        print(f"Transfer failed: {ResponseCode(tx.status).name}")
        sys.exit(1)

    print(
        f"SUCCESS: Spender ({spender_client.operator_account_id}) transferred NFT {nft_id} to Receiver ({receiver_id})"
    )


def main():
    """End-to-end demonstration."""
    owner_client, owner_id, owner_key = setup_client()

    try:
        # Create spender and receiver accounts
        spender_id, spender_key = create_account(owner_client, "Spender")
        receiver_id, receiver_key = create_account(owner_client, "Receiver")

        # Create and mint NFT
        token_id = create_nft_token(owner_client, owner_id, owner_key)
        nft_ids = mint_nft(owner_client, token_id, [b"Metadata 1"])
        nft_id = nft_ids[0]

        # Associate token with receiver
        associate_token_with_account(owner_client, receiver_id, receiver_key, token_id)

        # Approve allowance
        approve_nft_allowance(owner_client, nft_id, owner_id, spender_id, owner_key)

        # Create a client for the spender
        print("\nSetting up client for the Spender...")
        spender_client = Client(owner_client.network)
        spender_client.set_operator(spender_id, spender_key)
        print(f"Client setup for Spender: {spender_id}")

        # Transfer NFT using the allowance
        transfer_nft_using_allowance(spender_client, nft_id, owner_id, receiver_id)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        owner_client.close()


if __name__ == "__main__":
    main()
