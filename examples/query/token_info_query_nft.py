import sys

from hiero_sdk_python import (
    Client,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenType,
    SupplyType,
    TokenNftInfoQuery,
    ResponseCode,
)


def setup_client():
    """Initialize and set up the client with operator account using env vars."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client, client.operator_account_id, client.operator_private_key


def create_nft(client, operator_id, operator_key):
    """Create an NFT token"""
    print("Creating NFT token...")
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleNFT")
        .set_token_symbol("EXNFT")
        .set_decimals(0)
        .set_initial_supply(0)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_freeze_key(operator_key)
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"NFT token created with ID: {token_id}")
    return token_id


def mint_nft(client, nft_token_id, operator_key):
    """Mint an NFT"""
    print("Minting NFT...")
    receipt = (
        TokenMintTransaction()
        .set_token_id(nft_token_id)
        .set_metadata(b"My NFT Metadata 1")
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Minting failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print("NFT minted successfully")
    return receipt.serial_numbers[0]


def query_nft_info():
    client, operator_id, operator_key = setup_client()

    token_id = create_nft(client, operator_id, operator_key)
    serial_number = mint_nft(client, token_id, operator_key)

    nft_id = token_id.nft(serial_number)

    print("Querying NFT info...")
    nft_info = TokenNftInfoQuery().set_nft_id(nft_id).execute(client)

    print(f"NFT ID: {nft_info[0].nft_id}")
    print(f"Account ID: {nft_info[0].account_id}")
    print(f"Metadata: {nft_info[0].metadata}")


if __name__ == "__main__":
    query_nft_info()