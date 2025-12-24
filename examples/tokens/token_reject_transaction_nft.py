"""
uv run examples/tokens/token_reject_transaction_nft.py
python examples/tokens/token_reject_transaction_nft.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import (
    TokenAssociateTransaction,
)
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client


def create_test_account(client):
    """Create a new account for testing"""
    # Generate private key for new account
    new_account_private_key = PrivateKey.generate_ed25519()
    new_account_public_key = new_account_private_key.public_key()

    # Create new account with initial balance of 1 HBAR
    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(new_account_public_key)
        .set_initial_balance(Hbar(1))
        .execute(client)
    )

    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    # Get account ID from receipt
    account_id = receipt.account_id
    print(f"New account created with ID: {account_id}")

    return account_id, new_account_private_key


def create_nft(client, treasury_id, treasury_private_key):
    """Create a non-fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(treasury_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(treasury_private_key)
        .set_supply_key(treasury_private_key)
        .set_freeze_key(treasury_private_key)
        .freeze_with(client)
        .sign(
            treasury_private_key
        )  # Has to be signed here by treasury's key as we set the treasury_account_id to be the treasury_id
        .execute(client)
    )

    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    # Get token ID from receipt
    nft_token_id = receipt.token_id
    print(f"NFT created with ID: {nft_token_id}")

    return nft_token_id


def mint_nfts(client, nft_token_id, metadata_list, treasury_private_key):
    """Mint a non-fungible token"""
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(metadata_list)
        .freeze_with(client)
        .sign(
            treasury_private_key
        )  # Has to be signed here by treasury's key because they own the supply key
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"NFT minted with serial numbers: {receipt.serial_numbers}")

    return [
        NftId(nft_token_id, serial_number) for serial_number in receipt.serial_numbers
    ]


def associate_token(client, receiver_id, nft_token_id, receiver_private_key):
    """Associate token with an account"""
    # Associate the token_id with the new account
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(receiver_id)
        .add_token_id(nft_token_id)
        .freeze_with(client)
        .sign(receiver_private_key)  # Has to be signed here by receiver's key
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Token successfully associated with account: {receiver_id}")


def transfer_nfts(client, treasury_id, treasury_private_key, receiver_id, nft_ids):
    """Transfer NFTs to the receiver account so we can later reject them"""
    # Transfer NFTs to the receiver account
    receipt = (
        TransferTransaction()
        .add_nft_transfer(nft_ids[0], treasury_id, receiver_id)
        .add_nft_transfer(nft_ids[1], treasury_id, receiver_id)
        .freeze_with(client)
        .sign(treasury_private_key)
        .execute(client)
    )

    # Check if transfer was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Successfully transferred NFTs to receiver account {receiver_id}")


def get_nft_balances(client, treasury_id, receiver_id, nft_token_id):
    """Get NFT balances for both accounts"""
    token_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(treasury_id).execute(client)
    )
    print(
        f"NFT balance of treasury {treasury_id}: {token_balance.token_balances[nft_token_id]}"
    )

    receiver_token_balance = (
        CryptoGetAccountBalanceQuery().set_account_id(receiver_id).execute(client)
    )
    print(
        f"NFT balance of receiver {receiver_id}: {receiver_token_balance.token_balances[nft_token_id]}"
    )


def token_reject_nft():
    """
    Demonstrates the NFT token reject functionality by:
    1. Creating a new treasury account
    2. Creating a new receiver account
    3. Creating a non-fungible token
    4. Minting two NFTs
    5. Associating the NFT with the receiver account
    6. Transferring the NFTs to the receiver account
    7. Rejecting the NFTs from the receiver account
    """
    client = setup_client()
    # Create treasury/sender account that will create and send tokens
    treasury_id, treasury_private_key = create_test_account(client)
    # Create receiver account that will receive and later reject tokens
    receiver_id, receiver_private_key = create_test_account(client)

    # Create a new NFT collection with the treasury account as owner
    nft_token_id = create_nft(client, treasury_id, treasury_private_key)
    # Mint 2 NFTs in the collection with example metadata and get their unique IDs that we will send and reject
    nft_ids = mint_nfts(
        client,
        nft_token_id,
        [b"ExampleMetadata 1", b"ExampleMetadata 2"],
        treasury_private_key,
    )

    # Associate the NFT token with the receiver account so they can receive the NFTs
    associate_token(client, receiver_id, nft_token_id, receiver_private_key)

    # Transfer NFTs to the receiver account
    transfer_nfts(client, treasury_id, treasury_private_key, receiver_id, nft_ids)

    # Get and print NFT balances before rejection to show the initial state
    print("\nNFT balances before rejection:")
    get_nft_balances(client, treasury_id, receiver_id, nft_token_id)

    # Receiver rejects the NFTs that were previously transferred to them
    receipt = (
        TokenRejectTransaction()
        .set_owner_id(receiver_id)
        .set_nft_ids([nft_ids[0], nft_ids[1]])
        .freeze_with(client)
        .sign(receiver_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT rejection failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(
        f"Successfully rejected NFTs {nft_ids[0]} and {nft_ids[1]} from account {receiver_id}"
    )

    # Get and print NFT balances after rejection to show the final state
    print("\nNFT balances after rejection:")
    get_nft_balances(client, treasury_id, receiver_id, nft_token_id)


if __name__ == "__main__":
    token_reject_nft()
