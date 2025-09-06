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
    TokenType,
    SupplyType,
    NftId,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    Hbar,
)
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery

load_dotenv()

# ----------------------- Setup Client -----------------------
def setup_client():
    client = Client(Network(os.getenv("NETWORK", "testnet")))
    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID"))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))
        client.set_operator(operator_id, operator_key)
    except Exception:
        print("❌ Invalid OPERATOR_ID or OPERATOR_KEY in .env")
        sys.exit(1)
    print("✅ Connected to Hedera network")
    return client, operator_id, operator_key

# ----------------------- Create Receiver -----------------------
def create_receiver(client, signature_required=False, max_auto_assoc=10):
    receiver_key = PrivateKey.generate()
    tx = (
        AccountCreateTransaction()
        .set_key(receiver_key.public_key())
        .set_initial_balance(Hbar(1))
        .set_receiver_signature_required(signature_required)
        .set_max_automatic_token_associations(max_auto_assoc)
        .freeze_with(client)
        .sign(receiver_key)
    )
    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        sys.exit(f"❌ Receiver account creation failed: {receipt.status}")
    receiver_id = receipt.account_id
    print(f"✅ Receiver account created: {receiver_id} (auto-assoc={max_auto_assoc}, sig_required={signature_required})")
    return receiver_id, receiver_key

# ----------------------- Create Fungible Token -----------------------
def create_fungible_token(client, operator_id, operator_key, name="FTK", symbol="FT", initial_supply=1000):
    tx = TokenCreateTransaction() \
        .set_token_name(name) \
        .set_token_symbol(symbol) \
        .set_initial_supply(initial_supply) \
        .set_token_type(TokenType.FUNGIBLE_COMMON) \
        .set_supply_type(SupplyType.FINITE) \
        .set_max_supply(initial_supply) \
        .set_treasury_account_id(operator_id) \
        .freeze_with(client) \
        .sign(operator_key)
    receipt = tx.execute(client)
    token_id = receipt.token_id
    print(f"✅ Fungible token created: {token_id}")
    return token_id

# ----------------------- Create and Mint NFT -----------------------
def create_and_mint_nft(client, operator_id, operator_key, name="NFTK", symbol="NFT"):
    tx = TokenCreateTransaction() \
        .set_token_name(name) \
        .set_token_symbol(symbol) \
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

    tx_mint = TokenMintTransaction(token_id=nft_token_id, metadata=[b"NFT Metadata Auto"]) \
        .freeze_with(client).sign(operator_key)
    receipt_mint = tx_mint.execute(client)
    serial = receipt_mint.serial_numbers[0]
    nft_id = NftId(nft_token_id, serial)
    print(f"✅ NFT minted: serial {serial}")

    return nft_id

# ----------------------- Log Balances -----------------------
def log_balances(client, operator_id, receiver_id, ft_ids, nft_ids, prefix=""):
    print(f"\n{prefix} balances and NFT ownership:")
    for ft_id in ft_ids:
        sender_balance = CryptoGetAccountBalanceQuery(operator_id).execute(client).token_balances.get(ft_id, 0)
        receiver_balance = CryptoGetAccountBalanceQuery(receiver_id).execute(client).token_balances.get(ft_id, 0)
        print(f"Fungible token {ft_id} -> Sender: {sender_balance}, Receiver: {receiver_balance}")
    for nft_id in nft_ids:
        info = TokenNftInfoQuery(nft_id=nft_id).execute(client)
        print(f"NFT {nft_id} now owned by {info.account_id}")

# ----------------------- Perform Airdrop -----------------------
def perform_airdrop(client, operator_id, operator_key, receiver_id, ft_ids, nft_ids, ft_amount=100):
    tx = TokenAirdropTransaction()
    for ft_id in ft_ids:
        tx.add_token_transfer(ft_id, operator_id, -ft_amount)
        tx.add_token_transfer(ft_id, receiver_id, ft_amount)
    for nft_id in nft_ids:
        tx.add_nft_transfer(nft_id, operator_id, receiver_id)
    tx.freeze_with(client).sign(operator_key)
    receipt = tx.execute(client)
    print(f"\n✅ Airdrop executed: {receipt.transaction_id}")

# ----------------------- Verify Airdrop Contents -----------------------
def verify_airdrop_contents(client, operator_id, receiver_id, ft_ids, nft_ids, ft_amount=100):
    print("\n🔍 Verifying airdrop transaction contents:")
    tx_preview = TokenAirdropTransaction()
    for ft_id in ft_ids:
        tx_preview.add_token_transfer(ft_id, operator_id, -ft_amount)
        tx_preview.add_token_transfer(ft_id, receiver_id, ft_amount)
    for nft_id in nft_ids:
        tx_preview.add_nft_transfer(nft_id, operator_id, receiver_id)
    print("Fungible token transfers scheduled:")
    for token_transfer in tx_preview.token_transfers:
        print(f"  Token {token_transfer.token_id} -> Account {token_transfer.account_id}: {token_transfer.amount}")
    print("NFT transfers scheduled:")
    for nft_transfer in tx_preview.nft_transfers:
        print(f"  NFT {nft_transfer.token_id} -> From {nft_transfer.sender_id} to {nft_transfer.receiver_id}, Serial {nft_transfer.serial_number}")

# ----------------------- Main Function -----------------------
def main():
    client, operator_id, operator_key = setup_client()
    receiver_id, receiver_key = create_receiver(client, signature_required=False)
    ft_id = create_fungible_token(client, operator_id, operator_key, name="FTK2", symbol="FT2")
    nft_id = create_and_mint_nft(client, operator_id, operator_key, name="NFTK2", symbol="NFT2")
    log_balances(client, operator_id, receiver_id, [ft_id], [nft_id], prefix="Before airdrop")

    print("\n🔍 Verifying initial state:")
    ft_balance_before = CryptoGetAccountBalanceQuery(receiver_id).execute(client).token_balances.get(ft_id, 0)
    print("✅ Receiver had no FT balance before → no prior association." if ft_balance_before == 0 else "⚠️ Receiver already had FT balance (check associations).")
    
    nft_info_before = TokenNftInfoQuery(nft_id=nft_id).execute(client)
    print("✅ Operator owned NFT before → ready to transfer." if nft_info_before.account_id == operator_id else "⚠️ NFT was already transferred.")

    verify_airdrop_contents(client, operator_id, receiver_id, [ft_id], [nft_id], ft_amount=100)
    perform_airdrop(client, operator_id, operator_key, receiver_id, [ft_id], [nft_id], ft_amount=100)
    log_balances(client, operator_id, receiver_id, [ft_id], [nft_id], prefix="After airdrop")

    print("\n🔍 Verifying auto-association & no-signature behavior:")
    ft_balance_after = CryptoGetAccountBalanceQuery(receiver_id).execute(client).token_balances.get(ft_id, 0)
    print("✅ Auto-association successful: Receiver accepted new fungible tokens without pre-association." if ft_balance_after > ft_balance_before else "❌ Auto-association failed.")

    nft_info_after = TokenNftInfoQuery(nft_id=nft_id).execute(client)
    print("✅ Signature not required: Receiver owns NFT without signing." if nft_info_after.account_id == receiver_id else "❌ NFT transfer failed.")

if __name__ == "__main__":
    main()
