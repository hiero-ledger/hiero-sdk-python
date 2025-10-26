"""
Example demonstrating NFT allowance approval and usage.

This script walks through the end-to-end process of setting up accounts, 
creating and minting an NFT, approving a spending allowance for a third party (spender), 
using the allowance to transfer the NFT, and then deleting the allowance.
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
    """Initializes and sets up the client with operator account credentials.

    Loads OPERATOR_ID and OPERATOR_KEY from environment variables and configures 
    the client to connect to the Hedera testnet.

    Returns:
        Client: The initialized client configured with operator credentials.
    
    Raises:
        SystemExit: If account initialization fails.
    """
    network = Network(network="testnet")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
    client.set_operator(operator_id, operator_key)

    return client


def create_account(client):
    """Creates a new Hedera account with a small initial balance.

    Generates a new Ed25519 private key for the account.

    Args:
        client (Client): The client instance used to submit the transaction.

    Returns:
        tuple[AccountId, PrivateKey]: The ID and private key of the newly created account.

    Raises:
        SystemExit: If the account creation fails.
    """
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
    """Associates a given TokenId with a target account.

    The target account's private key is used to sign the association transaction.

    Args:
        client (Client): The client instance.
        account_id (AccountId): The ID of the account to associate the token with.
        account_private_key (PrivateKey): The private key of the account to sign the transaction.
        token_id (TokenId): The ID of the token to be associated.

    Raises:
        SystemExit: If the token association fails.
    """
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
    """Creates a new Non-Fungible Token (NFT) with infinite supply.

    The operator account is set as the treasury, admin key, and supply key.

    Args:
        client (Client): The client instance.

    Returns:
        TokenId: The ID of the newly created NFT token.

    Raises:
        SystemExit: If the NFT token creation fails.
    """
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
    """Mints new NFTs under the created token ID.

    Args:
        client (Client): The client instance.
        token_id (TokenId): The ID of the NFT token.
        metadata (List[bytes]): A list of byte arrays representing the metadata for each new NFT.

    Returns:
        List[NftId]: A list of NftId objects corresponding to the newly minted serial numbers.

    Raises:
        SystemExit: If the NFT minting process fails or returns no serial numbers.
    """
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
    """Approves an NFT allowance for a spender across all serials of a token.

    Uses AccountAllowanceApproveTransaction to delegate spending authority.

    Args:
        client (Client): The client instance.
        nft_id (NftId): The ID of a specific NFT (used here to reference the TokenId).
        owner_account_id (AccountId): The account ID of the NFT owner (delegator).
        spender_account_id (AccountId): The account ID receiving spending authority.

    Returns:
        TransactionResponse: The receipt of the allowance approval transaction.

    Raises:
        SystemExit: If the allowance approval fails.
    """
    receipt = (
        AccountAllowanceApproveTransaction()
        .approve_token_nft_allowance_all_serials(
            nft_id.token_id, owner_account_id, spender_account_id
        )
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT allowance approval failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT allowance approved for spender {spender_account_id} for NFT {nft_id}")
    return receipt


def delete_nft_allowance(client, nft_id, owner_account_id, spender_account_id):
    """Deletes all NFT allowance approvals for a token given by NftId.

    Uses AccountAllowanceDeleteTransaction to revoke spending authority.

    Args:
        client (Client): The client instance.
        nft_id (NftId): The ID of an NFT (used here to reference the TokenId).
        owner_account_id (AccountId): The account ID of the NFT owner.
        spender_account_id (AccountId): The account ID whose allowance is being deleted.

    Returns:
        TransactionResponse: The receipt of the allowance deletion transaction.

    Raises:
        SystemExit: If the allowance deletion fails.
    """
    receipt = (
        AccountAllowanceDeleteTransaction()
        .delete_all_token_nft_allowances(nft_id.token_id, owner_account_id)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT allowance deletion failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT allowance deleted for NFT {nft_id}")
    return receipt


def transfer_nft_without_allowance(
    client, nft_id, spender_account_id, spender_private_key, receiver_account_id
):
    """Attempts to transfer an NFT using a spender's key without prior allowance.

    This function is intended to fail, verifying the allowance system is working.

    Args:
        client (Client): The client instance.
        nft_id (NftId): The ID of the NFT to attempt transferring.
        spender_account_id (AccountId): The account ID of the unauthorized spender.
        spender_private_key (PrivateKey): The private key of the unauthorized spender.
        receiver_account_id (AccountId): The target receiver account ID.

    Raises:
        SystemExit: If the transfer fails with the *wrong* error status (i.e., if it succeeds unexpectedly).
    """
    print("Trying to transfer NFT without allowance...")
    client.set_operator(spender_account_id, spender_private_key)

    receipt = (
        TransferTransaction()
        .add_approved_nft_transfer(nft_id, spender_account_id, receiver_account_id)
        .execute(client)
    )
    
    # Reset operator immediately after execution attempt
    client.set_operator(AccountId.from_string(os.getenv("OPERATOR_ID")), PrivateKey.from_string(os.getenv("OPERATOR_KEY")))


    if receipt.status != ResponseCode.SPENDER_DOES_NOT_HAVE_ALLOWANCE:
        print(
            f"NFT transfer should have failed with SPENDER_DOES_NOT_HAVE_ALLOWANCE "
            f"status but got: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"NFT transfer successfully failed with {ResponseCode(receipt.status).name} status")


def nft_allowance():
    """
    Main execution function demonstrating NFT allowance functionality.

    Performs the following steps:
    1. Sets up the client and operator.
    2. Creates spender and receiver accounts.
    3. Creates an NFT token.
    4. Associates the token with the receiver account.
    5. Mints two NFTs.
    6. Approves spending allowance for the first NFT for the spender.
    7. Transfers the first NFT using the spender's key (SUCCESS).
    8. Deletes the allowance for the second NFT.
    9. Attempts to transfer the second NFT without an allowance (FAILURE verification).
    """
    client = setup_client()

    # Create spender and receiver accounts
    spender_account_id, spender_private_key = create_account(client)
    receiver_account_id, receiver_private_key = create_account(client)

    # Create NFT token
    token_id = create_nft_token(client)

    # Associate token with receiver account
    associate_token_with_account(client, receiver_account_id, receiver_private_key, token_id)

    metadata = [b"NFT Metadata 1", b"NFT Metadata 2"]
    nft_ids = mint_nft(client, token_id, metadata)
    nft_id = nft_ids[0]      
    nft_id_2 = nft_ids[1]    

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

    delete_nft_allowance(client, nft_id_2, client.operator_account_id, spender_account_id)
    
    transfer_nft_without_allowance(
        client, nft_id_2, spender_account_id, spender_private_key, receiver_account_id
    )


if __name__ == "__main__":
    nft_allowance()