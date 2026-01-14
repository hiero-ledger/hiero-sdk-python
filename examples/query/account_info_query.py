"""
uv run examples/query/account_info_query.py
python examples/query/account_info_query.py
"""

import sys

from hiero_sdk_python import (
    Client,
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


def setup_client():
    """Initialize client using environment configuration"""
    print("Connecting to Hedera network using environment configuration...")

    client = Client.from_env()

    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    if not operator_id or not operator_key:
        raise ValueError(
            "OPERATOR_ID and OPERATOR_KEY must be set in the environment"
        )

    print(f"Client set up with operator id {operator_id}")
    return client, operator_id, operator_key


def create_test_account(client, operator_key):
    """Create a new test account for demonstration"""
    new_account_private_key = PrivateKey.generate_ed25519()
    new_account_public_key = new_account_private_key.public_key()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(new_account_public_key)
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
        .sign(account_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"NFT creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

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
        .sign(account_private_key)
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
        f"\nToken Relationships ({len(info.token_relationships)} total) "
        f"for account {info.account_id}:"
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
    Demonstrates the account info query functionality
    """
    client, operator_id, operator_key = setup_client()

    account_id, account_private_key = create_test_account(client, operator_key)

    info = AccountInfoQuery(account_id).execute(client)
    print("\nAccount info query completed successfully!")
    display_account_info(info)

    token_id = create_fungible_token(client, operator_id, operator_key)

    associate_token_with_account(client, token_id, account_id, account_private_key)

    info = AccountInfoQuery(account_id).execute(client)
    display_token_relationships(info)

    grant_kyc_for_token(client, account_id, token_id)

    info = AccountInfoQuery(account_id).execute(client)
    display_token_relationships(info)

    nft_token_id = create_nft(client, account_id, account_private_key)
    mint_nft(client, nft_token_id, account_private_key)

    info = AccountInfoQuery(account_id).execute(client)
    display_account_info(info)
    display_token_relationships(info)


if __name__ == "__main__":
    query_account_info()
