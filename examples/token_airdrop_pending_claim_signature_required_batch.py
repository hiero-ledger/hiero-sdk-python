import os
import sys
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
    TokenClaimAirdropTransaction,
    TokenType,
    SupplyType,
    NftId,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
    TokenNftInfoQuery
)
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId

load_dotenv()

def setup_client():
    """Initialize Hedera client and operator"""
    client = Client(Network(os.getenv("NETWORK", "testnet")))
    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
    except Exception:
        print("❌ Invalid OPERATOR_ID or OPERATOR_KEY in .env")
        sys.exit(1)
    return client, operator_id, operator_key

def log_balances(client, operator_id, receiver_id, fungible_tokens, nft_ids):
    """Log balances of fungible tokens and ownership of NFTs after claim"""
    print("\nBalances after claim:")
    
    for token_id in fungible_tokens:
        sender_balance = CryptoGetAccountBalanceQuery(operator_id).execute(client).token_balances.get(token_id, 0)
        receiver_balance = CryptoGetAccountBalanceQuery(receiver_id).execute(client).token_balances.get(token_id, 0)
        print(f"Fungible token {token_id} -> Sender: {sender_balance}, Receiver: {receiver_balance}")
    
    for nft_id in nft_ids:
        nft_owner = TokenNftInfoQuery(nft_id).execute(client).account_id
        print(f"NFT {nft_id} now owned by {nft_owner}")

def create_receiver(client):
    """Create a receiver account that requires signature"""
    receiver_key = PrivateKey.generate()
    tx = AccountCreateTransaction() \
        .set_key(receiver_key.public_key()) \
        .set_initial_balance(Hbar(1)) \
        .set_receiver_signature_required(True) \
        .freeze_with(client) \
        .sign(receiver_key)
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        sys.exit(f"❌ Receiver account creation failed: {receipt.status}")
    receiver_id = receipt.account_id
    print(f"✅ Receiver account created: {receiver_id}")
    return receiver_id, receiver_key

def create_fungible_tokens(client, operator_id, operator_key, count=3):
    """Create fungible tokens"""
    tokens = []
    for i in range(count):
        tx = TokenCreateTransaction() \
            .set_token_name(f"FTK{i+1}") \
            .set_token_symbol(f"FT{i+1}") \
            .set_initial_supply(1000) \
            .set_token_type(TokenType.FUNGIBLE_COMMON) \
            .set_supply_type(SupplyType.FINITE) \
            .set_max_supply(1000) \
            .set_treasury_account_id(operator_id) \
            .freeze_with(client) \
            .sign(operator_key)
        receipt = tx.execute(client)
        tokens.append(receipt.token_id)
        print(f"✅ Fungible token created: {receipt.token_id}")
    return tokens

def create_and_mint_nfts(client, operator_id, operator_key, count=2):
    """Create NFTs and mint one NFT for each"""
    nft_ids = []
    for i in range(count):
        # Create NFT
        tx = TokenCreateTransaction() \
            .set_token_name(f"NFTK{i+1}") \
            .set_token_symbol(f"NFT{i+1}") \
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE) \
            .set_initial_supply(0) \
            .set_supply_type(SupplyType.FINITE) \
            .set_max_supply(100) \
            .set_treasury_account_id(operator_id) \
            .set_supply_key(operator_key) \
            .freeze_with(client) \
            .sign(operator_key)
        receipt = tx.execute(client)
        nft_token_id = receipt.token_id
        print(f"✅ NFT created: {nft_token_id}")

        # Mint NFT
        tx_mint = TokenMintTransaction(token_id=nft_token_id, metadata=[b"Batch NFT Metadata"]) \
            .freeze_with(client).sign(operator_key)
        receipt_mint = tx_mint.execute(client)
        serial = receipt_mint.serial_numbers[0]
        nft_id = NftId(nft_token_id, serial)
        nft_ids.append(nft_id)
        print(f"✅ NFT minted: serial {serial}")
    return nft_ids
def create_airdrops(client, operator_id, operator_key, receiver_id, fungible_tokens, nft_ids):
    tx = TokenAirdropTransaction()
    airdrops_summary = []

    # Fungible token transfers
    for token_id in fungible_tokens:
        amount = 100
        tx.add_token_transfer(token_id, operator_id, -amount)
        tx.add_token_transfer(token_id, receiver_id, amount)
        airdrops_summary.append(f"Fungible token {token_id}: {amount} tokens")

    # NFT transfers
    for nft_id in nft_ids:
        tx.add_nft_transfer(nft_id, operator_id, receiver_id)
        airdrops_summary.append(f"NFT {nft_id}: 1 NFT")

    # Freeze & sign with operator_key
    tx.freeze_with(client).sign(operator_key)
    receipt = tx.execute(client)
    print(f"✅ Pending airdrops created: {receipt.transaction_id}")
    print("Airdrops details:")
    for summary in airdrops_summary:
        print(f"  {summary}")

    # Prepare PendingAirdropId objects
    pending_airdrops = []
    for token_id in fungible_tokens:
        pending_airdrops.append(PendingAirdropId(operator_id, receiver_id, token_id, None))
    for nft_id in nft_ids:
        pending_airdrops.append(PendingAirdropId(operator_id, receiver_id, None, nft_id))

    print("\nPending airdrops to claim ({} total):".format(len(pending_airdrops)))
    for p in pending_airdrops:
        print(f"  {p}")

    return pending_airdrops

def claim_airdrops(client, receiver_key, pending_airdrops):
    """Receiver claims all pending airdrops"""
    tx_claim = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_airdrops)
    tx_claim.freeze_with(client).sign(receiver_key)
    receipt_claim = tx_claim.execute(client)
    if receipt_claim.status != ResponseCode.SUCCESS:
        sys.exit(f"❌ Batch airdrop claim failed: {receipt_claim.status}")
    print(f"✅ Batch airdrops claimed: {receipt_claim.transaction_id}")

def attempt_second_claim(client, receiver_key, pending_airdrops):
    """Attempt to claim the same airdrops again, should fail"""
    print("\nAttempting to claim the same airdrops again (should fail)...")
    tx_claim_again = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_airdrops)
    tx_claim_again.freeze_with(client).sign(receiver_key)
    receipt_claim_again = tx_claim_again.execute(client)
    if receipt_claim_again.status == ResponseCode.SUCCESS:
        print("❌ ERROR: Airdrops were claimed again, which should not happen!")
    else:
        print(f"✅ Second claim failed as expected: {receipt_claim_again.status}")

def main():
    # 1️⃣ Setup the Hedera client and operator account
    client, operator_id, operator_key = setup_client()

    # 2️⃣ Create a receiver account
    # This generates a new account on the Hedera network that will receive tokens/NFTs
    # The receiver's key pair is returned to allow signing transactions later
    receiver_id, receiver_key = create_receiver(client)

    # 3️⃣ Create fungible tokens (FTs)
    # This creates multiple fungible tokens under the operator's account
    # These are like "coins" that can be transferred between accounts
    fungible_tokens = create_fungible_tokens(client, operator_id, operator_key)

    # 4️⃣ Create and mint NFTs
    # Creates non-fungible tokens (NFTs) and mints one NFT for each token collection
    # NFTs are unique items (like collectibles) and have serial numbers
    nft_ids = create_and_mint_nfts(client, operator_id, operator_key)

    # 5️⃣ Create pending airdrops
    # Prepares transfers of FTs and NFTs from the operator to the receiver
    # The airdrops are "pending", meaning the receiver must claim them manually
    pending_airdrops = create_airdrops(client, operator_id, operator_key, receiver_id, fungible_tokens, nft_ids)

    # 6️⃣ Receiver claims all pending airdrops
    # This executes the pending airdrops, transferring the tokens and NFTs to the receiver
    claim_airdrops(client, receiver_key, pending_airdrops)
    log_balances(client, operator_id, receiver_id, fungible_tokens, nft_ids)

    # 7️⃣ Attempt to claim the same airdrops again
    # This demonstrates that once an airdrop is claimed, it cannot be claimed a second time
    attempt_second_claim(client, receiver_key, pending_airdrops)


if __name__ == "__main__":
    main()
