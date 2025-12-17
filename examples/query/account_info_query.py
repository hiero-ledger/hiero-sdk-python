"""
uv run examples/query/account_info_query.py
python examples/query/account_info_query.py

"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    ResponseCode,
    Hbar,
)
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_associate_transaction import (
    TokenAssociateTransaction,
)
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.nft_id import NftId

load_dotenv()

network_name = os.getenv("NETWORK", "testnet").lower()


def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to the Hedera {network} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
    operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client, operator_id, operator_key


def create_test_account(client, operator_key):
    """Create a new test account for demonstration"""
    new_account_private_key = PrivateKey.generate_ed25519()
    new_account_public_key = new_account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(Hbar(1))
        .set_account_memo("Test account memo")
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    new_account_id = receipt.account_id
    print(f"\nTest account created with ID: {new_account_id}")

    return new_account_id, new_account_private_key


def create_fungible_token(client, operator_id, operator_key):
    """Create a fungible token for association with test account"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("FungibleToken")
        .set_token_symbol("FTT")
        .set_decimals(2)
        .set_initial_supply(1000)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(10000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_kyc_key(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"\nFungible token created with ID: {token_id}")

    return token_id


def create_nft(client, account_id, account_private_key):
    """Create a non-fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(account_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(account_private_key)
        .set_supply_key(account_private_key)
        .set_freeze_key(account_private_key)
        .freeze_with(client)
        .sign(account_private_key)  # Sign with the account private key
        .execute(client)
    )

    # Check if nft creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    # Get token ID from receipt
    nft_token_id = receipt.token_id
    print(f"\nNFT created with ID: {nft_token_id}")

    return nft_token_id


def mint_nft(client, nft_token_id, account_private_key):
    """Mint a non-fungible token"""
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(b"My NFT Metadata 1")
        .freeze_with(client)
        .sign(account_private_key)  # Sign with the account private key
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT minting failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"\nNFT minted with serial number: {receipt.serial_numbers[0]}")

    return NftId(nft_token_id, receipt.serial_numbers[0])


def associate_token_with_account(client, token_id, account_id, account_key):
    """Associate the token with the test account"""
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
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Token {token_id} associated with account {account_id}")


def grant_kyc_for_token(client, account_id, token_id):
    """Grant KYC for the token to the account"""
    receipt = (
        TokenGrantKycTransaction()
        .set_account_id(account_id)
        .set_token_id(token_id)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"KYC grant failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"\nKYC granted for token_id: {token_id}")


def display_account_info(info):
    """Display basic account information"""
    print(f"\nAccount ID: {info.account_id}")
    print(f"Contract Account ID: {info.contract_account_id}")
    print(f"Account Balance: {info.balance}")
    print(f"Account Memo: '{info.account_memo}'")
    print(f"Is Deleted: {info.is_deleted}")
    print(f"Receiver Signature Required: {info.receiver_signature_required}")
    print(f"Owned NFTs: {info.owned_nfts}")

    print(f"Public Key: {info.key.to_string()}")

    print(f"Expiration Time: {info.expiration_time}")
    print(f"Auto Renew Period: {info.auto_renew_period}")

    print(f"Proxy Received: {info.proxy_received}")


def display_token_relationships(info):
    """Display token relationships information"""
    print(
        f"\nToken Relationships ({len(info.token_relationships)} total) for account {info.account_id}:"
    )
    if info.token_relationships:
        for i, relationship in enumerate(info.token_relationships, 1):
            print(f"  Token {i}:")
            print(f"    Token ID: {relationship.token_id}")
            print(f"    Symbol: {relationship.symbol}")
            print(f"    Balance: {relationship.balance}")
            print(f"    Decimals: {relationship.decimals}")
            print(f"    Freeze Status: {relationship.freeze_status}")
            print(f"    KYC Status: {relationship.kyc_status}")
            print(f"    Automatic Association: {relationship.automatic_association}")
    else:
        print("    No token relationships found")


def query_account_info():
    """
    Demonstrates the account info query functionality by:
    1. Setting up client with operator account
    2. Creating a new account
    3. Querying account info and displaying account information
    4. Creating a fungible token and associating it with the new account
    5. Querying account info to see token relationships
    6. Granting KYC to the new account for the token
    7. Querying account info again to see updated KYC status
    8. Creating an NFT token with the new account as treasury and minting one NFT
    9. Querying final account info to see complete token relationships and NFT ownership
    """
    client, operator_id, operator_key = setup_client()

    # Create a new account
    account_id, account_private_key = create_test_account(client, operator_key)

    # Query the account info and display account information
    info = AccountInfoQuery(account_id).execute(client)
    print("\nAccount info query completed successfully!")
    display_account_info(info)

    # Create a fungible token
    token_id = create_fungible_token(client, operator_id, operator_key)

    # Associate the token with the account
    associate_token_with_account(client, token_id, account_id, account_private_key)

    # Query the account info and display token relationships
    info = AccountInfoQuery(account_id).execute(client)
    print("\nToken info query completed successfully!")
    display_token_relationships(info)

    # Grant KYC for the token
    print(f"\nGrant KYC for token: {token_id}")
    grant_kyc_for_token(client, account_id, token_id)

    # Query the account info again and see the kyc status has been updated to GRANTED
    info = AccountInfoQuery(account_id).execute(client)
    print("\nAccount info query completed successfully!")
    display_token_relationships(info)

    # Create an NFT token with the new account as the owner
    nft_token_id = create_nft(client, account_id, account_private_key)

    # Mint an NFT to the account
    mint_nft(client, nft_token_id, account_private_key)

    # Query the account info again and see that the account has 1 owned NFT
    # and the token relationship has been updated to include the NFT
    # NOTE: the newest token is the first in the list
    info = AccountInfoQuery(account_id).execute(client)
    display_account_info(info)
    display_token_relationships(info)


if __name__ == "__main__":
    query_account_info()
