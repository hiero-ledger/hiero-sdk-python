"""
Hedera Token Airdrop Example Script

This script demonstrates and end-to-end example for an account to claim a set of airdrops.

Unique configurations of this account:
- 0 auto-association slots.
- Has no tokens associated before the claiming of the airdrop.
- Requires a signature to claim the airdrop.
Token airdrop claim will work despite no associations as the Hedera network will complete that step.

This script demonstrates:
- Setting up a Hedera client
- Creating fungible and NFT tokens
- Creating a receiver account with signature required and 0 auto-association slots
- Performing token airdrops to the receiver
- Fetching and claiming pending airdrops
- Checking balances and token association statuses for verification purposes.

Run this script using:
uv run examples/tokens/token_airdrop_claim_signature_required.py
python examples/tokens/token_airdrop_claim_signature_required.py
"""

# pylint: disable=import-error,
# pylint: disable=too-many-arguments,
# pylint: disable=protected-access,
# pylint: disable=broad-except
import os
import sys
from typing import Iterable, List, Dict
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
    TokenNftInfoQuery,
    TokenClaimAirdropTransaction,
    PendingAirdropId,
    TransactionRecordQuery,
    TransactionRecord,
    TransactionId
)

load_dotenv()

def setup_client():
    """
    Sets up the Hedera client using environment variables.
    """
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

    except Exception as exc:
        raise ConnectionError(f'Error initializing client: {exc}') from exc

    print(f"✅ Connected to Hedera {network_name} network as operator: {operator_id}")
    return client, operator_id, operator_key

def create_receiver(
        client: Client,
        signature_required: bool =True,
        max_auto_assoc: int = 0
    ):
    """
    Creates a receiver account with specific configurations.
    """
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
    except Exception as exc:
        raise RuntimeError(f"❌ Error creating receiver account: {exc}") from exc

def create_fungible_token(
        client: Client,
        operator_id: AccountId,
        operator_key: PrivateKey,
        name: str ="My Fungible Token",
        symbol: str ="MFT",
        initial_supply: int =50,
        max_supply: int = 1000,
    ):
    """
    Creates a fungible token.
    """
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
    except Exception as exc:
        raise RuntimeError(f"❌ Error creating fungible token: {exc}") from exc

def create_nft_token(
        client: Client,
        operator_id: AccountId,
        operator_key: PrivateKey,
        name: str ="My NFT Token",
        symbol: str ="MNT",
        max_supply: int = 100
    ):
    """
    Creates an NFT token.
    """
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
    except Exception as exc:
        raise RuntimeError(f"❌ Error creating NFT token: {exc}") from exc

def mint_nft_token(
        client: Client,
        operator_key: PrivateKey,
        nft_token_id: TokenId,
    ):
    """
    Mints an NFT token.
    """
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

        print(f"✅ NFT {nft_token_id} serial {serial} minted with NFT id of {nft_id}.")
        print(f"   Total NFT supply is {total_supply}")
        return nft_id
    except Exception as exc:
        raise RuntimeError(f"❌ Error minting NFT token: {exc}") from exc

def get_token_association_status(
        client: Client,
        receiver_id: AccountId,
        token_ids: List[TokenId]
    ) -> Dict[TokenId, bool]:
    """
    Checks if the receiver account is associated with the given tokens.
    """
    try:
        # Query the receiver's balance, which includes token associations
        balance = CryptoGetAccountBalanceQuery()\
                    .set_account_id(receiver_id)\
                    .execute(client)

        associated_tokens = set(balance.token_balances.keys())
        association_status = {token_id: token_id in associated_tokens for token_id in token_ids}

        print(f"✅ Association status for account {receiver_id}:")
        for tid, associated in association_status.items():
            print(f"  Token {tid}: {'Associated' if associated else 'Not Associated'}")

        return association_status

    except Exception as exc:
        print(f"❌ Failed to fetch token associations for account {receiver_id}: {exc}")
        return {token_id: False for token_id in token_ids}
def log_fungible_balances(balances: dict, token_ids: Iterable[TokenId]):
    """
    Logs the balances of fungible tokens.
    """
    print("  Fungible tokens:")
    for token_id in token_ids:
        amount = balances.get(token_id, 0)
        print(f"    {token_id}: {amount}")



def log_nft_balances(client: Client, account_id: AccountId, nft_ids: Iterable[NftId]):
    """
    Logs the ownership of NFTs.
    """
    print("  NFTs:")
    owned_nfts = []
    for nft_id in nft_ids:
        try:
            info = TokenNftInfoQuery().set_nft_id(nft_id).execute(client)
            if info.account_id == account_id:
                owned_nfts.append(str(nft_id))
        except Exception as exc:
            print(f"    ⚠️ Error fetching NFT {nft_id}: {exc}")

    if owned_nfts:
        for nft in owned_nfts:
            print(f"    {nft}")
    else:
        print("    (none)")


def log_balances(
    client: Client,
    operator_id: AccountId,
    receiver_id: AccountId,
    fungible_ids: Iterable[TokenId],
    nft_ids: Iterable[NftId],
    prefix: str = ""
):
    """
    Logs the balances of both the operator and receiver accounts.
    """
    print(f"\n===== {prefix} Balances =====")

    try:
        operator_balance = CryptoGetAccountBalanceQuery().set_account_id(
            operator_id).execute(client)
        receiver_balance = CryptoGetAccountBalanceQuery().set_account_id(
            receiver_id).execute(client)
    except Exception as exc:
        print(f"❌ Failed to fetch balances: {exc}")
        return

    operator_balances = dict(operator_balance.token_balances)
    receiver_balances = dict(receiver_balance.token_balances)

    # ------------------------------
    # SENDER BALANCES
    # ------------------------------
    print(f"\nSender ({operator_id}):")
    log_fungible_balances(operator_balances, fungible_ids)
    log_nft_balances(client, operator_id, nft_ids)

    # ------------------------------
    # RECEIVER BALANCES
    # ------------------------------
    print(f"\nReceiver ({receiver_id}):")
    log_fungible_balances(receiver_balances, fungible_ids)
    log_nft_balances(client, receiver_id, nft_ids)

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
    """
    Performs an airdrop of fungible and NFT tokens.
    """

    try:
        transaction = TokenAirdropTransaction()

        for fungible_id in fungible_ids:
            transaction.add_token_transfer(fungible_id, operator_id, -ft_amount)
            transaction.add_token_transfer(fungible_id, receiver_id, ft_amount)
            print(f"📤 Transferring {ft_amount} of fungible token {fungible_id}")
            print(f"   from {operator_id} → {receiver_id}")

        for nft_id in nft_ids:
            transaction.add_nft_transfer(nft_id, operator_id, receiver_id)
            print(f"🎨 Transferring NFT {nft_id} from {operator_id} → {receiver_id}")

        print("\n⏳ Submitting airdrop transaction...")
        receipt = transaction.freeze_with(client).sign(operator_key).execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"Airdrop transaction failed with status: {status_message}")

        transaction_id = receipt.transaction_id
        print(f"✅ Airdrop executed successfully! Transaction ID: {transaction_id}")

        return transaction_id
    except Exception as exc:
        print(f"❌ Airdrop failed: {exc}")
        raise RuntimeError("Airdrop execution failed") from exc

def fetch_pending_airdrops(
        client: Client,
        transaction_id: TransactionId
    ) -> List[PendingAirdropId]:
    """
    Retrieve all pending airdrop IDs generated by a specific transaction.

    Executes a `TransactionRecordQuery` to inspect the transaction record and
    extract any newly created `PendingAirdropId` objects from the
    `new_pending_airdrops` field.
    """
    try:
        record: TransactionRecord = TransactionRecordQuery(transaction_id).execute(client)
        pending_airdrops = record.new_pending_airdrops  # List of PendingAirdropRecord

        pending_airdrop_ids = [p.pending_airdrop_id for p in pending_airdrops]

        print(f"✅ Found {len(pending_airdrop_ids)} pending airdrops")
        for pid in pending_airdrop_ids:
            print(" →", pid)

        return pending_airdrop_ids

    except Exception as exc:
        print(f"❌ Failed to fetch pending airdrops for transaction {transaction_id}: {exc}")
        return []

def claim_airdrop(
        client: Client,
        receiver_key: PrivateKey,
        pending_airdrops: List[PendingAirdropId]
    ):
    """
    Claims one or more pending airdrops on behalf of the receiver.

    This function builds and executes a TokenClaimAirdropTransaction, which
    must be signed by the receiver. It uses `get_pending_airdrop_ids()` to
    safely retrieve and display the list of pending airdrop IDs before execution
    """
    try:
        transaction = (
            TokenClaimAirdropTransaction()
            .add_pending_airdrop_ids(pending_airdrops)
            .freeze_with(client)
            .sign(receiver_key) # Signing with receiver is required
        )
        print(f"{transaction}")

        receipt = transaction.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode(receipt.status).name
            raise RuntimeError(f"❌ Airdrop claim failed: {status_message}")

        print("✅ airdrop claimed")
        return receipt
    except Exception as exc:
        raise RuntimeError(f"❌ Error claiming airdrop: {exc}") from exc

def main():
    """
    Main function to execute the airdrop claim example.
    """
    # Set up client and return client, operator_id, operator_key
    client, operator_id, operator_key = setup_client()

    # Create and return a fungible token to airdrop
    print("Create 50 fungible tokens and 1 NFT to airdrop")
    fungible_id = create_fungible_token(
        client,
        operator_id,
        operator_key,
        name="My Fungible Token",
        symbol="123",
        initial_supply=50,
        max_supply = 2000
    )

    # Create and return an nft token to airdrop
    nft_token_id = create_nft_token(
        client,
        operator_id,
        operator_key,
        name="My NFT Token",
        symbol = "MNFT",
        max_supply=1000
    )

    # Mint and return an nft to airdrop
    nft_serial = mint_nft_token(
        client,
        operator_key,
        nft_token_id
    )

    # Create a receiver that will require signature to claim the airdrop
        # Ensure true for signature required (for the receiver)
        # 0 max association slots
    # Return the receiver id and receiver private key
    print("Creating the account that will receive the airdropped tokens on signing")
    receiver_id, receiver_key = create_receiver(
        client,
        True,
        0
    )

    # Verify this receiver does NOT have any of the fungible or NFT tokens associated
    # Claim airdrop will work regardless
    token_ids_to_check = [fungible_id, nft_token_id]
    association_status = get_token_association_status(
        client,
        receiver_id,
        token_ids_to_check
    )
    print(association_status)

    # Check pre-airdrop balances
    print("\n🔍 Verifying sender has tokens to airdrop and receiver neither:")
    log_balances(
        client,
        operator_id,
        receiver_id,
        [fungible_id],
        [nft_serial],
        prefix="Before airdrop"
    )

    # Initiate airdrop of 20 fungible tokens and 1 nft token id
    transaction_id = perform_airdrop(
        client,
        operator_id,
        operator_key,
        receiver_id,
        [fungible_id],
        [nft_serial],
        20
    )

    print("\n🔍 Verifying no balance change as airdrop is not yet claimed:")
    log_balances(client,operator_id,receiver_id,[fungible_id],[nft_serial],prefix="After airdrop")

    # Get a list of pending airdrops
    pending_airdrop_ids = fetch_pending_airdrops(client, transaction_id)
    print(pending_airdrop_ids)

    # Claim this list of pending airdrops
    # Note that we are signing with the receiver key which is required as was set to True
    # Claiming will work even without association and available auto-association slots
    # This is because the signing itself causes the Hedera network to associate the tokens.
    print("Claiming airdrop:")
    claim_airdrop(
        client, receiver_key, pending_airdrop_ids
    )  # Pass the receiver key which is needed to sign

    # Check airdrop has resulted in transfers
    print("\n🔍 Verifying balances have now changed after claim:")
    log_balances(client,operator_id,receiver_id,[fungible_id],[nft_serial],prefix="After claim")

    # Check Hedera network has associated these tokens behind the scenes
    token_ids_to_check = [fungible_id, nft_token_id]
    association_status = get_token_association_status(client,receiver_id,token_ids_to_check)
    print(association_status)

if __name__ == "__main__":
    main()
