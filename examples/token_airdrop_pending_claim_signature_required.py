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
    TokenAirdropTransaction,
    TokenClaimAirdropTransaction,
    TokenMintTransaction,
    PendingAirdropId,
    TokenType,
    SupplyType,
    NftId,
    CryptoGetAccountBalanceQuery,
    TokenId,
    ResponseCode,
    Hbar,
    TokenNftInfoQuery
)

load_dotenv()


# ----------------------- Setup Client -----------------------
def setup_client():
    print("Connecting to Hedera testnet...")
    client = Client(Network(os.getenv("NETWORK", "testnet")))

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
        return client, operator_id, operator_key
    except Exception:
        print("❌ Invalid OPERATOR_ID or OPERATOR_KEY in .env")
        sys.exit(1)


# ----------------------- Create Receiver -----------------------
def create_receiver(client):
    print("\nCreating a receiver account...")
    receiver_key = PrivateKey.generate()
    tx = (
        AccountCreateTransaction()
        .set_key(receiver_key.public_key())
        .set_initial_balance(Hbar(1))
        .set_receiver_signature_required(True)
        .freeze_with(client)
        .sign(receiver_key)
    )
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Receiver account creation failed: {receipt.status}")
        sys.exit(1)
    receiver_id = receipt.account_id
    print(f"✅ Receiver account created: {receiver_id}")
    return receiver_id, receiver_key


# ----------------------- Create Fungible Token -----------------------
def create_fungible_token(client, operator_id, operator_key, name="FungibleToken", symbol="FTK", supply=1000):
    print(f"\nCreating fungible token {name}...")
    tx = (
        TokenCreateTransaction()
        .set_token_name(name)
        .set_token_symbol(symbol)
        .set_initial_supply(supply)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(supply)
        .set_treasury_account_id(operator_id)
        .freeze_with(client)
        .sign(operator_key)
    )
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Fungible token creation failed: {receipt.status}")
        sys.exit(1)
    token_id = receipt.token_id
    print(f"✅ Fungible token created: {token_id}")
    return token_id


# ----------------------- Create NFT -----------------------
def create_nft(client, operator_id, operator_key, name="NFTToken", symbol="NFTK"):
    print(f"\nCreating NFT {name}...")
    tx = (
        TokenCreateTransaction()
        .set_token_name(name)
        .set_token_symbol(symbol)
        .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
        .set_initial_supply(0)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .set_treasury_account_id(operator_id)
        .set_supply_key(operator_key)
        .freeze_with(client)
        .sign(operator_key)
    )
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ NFT creation failed: {receipt.status}")
        sys.exit(1)
    token_id = receipt.token_id
    print(f"✅ NFT created: {token_id}")
    return token_id


# ----------------------- Mint NFT -----------------------
def mint_nft(client, operator_key, nft_id, metadata=b"NFT Metadata"):
    print(f"\nMinting NFT {nft_id}...")
    tx = TokenMintTransaction(token_id=nft_id, metadata=[metadata]).freeze_with(client).sign(operator_key)
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ NFT mint failed: {receipt.status}")
        sys.exit(1)
    serial_number = receipt.serial_numbers[0]
    print(f"✅ NFT minted: serial {serial_number}")
    return serial_number


# ----------------------- Token Airdrop -----------------------
def create_airdrop(client, sender_id, sender_key, receiver_id, fungible_tokens, nft_list):
    print("\nCreating pending airdrops...")
    tx = TokenAirdropTransaction()
    # Add fungible token transfers
    for token_id, amount in fungible_tokens.items():
        print(f"  Scheduling fungible token airdrop: {amount} of {token_id}")
        tx.add_token_transfer(token_id, sender_id, -amount)
        tx.add_token_transfer(token_id, receiver_id, amount)
    # Add NFT transfers
    for nft in nft_list:
        print(f"  Scheduling NFT airdrop: {nft}")
        tx.add_nft_transfer(nft, sender_id, receiver_id)
    tx.freeze_with(client).sign(sender_key)
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Airdrop creation failed: {receipt.status}")
        sys.exit(1)
    print(f"✅ Pending airdrop created: {receipt.transaction_id}")
    return receipt


# ----------------------- Claim Airdrops -----------------------
def claim_airdrops(client, receiver_id, receiver_key, pending_airdrops):
    print("\nClaiming pending airdrops...")
    tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_airdrops).freeze_with(client).sign(receiver_key)
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Airdrop claim failed: {receipt.status}")
        sys.exit(1)
    print(f"✅ Airdrops claimed: {receipt.transaction_id}")


# ----------------------- Check Balances -----------------------
def log_fungible_balance(client, account_id, token_id, label=""):
    balances = CryptoGetAccountBalanceQuery(account_id=account_id).execute(client).token_balances
    balance = balances.get(token_id, 0)
    print(f"{label} Balance of {account_id} for token {token_id}: {balance}")
    return balance


def log_nft_owner(client, nft_id, label=""):
    nft_info = TokenNftInfoQuery(nft_id).execute(client)
    print(f"{label} NFT {nft_id} owned by {nft_info.account_id}")
    return nft_info.account_id


# ----------------------- Main Workflow -----------------------
def main():
    client, operator_id, operator_key = setup_client()

    # Create receiver account
    receiver_id, receiver_key = create_receiver(client)

    # Create tokens
    fungible_token_id = create_fungible_token(client, operator_id, operator_key, name="FTK1", symbol="FT1", supply=1000)
    nft_token_id = create_nft(client, operator_id, operator_key, name="NFTK1", symbol="NFT1")
    nft_serial = mint_nft(client, operator_key, nft_token_id)

    # Build NftId
    nft_id = NftId(nft_token_id, nft_serial)

    # Check balances before airdrop
    sender_balance_before = log_fungible_balance(client, operator_id, fungible_token_id, "Sender before airdrop")
    receiver_balance_before = log_fungible_balance(client, receiver_id, fungible_token_id, "Receiver before airdrop")
    nft_owner_before = log_nft_owner(client, nft_id, "NFT before airdrop")

    # Prepare pending airdrops
    pending_fungible = PendingAirdropId(operator_id, receiver_id, fungible_token_id, None)
    pending_nft = PendingAirdropId(operator_id, receiver_id, None, nft_id)

    pending_airdrops = [pending_fungible, pending_nft]

    print("\nPending airdrops to claim:")
    for p in pending_airdrops:
        print(f"  {p}")

    # Create airdrop on the network
    create_airdrop(client, operator_id, operator_key, receiver_id, {fungible_token_id: 100}, [nft_id])

    # Claim airdrops
    claim_airdrops(client, receiver_id, receiver_key, pending_airdrops)

    # Check balances after claim
    sender_balance_after = log_fungible_balance(client, operator_id, fungible_token_id, "Sender after airdrop")
    receiver_balance_after = log_fungible_balance(client, receiver_id, fungible_token_id, "Receiver after airdrop")
    nft_owner_after = log_nft_owner(client, nft_id, "NFT after airdrop")

    # Log transfer amounts
    print(f"\n✅ Fungible tokens transferred: {receiver_balance_after - receiver_balance_before}")
    print(f"✅ NFT ownership changed: {nft_owner_before} → {nft_owner_after}")


if __name__ == "__main__":
    main()
