"""
Example demonstrating NFT allowance approval and usage.
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import AccountId, Client, Hbar, Network, PrivateKey
from hiero_sdk_python.account.account_allowance_approve_transaction import (
    AccountAllowanceApproveTransaction,
)
from hiero_sdk_python.account.account_allowance_delete_transaction import (
    AccountAllowanceDeleteTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

load_dotenv()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network="testnet")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_account(client):
    """Create an account"""
    account_private_key = PrivateKey.generate_ed25519()
    account_public_key = account_private_key.public_key()

    account_receipt = (
        AccountCreateTransaction()
        .set_key(account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Account for nft allowance")
        .execute(client)
    )

    if account_receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode(account_receipt.status).name}")
        sys.exit(1)

    account_account_id = account_receipt.account_id

    return account_account_id, account_private_key


def associate_token_with_account(client, account_id, account_private_key, token_id):
    """Associate token with account"""
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Token {token_id} associated with account {account_id}")


def create_nft_token(client):
    """Create an NFT token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("Test NFT")
        .set_token_symbol("TNFT")
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.INFINITE)
        .set_treasury_account_id(client.operator_account_id)
        .set_admin_key(client.operator_private_key)
        .set_supply_key(client.operator_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"NFT token created with ID: {token_id}")
    return token_id


def mint_nft(client, token_id, metadata):
    """Mint NFT with metadata"""
    receipt = TokenMintTransaction().set_token_id(token_id).set_metadata(metadata).execute(client)

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT mint failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    if len(receipt.serial_numbers) == 0:
        print("No serial numbers returned from NFT mint")
        sys.exit(1)

    nft_ids = []
    for serial_number in receipt.serial_numbers:
        nft_ids.append(NftId(token_id, serial_number))

    print(f"Minted {len(nft_ids)} NFTs with serial numbers: {receipt.serial_numbers}")
    return nft_ids


def approve_nft_allowance(client, nft_id, owner_account_id, spender_account_id):
    """Approve NFT allowance for spender"""
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(
            nft_id.token_id, owner_account_id, spender_account_id
        )
        .execute(client)
    )

    # # Alternative approach to approve allowance for all NFT serials of a token:
    # receipt = (
    #     AccountAllowanceApproveTransaction()
    #     .approve_token_nft_allowance(nft_id, owner_account_id, spender_account_id)
    #     .execute(client)
    # )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT allowance approval failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT allowance approved for spender {spender_account_id} for NFT {nft_id}")
    return receipt


def delete_nft_allowance(client, nft_id, owner_account_id, spender_account_id):
    """Delete NFT allowance"""
    receipt = (
        AccountAllowanceDeleteTransaction()
        .delete_all_token_nft_allowances(nft_id, owner_account_id)
        .execute(client)
    )

    # # Alternative way of deleting allowance
    # receipt = (
    #     AccountAllowanceApproveTransaction()
    #     .delete_token_nft_allowance_all_serials(
    #         nft_id.token_id, owner_account_id, spender_account_id
    #     )
    #     .execute(client)
    # )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT allowance deletion failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT allowance deleted for NFT {nft_id}")
    return receipt


def transfer_nft_without_allowance(
    client, nft_id, spender_account_id, spender_private_key, receiver_account_id
):
    """Fail to transfer NFT without allowance"""
    print("Trying to transfer NFT without allowance...")
    client.set_operator(spender_account_id, spender_private_key)

    receipt = (
        TransferTransaction()
        .add_approved_nft_transfer(nft_id, spender_account_id, receiver_account_id)
        .execute(client)
    )

    if receipt.status != ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE:
        print(
            f"NFT transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE "
            f"status but got: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"NFT transfer successfully failed with {ResponseCode(receipt.status).name} status")


def nft_allowance():
    """
    Demonstrates NFT allowance functionality by:
    1. Setting up client with operator account
    2. Creating spender and receiver accounts
    3. Creating an NFT token
    4. Associating token with receiver account
    5. Minting NFTs
    6. Approving NFT allowance for spender
    7. Transferring NFT using the allowance
    8. Deleting the allowance
    9. Attempting to transfer without allowance (should fail)
    """
    client = setup_client()

    # Create spender and receiver accounts
    spender_account_id, spender_private_key = create_account(client)
    receiver_account_id, receiver_private_key = create_account(client)

    # Create NFT token
    token_id = create_nft_token(client)

    # Associate token with receiver account
    associate_token_with_account(client, receiver_account_id, receiver_private_key, token_id)

    # Mint NFTs
    metadata = [b"NFT Metadata 1", b"NFT Metadata 2"]
    nft_ids = mint_nft(client, token_id, metadata)
    nft_id = nft_ids[0]  # Use the first NFT
    nft_id_2 = nft_ids[1]  # Use the second NFT to delete the allowance

    # Approve NFT allowance for spender
    approve_nft_allowance(client, nft_id, client.operator_account_id, spender_account_id)

    receipt = (
        TransferTransaction()
        .set_transaction_id(TransactionId.generate(spender_account_id))
        .add_approved_nft_transfer(nft_id, client.operator_account_id, receiver_account_id)
        .freeze_with(client)
        .sign(spender_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"NFT transfer with allowance failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Successfully transferred NFT {nft_id} from", end=" ")
    print(f"{client.operator_account_id} to {receiver_account_id} using allowance")

    # Delete allowance
    delete_nft_allowance(client, nft_id_2, client.operator_account_id, spender_account_id)

    # Fail to transfer NFT without allowance
    transfer_nft_without_allowance(
        client, nft_id_2, spender_account_id, spender_private_key, receiver_account_id
    )


if __name__ == "__main__":
    nft_allowance()
