"""
this example demonstrates deleting an NFT allowance.

- Creates an owner and spender account.
- Creates and mints an NFT.
- Approves the spender.
- Deletes the allowance.
- Verifies the spender can NO LONGER transfer the NFT.

Usage:
    python examples/account/account_allowance_delete_transaction_nft.py
    uv run examples/account/account_allowance_delete_transaction_nft.py
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
    TokenId,
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
    """Create a new Hedera account."""
    private_key = PrivateKey.generate_ed25519()
    public_key = private_key.public_key()

    tx = (
        AccountCreateTransaction()
        .set_key(public_key)
        .set_initial_balance(Hbar(10))
        .set_account_memo(memo)
        .execute(client)
    )
    # Check receipt/status for account creation
    try:
        receipt = tx
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"Account creation failed ({memo}): {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        account_id = receipt.account_id
        print(f"Created new account ({memo}): {account_id}")
        return account_id, private_key
    except Exception as e:
        print(f"Account creation exception ({memo}): {e}")
        sys.exit(1)


def create_nft_token(client, owner_id, owner_key):
    """Create a new non-fungible token (NFT)."""

    tx = (
        TokenCreateTransaction()
        .set_token_name("DeleteTest NFT")
        .set_token_symbol("DTNFT")
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

    try:
        receipt = tx.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(f"Token creation failed: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print(f"NFT Owner ({owner_id}) created NFT Token: {receipt.token_id}")
        return receipt.token_id
    except Exception as e:
        print(f"Token creation exception: {e}")
        sys.exit(1)


def mint_nft(client, token_id, metadata_list):
    """Mint NFT(s)."""
    try:
        tx = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata(metadata_list)
            .execute(client)
        )

        receipt = tx
        if receipt.status != ResponseCode.SUCCESS:
            print(f"NFT minting failed: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        serials = receipt.serial_numbers
        print(
            f"NFT Owner ({client.operator_account_id}) minted {len(serials)} NFT(s) for Token {token_id}: {serials}"
        )
        return [NftId(token_id, s) for s in serials]
    except Exception as e:
        print(f"NFT minting exception: {e}")
        sys.exit(1)


def associate_token_with_account(client, account_id, private_key, token_id):
    """Associate a token with an account."""
    try:
        tx = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(client)
            .sign(private_key)
            .execute(client)
        )

        receipt = tx
        if receipt.status != ResponseCode.SUCCESS:
            print(
                f"Token association failed for {account_id}: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)

        print(f"Associated token {token_id} with Receiver account {account_id}")
    except Exception as e:
        print(f"Token association exception for {account_id}: {e}")
        sys.exit(1)


def approve_nft_allowance_all_serials(
    client,
    token_id: TokenId,
    owner_id: AccountId,
    spender_id: AccountId,
    owner_key: PrivateKey,
):
    """Approve NFT allowance for ALL serials for a spender."""
    try:
        tx = (
            AccountAllowanceApproveTransaction()
            .approve_token_nft_allowance_all_serials(token_id, owner_id, spender_id)
            .freeze_with(client)
            .sign(owner_key)
            .execute(client)
        )

        receipt = tx
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Allowance approval failed: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print(
            f"NFT Owner ({owner_id}) approved Spender ({spender_id}) for ALL serials of token {token_id}"
        )
    except Exception as e:
        print(f"Allowance approval exception: {e}")
        sys.exit(1)


def delete_nft_allowance_all_serials(
    client,
    token_id: TokenId,
    owner_id: AccountId,
    spender_id: AccountId,
    owner_key: PrivateKey,
):
    """
    Revokes an "approve for all serials" NFT allowance from a spender.
    """
    print(
        f"NFT Owner ({owner_id}) deleting 'approve for all' allowance for {token_id} from Spender ({spender_id})..."
    )

    try:
        tx = (
            AccountAllowanceApproveTransaction()
            .delete_token_nft_allowance_all_serials(token_id, owner_id, spender_id)
            .freeze_with(client)
            .sign(owner_key)
            .execute(client)
        )

        receipt = tx
        if receipt.status != ResponseCode.SUCCESS:
            print(f"Allowance deletion failed: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print("Allowance successfully deleted.")
    except Exception as e:
        print(f"Allowance deletion exception: {e}")
        sys.exit(1)


def verify_allowance_removed(
    spender_client, nft_id: NftId, owner_id: AccountId, receiver_id: AccountId
):
    """
    Try to transfer NFT after allowance removal (should fail).
    This transaction is paid for and signed by the SPENDER.
    """
    print(
        f"\nVerifying allowance removal by Spender ({spender_client.operator_account_id}) attempting transfer..."
    )

    try:
        receipt = (
            TransferTransaction()
            .add_approved_nft_transfer(nft_id, owner_id, receiver_id)
            .execute(spender_client)
        )

        if receipt.status == ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE:
            print(
                "Verification SUCCEEDED: Transfer failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE as expected."
            )
        elif receipt.status == ResponseCode.SUCCESS:
            print(f"Verification FAILED: Transfer succeeded unexpectedly!")
            sys.exit(1)
        else:
            print(
                f"Verification FAILED: Transfer failed with an unexpected status: {ResponseCode(receipt.status).name}"
            )
            sys.exit(1)
    except Exception as e:
        print(f"Verification exception while attempting transfer as spender: {e}")
        sys.exit(1)


def main():
    """End-to-end demonstration of NFT allowance deletion."""
    owner_client, owner_id, owner_key = setup_client()

    try:
        # 1. Create accounts
        spender_id, spender_key = create_account(owner_client, "Spender")
        receiver_id, receiver_key = create_account(owner_client, "Receiver")

        # 2. Create and mint NFT
        token_id = create_nft_token(owner_client, owner_id, owner_key)
        nft_ids = mint_nft(owner_client, token_id, [b"Metadata 1"])
        nft_id = nft_ids[0]  # The specific NFT we will try to transfer

        # 3. Associate receiver
        associate_token_with_account(owner_client, receiver_id, receiver_key, token_id)

        # 4. Approve allowance (for all serials)
        approve_nft_allowance_all_serials(
            owner_client, token_id, owner_id, spender_id, owner_key
        )

        # 5. Delete the "all serials" allowance
        delete_nft_allowance_all_serials(
            owner_client, token_id, owner_id, spender_id, owner_key
        )

        # 6. Verify deletion
        print("\nSetting up client for the Spender...")
        spender_client = Client(owner_client.network)
        spender_client.set_operator(spender_id, spender_key)
        print(f"Client setup for Spender: {spender_id}")

        # We try to transfer the specific serial (nft_id)
        verify_allowance_removed(spender_client, nft_id, owner_id, receiver_id)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        owner_client.close()


if __name__ == "__main__":
    main()
