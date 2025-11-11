"""
Hedera Token Airdrop Example Script

This script demonstrates and end-to-end example for an account to automatically (no user action required) claim a set of airdrops.

Unique configurations of this account:
- 10 auto-association slots.
- Does not require a signature to claim the airdrop.
The Hedera network will auto-associate the token and claim it on airdrop.

This script demonstrates:
- Setting up a Hedera client
- Creating fungible and NFT tokens
- Creating a receiver account with unique configurations
- Performing token airdrops to the receiver
- Checking balances for verification purposes.

Run this script using:
uv run examples/tokens/token_airdrop_claim_auto.py
python examples/tokens/token_airdrop_claim_auto.py
"""
import os
import sys
from typing import Iterable
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    Network,
    AccountId,
    PrivateKey,
    AccountCreateTransaction,
    TokenCreateTransaction,
    TokenMintTransaction,
    TokenAirdropTransaction,
    TokenType,
    SupplyType,
    NftId,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
    TokenId,
    TokenNftInfoQuery
)

load_dotenv()

def setup_client():
    network_name = os.getenv("NETWORK", "testnet")

    # Validate environment variables
    if not os.getenv("OPERATOR_ID") or not os.getenv("OPERATOR_KEY"):
        print("❌ Missing OPERATOR_ID or OPERATOR_KEY in .env file.")
        sys.exit(1)

    try:
        network = Network(network_name)
        print(f"Connecting to Hedera {network_name} network!")
        client = Client(network)

        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ''))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ''))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

    except Exception as e:
        raise ConnectionError(f"Error initializing client: {e}")

    print(f"✅ Connected to Hedera {network_name} network as operator: {operator_id}")
    return client, operator_id, operator_key

def create_receiver(
        client: Client,
        signature_required: bool =False,
        max_auto_assoc: int =10
    ):
    receiver_key = PrivateKey.generate()
    receiver_public_key = receiver_key.public_key()

    try:
        receipt = (
            AccountCreateTransaction()
            .set_key(receiver_public_key)
            .set_initial_balance(Hbar(1))
            .set_receiver_signature_required(signature_required)
            .set_max_automatic_token_associations(max_auto_assoc)
            .freeze_with(client)
            .sign(receiver_key)
            .execute(client)
        )
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"❌ Receiver account creation failed: {status_message}")

        receiver_id = receipt.account_id
        print(
            f"✅ Receiver account {receiver_id} created "
            f"(auto-assoc={max_auto_assoc}, sig_required={signature_required})"
        )
        return receiver_id, receiver_key
    except Exception as e:
        raise RuntimeError(f"❌ Error creating receiver account: {e}") from e


def create_fungible_token(
        client: Client,
        operator_id: AccountId,
        operator_key: PrivateKey,
        name: str ="My Fungible Token",
        symbol: str ="MFT",
        initial_supply: int =50,
        max_supply: int = 1000,
    ):
    try:
        receipt = ( 
            TokenCreateTransaction()
            .set_token_name(name)
            .set_token_symbol(symbol)
            .set_initial_supply(initial_supply)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(max_supply)
            .set_treasury_account_id(operator_id)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        token_id = receipt.token_id
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"❌ Fungible token creation failed: {status_message}")

        print(f"✅ Fungible token created: {token_id}")
        return token_id
    except Exception as e:
        raise RuntimeError(f"❌ Error creating fungible token: {e}") from e


def create_nft_token(
        client: Client,
        operator_id: AccountId,
        operator_key: PrivateKey,
        name: str ="My NFT Token",
        symbol: str ="MNT",
        max_supply: int = 100
    ):
    try:
        receipt = ( 
            TokenCreateTransaction()
            .set_token_name(name)
            .set_token_symbol(symbol)
            .set_initial_supply(0)
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(max_supply)
            .set_treasury_account_id(operator_id)
            .set_supply_key(operator_key)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        token_id = receipt.token_id
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"❌ NFT token creation failed: {status_message}")

        print(f"✅ NFT token created: {token_id}")
        return token_id
    except Exception as e:
        raise RuntimeError(f"❌ Error creating NFT token: {e}") from e


def mint_nft_token(
        client: Client,
        operator_key: PrivateKey,
        nft_token_id: TokenId,
    ):
    try:
        receipt = ( 
            TokenMintTransaction()
            .set_token_id(nft_token_id)
            .set_metadata([b"NFT Metadata Example"])
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        total_supply = receipt._receipt_proto.newTotalSupply
        serial = receipt.serial_numbers[0]
        nft_id = NftId(nft_token_id, serial)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"❌ NFT token mint failed: {status_message}")

        print(f"✅ NFT {nft_token_id} serial {serial} minted with NFT id of {nft_id}. Total NFT supply is {total_supply} ")
        return nft_id
    except Exception as e:
        raise RuntimeError(f"❌ Error minting NFT token: {e}") from e
def log_balances(
    client: Client,
    operator_id: AccountId,
    receiver_id: AccountId,
    fungible_ids: Iterable[TokenId],
    nft_ids: Iterable[NftId],
    prefix: str = ""
):
    print(f"\n===== {prefix} Balances =====")

    try:
        operator_balance = CryptoGetAccountBalanceQuery().set_account_id(operator_id).execute(client)
        receiver_balance = CryptoGetAccountBalanceQuery().set_account_id(receiver_id).execute(client)
    except Exception as e:
        print(f"❌ Failed to fetch balances: {e}")
        return

    def log_fungible(account_id: AccountId, balances: dict, token_ids: Iterable[TokenId]):
        print("  Fungible tokens:")
        for token_id in token_ids:
            print(f"    {token_id}: {balances.get(token_id, 0)}")

    def log_nfts(account_id: AccountId, nft_ids: Iterable[NftId]):
        print("  NFTs:")
        owned = []
        for nft_id in nft_ids:
            try:
                info = TokenNftInfoQuery().set_nft_id(nft_id).execute(client)
                if info.account_id == account_id:
                    owned.append(str(nft_id))
            except Exception as e:
                print(f"    ⚠️ Error fetching NFT {nft_id}: {e}")
        if owned:
            for nft in owned:
                print(f"    {nft}")
        else:
            print("    (none)")

    print(f"\nSender ({operator_id}):")
    log_fungible(operator_id, dict(operator_balance.token_balances), fungible_ids)
    log_nfts(operator_id, nft_ids)

    print(f"\nReceiver ({receiver_id}):")
    log_fungible(receiver_id, dict(receiver_balance.token_balances), fungible_ids)
    log_nfts(receiver_id, nft_ids)

    print("=============================================\n")

def perform_airdrop(
        client: Client,
        operator_id: AccountId,
        operator_key: PrivateKey,
        receiver_id: AccountId,
        fungible_ids: Iterable[TokenId],
        nft_ids: Iterable[NftId],
        ft_amount: int = 100
    ):

    try:
        tx = TokenAirdropTransaction()

        for fungible_id in fungible_ids:
            tx.add_token_transfer(fungible_id, operator_id, -ft_amount)
            tx.add_token_transfer(fungible_id, receiver_id, ft_amount)
            print(f"📤 Transferring {ft_amount} of fungible token {fungible_id} from {operator_id} → {receiver_id}")

        for nft_id in nft_ids:
            tx.add_nft_transfer(nft_id, operator_id, receiver_id)
            print(f"🎨 Transferring NFT {nft_id} from {operator_id} → {receiver_id}")

        print("\n⏳ Submitting airdrop transaction...")
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"Airdrop transaction failed with status: {status_message}")

        print(f"✅ Airdrop executed successfully! Transaction ID: {receipt.transaction_id}")

    except Exception as e:
        print(f"❌ Airdrop failed: {e}")
        raise RuntimeError("Airdrop execution failed") from e

def main():
    # Set up client and return client, operator_id, operator_key
    client, operator_id, operator_key = setup_client()

    # Create and return a fungible token to airdrop 
    print("Create 50 fungible tokens and 1 NFT to airdrop")
    fungible_id = create_fungible_token(client, operator_id, operator_key, name="My Fungible Token", symbol="123", initial_supply=50, max_supply = 2000)

    # Create and return an nft token to airdrop 
    nft_token_id = create_nft_token(client, operator_id, operator_key, name="My NFT Token", symbol = "MNFT", max_supply=1000)

    # Mint and return an nft to airdrop
    nft_serial = mint_nft_token(client, operator_key, nft_token_id)

    # Create a receiver that will test no signature is required to claim the auto-airdrop
        # Ensure false for signature required
        # Assume 10 max association slots
    # Return the receiver id and receiver private key
    print("Creating the account that will automatically receive the airdropped tokens")
    receiver_id, receiver_key = create_receiver(client, False, 10)

    # Check pre-airdrop balances
    print("\n🔍 Verifying sender has tokens to airdrop and receiver neither:")
    log_balances(client, operator_id, receiver_id, [fungible_id], [nft_serial], prefix="Before airdrop")

    # Initiate airdrop of 20 fungible tokens and 1 nft token id
    perform_airdrop(client, operator_id, operator_key, receiver_id, [fungible_id], [nft_serial], 20)

    print("\n🔍 Verifying receiver has received airdrop contents automatically and sender has sent:")
    log_balances(client, operator_id, receiver_id, [fungible_id], [nft_serial], prefix="After airdrop")

    print("✅ Auto-association successful: Receiver accepted airdropped tokens without pre-association.")
    print("✅ Airdrop successful: Receiver accepted new fungible tokens without pre-association.")

if __name__ == "__main__":
    main()
