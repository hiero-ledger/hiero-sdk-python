import warnings
warnings.simplefilter("ignore", UserWarning)

import os
import sys
import pathlib
from dotenv import load_dotenv

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent / "src"
sys.path.insert(0, str(PROJECT_ROOT))

from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_info import TokenId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_pending_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.exceptions import PrecheckError, MaxAttemptsError, ReceiptStatusError
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction

# Set up Client
load_dotenv()
network = Network(os.environ.get('NETWORK', ''))
client = Client(network)

operator_id = AccountId.from_string(os.environ.get('OPERATOR_ID', ''))
operator_key = PrivateKey.from_string(os.environ.get('OPERATOR_KEY', ''))
client.set_operator(operator_id, operator_key)

# Create Receiver
def create_receiver_account(client):
   # Generate private key for new account
   receiver_private_key = PrivateKey.generate_ed25519()
   receiver_public_key = receiver_private_key.public_key()
  
   # Create new account with initial balance of 1 HBAR
   transaction = (
       AccountCreateTransaction()
       .set_key(receiver_public_key)
       .set_initial_balance(Hbar(1))
       .freeze_with(client)
   )
   receipt = transaction.execute(client)
  
   # Check if account creation was successful
   if receipt.status != ResponseCode.SUCCESS:
       print(f"Account creation failed with status: {ResponseCode(receipt.status).name}")
       sys.exit(1)
  
   # Get account ID from receipt
   receiver_id = receipt.account_id
   # print(f"New receiver account created with ID: {receiver_id}")
   # print(f"New receiver account created with private key: {receiver_private_key}")
   return receiver_id, receiver_private_key

# Call the function and create the receiver account
receiver_id, receiver_private_key = create_receiver_account(client)

# To keep things simple, we make the operator the sender
sender_id = operator_id
sender_key = operator_key

# Ensure the sender and receiver are set
print(f"The sending account is: {sender_id}")
print(f"The receiver account is: {receiver_id}")

# To claim an airdrop, we need to:
""" Goes through the steps to claim an airdrop

1. Create tokens to airdrop
In this case, we create a mix of fungible and nft tokens using TokenCreateTransaction.

2. Ensure the sender has the tokens to airdrop 
In this case, they will because they are creating the tokens as the operator.

3. The sender airdrops the tokens to the receiver.
Using TokenAirdropTransaction. Their balance will not change until it is claimed.

4. The receiver will claim the airdrop using TokenClaimAirdropTransaction.

5. Verify the balance of sender and receiver before and after the airdrop and claim.

"""
# Create tokens
fungible_tx_1 = (
   TokenCreateTransaction()
       .set_token_name("FungibleToken1")
       .set_token_symbol("FT1")
       .set_decimals(2)
       .set_initial_supply(1_000) # We will airdrop 900
       .set_treasury_account_id(operator_id) # Sender is treasury so already owns tokens.
       .set_token_type(TokenType.FUNGIBLE_COMMON) 
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(100_000_000)
       .freeze_with(client)
       .sign(operator_key)
   )

try:
    fungible_1_receipt = fungible_tx_1.execute(client)
    status = ResponseCode(fungible_1_receipt.status)
    if status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Fungible token 1 creation failed: {status.name} ({fungible_1_receipt.status})")
    print(f"✅ Fungible token 1 created: id={fungible_1_receipt.token_id}, status={status.name} ({fungible_1_receipt.status})")

except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
    status = getattr(e, "status", None)
    status_name = ResponseCode(status).name if status is not None else type(e).__name__
    tx_id = getattr(e, "transaction_id", None)
    node  = getattr(e, "node_account_id", None)
    raise SystemExit(f"{type(e).__name__}: {status_name} ({status}) tx={tx_id} node={node}") from e

except Exception as e:
    raise SystemExit(f"Unexpected error creating Fungible Token 1: {e}") from e

fungible_tx_2 = (
   TokenCreateTransaction()
       .set_token_name("FungibleToken2")
       .set_token_symbol("FT2")
       .set_decimals(2)
       .set_initial_supply(300) # We will airdrop 200.
       .set_treasury_account_id(operator_id) # Sender is treasury so already owns tokens.
       .set_token_type(TokenType.FUNGIBLE_COMMON)
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(300)
       .freeze_with(client)
       .sign(operator_key)
   )

try:
    fungible_2_receipt = fungible_tx_2.execute(client)
    status = ResponseCode(fungible_2_receipt.status)
    if status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Fungible token 2 creation failed: {status.name} ({fungible_2_receipt.status})")
    print(f"✅ Fungible token 2 created: id={fungible_2_receipt.token_id}, status={status.name} ({fungible_2_receipt.status})")

except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
    status = getattr(e, "status", None)
    status_name = ResponseCode(status).name if status is not None else type(e).__name__
    tx_id = getattr(e, "transaction_id", None)
    node  = getattr(e, "node_account_id", None)
    raise SystemExit(f"{type(e).__name__}: {status_name} ({status}) tx={tx_id} node={node}") from e

except Exception as e:
    raise SystemExit(f"Unexpected error creating Fungible Token 2: {e}") from e

nft_tx_1 = (
   TokenCreateTransaction()
       .set_token_name("NFTToken1")
       .set_token_symbol("NFT1")
       .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
       .set_treasury_account_id(operator_id) # Sender is treasury so already owns tokens.
       .set_initial_supply(0) # We need to mint one NFT serial to airdrop
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(100)
       .set_supply_key(operator_key)
       .freeze_with(client)
   )

try:
    nft_receipt = nft_tx_1.execute(client)
    status = ResponseCode(nft_receipt.status)
    if status != ResponseCode.SUCCESS:
        raise RuntimeError(f"NFT token 1 creation failed: {status.name} ({nft_receipt.status})")
    print(f"✅ NFT token 1 created: id={nft_receipt.token_id}, status={status.name} ({nft_receipt.status})")

except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
    status = getattr(e, "status", None)
    status_name = ResponseCode(status).name if status is not None else type(e).__name__
    tx_id = getattr(e, "transaction_id", None)
    node  = getattr(e, "node_account_id", None)
    raise SystemExit(f"{type(e).__name__}: {status_name} ({status}) tx={tx_id} node={node}") from e

except Exception as e:
    raise SystemExit(f"Unexpected error creating NFT Token 1: {e}") from e

# Summary of the tokens we will airdrop
## Fungible

airdrop_fungible_token_id_1: TokenId = fungible_1_receipt.token_id
airdrop_fungible_token_id_2: TokenId = fungible_2_receipt.token_id

## NFT
### We only have the token id part of the NFT, we are missing the serial number. We need both for airdrops.
airdrop_nft_1: TokenId = nft_receipt.token_id

# To airdrop an NFT, we airdrop a serial number. We mint a serial number of this nft token id:

mint_tx = (
   TokenMintTransaction()
       .set_token_id(airdrop_nft_1)
       .set_metadata(b"NFT1 Serial 1")
       .freeze_with(client)
       .sign(operator_key)
)

try:
    mint_receipt = mint_tx.execute(client)
    status = ResponseCode(mint_receipt.status)
    if status != ResponseCode.SUCCESS:
        raise RuntimeError(f"NFT1 Serial 1 mint failed: {status.name} ({mint_receipt.status})")
    print(f"✅ NFT1 Serial 1 minted with serial number={mint_receipt.serial_numbers[0]}, status={status.name} ({mint_receipt.status})")

except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
    status = getattr(e, "status", None)
    status_name = ResponseCode(status).name if status is not None else type(e).__name__
    tx_id = getattr(e, "transaction_id", None)
    node  = getattr(e, "node_account_id", None)
    raise SystemExit(f"{type(e).__name__}: {status_name} ({status}) tx={tx_id} node={node}") from e

except Exception as e:
    raise SystemExit(f"Unexpected error minting NFT1 Serial 1: {e}") from e

# We can now build an NFT to airdrop
airdrop_nft_token_id_1 = nft_receipt.token_id
airdrop_nft_serial_1 = mint_receipt.serial_numbers[0]

airdrop_nft_1: NftId = NftId(airdrop_nft_token_id_1, airdrop_nft_serial_1)

# Tokens to airdrop summary
print(f"Our tokens to airdrop will be fungible: {airdrop_fungible_token_id_1} and {airdrop_fungible_token_id_2} and NFT: {airdrop_nft_1} ")
print(f"The sender will be {sender_id} and receiver {receiver_id} ")

# To airdrop tokens, we need the sender to have the tokens which requires association and token balance. 
# In this case it is not needed as the sender is the treasury for all these tokens.

# Verifying the sender has the tokens which can be later airdropped (information purposes))
sender_info = AccountInfoQuery(sender_id).execute(client)

def bal(token_id):
    for rel in sender_info.token_relationships:
        if str(rel.token_id) == str(token_id):
            return getattr(rel, "balance", 0)
    return 0

assert bal(airdrop_fungible_token_id_1) >= 900, "Not enough FT1 to airdrop"
assert bal(airdrop_fungible_token_id_2) >= 200, "Not enough FT2 to airdrop"

print(f"Sender {sender_id} FT1 balance {bal(airdrop_fungible_token_id_1)}") # Should be 100
print(f"Sender {sender_id} FT2 balance {bal(airdrop_fungible_token_id_2)}") # Should be 300

def nft_owner(nft_id: NftId) -> str:
    info = TokenNftInfoQuery(nft_id).execute(client)
    return str(info.account_id)

airdrop_nft_1 = NftId(airdrop_nft_token_id_1, airdrop_nft_serial_1)
owner = nft_owner(airdrop_nft_1)
is_owner = 1 if owner == str(sender_id) else 0

print(f"Sender {owner} NFT1 serial {airdrop_nft_serial_1} balance = {is_owner}")
assert is_owner == 1, "Sender does not own the minted NFT"

# # We (unsure - double check) need the receiver to associate the tokens to claim them.

# def associate_tokens_once(client, account_id, account_private_key, token_ids):
#     tx = TokenAssociateTransaction().set_account_id(account_id)
#     for tid in token_ids:
#         tx.add_token_id(tid)

#     tx = tx.freeze_with(client).sign(account_private_key)

#     try:
#         receipt = tx.execute(client)
#         status = ResponseCode(receipt.status)
#         if status not in (ResponseCode.SUCCESS,):
#             raise RuntimeError(f"Association failed: {status.name} ({receipt.status})")
#         print(f"✅ Association status: {status.name} ({receipt.status})")
#         return receipt
#     except Exception as e:
#         raise SystemExit(f"failed to associate tokens: {e}") from e

# # Associate all the tokens at once
# all_token_ids = [
#     airdrop_fungible_token_id_1,
#     airdrop_fungible_token_id_2,
#     airdrop_nft_token_id_1,   # note: associate NFT *token id*, not a serial
# ]

# associate_tokens_once(client, receiver_id, receiver_private_key, all_token_ids)

# def verify_associations(client, account_id, token_ids):
#     info = AccountInfoQuery(account_id).execute(client)
#     rels = getattr(info, "token_relationships", [])

#     associated = {str(r.token_id) for r in rels}

#     missing = []
#     for tid in token_ids:
#         ok = 1 if str(tid) in associated else 0
#         print(f"Associated({tid}) = {ok}")
#         if not ok:
#             missing.append(tid)

#     if missing:
#         raise RuntimeError(f"Account {account_id} is missing associations for: {', '.join(map(str, missing))}")

#     print(f"✅ All {len(token_ids)} tokens associated to {account_id}. The receiver is {receiver_id}")
#     return True

# Call to verify the associations for each
# verify_associations(client, receiver_id, all_token_ids)

# Create the airdrops for each token
airdrop_tx = (TokenAirdropTransaction()
           .add_token_transfer(airdrop_fungible_token_id_1, sender_id, -900)
           .add_token_transfer(airdrop_fungible_token_id_1, receiver_id, +900)
           .add_token_transfer(airdrop_fungible_token_id_2, sender_id, -200)
           .add_token_transfer(airdrop_fungible_token_id_2, receiver_id, +200)
           .add_nft_transfer(airdrop_nft_1, sender_id, receiver_id)
           .freeze_with(client)
           .sign(sender_key)
           )
print(f"Airdrop transaction commencing! {airdrop_tx}. The sender {sender_id} is airdropping {airdrop_fungible_token_id_1}, {airdrop_fungible_token_id_2} and {airdrop_nft_1} to receiver {receiver_id}")

try:
   airdrop_receipt = airdrop_tx.execute(client)
   try:
       status_enum = ResponseCode(airdrop_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(airdrop_receipt.status)

   print(f"Airdrop create status: {status_name}{airdrop_receipt.status}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"Airdrop creation failed {status_name} ({airdrop_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to create airdrops: {e}")

# # #  associate the receiver to allow claim to finalize balances into their account
# # associate_rx = (
# #     TokenAssociateTransaction()
# #     .set_account_id(receiver_id)
# #     .add_token_id(fungible_token_id_1)
# #     .add_token_id(fungible_token_id_2)
# #     .add_token_id(nft_token_id_1)
# #     .freeze_with(client)
# #     .sign(receiver_private_key)
# # )
# # assoc_receipt = associate_rx.execute(client)
# # print("Receiver associate status:", ResponseCode(assoc_receipt.status).name, assoc_receipt.status)

# Airdrop Transaction complete but it is not claimed, so the account balances should not yet change:
sender_info = AccountInfoQuery(sender_id).execute(client)

def bal(token_id, info):
    for rel in info.token_relationships:
        if str(rel.token_id) == str(token_id):
            return getattr(rel, "balance", 0)
    return 0

# Sender balances (should still hold all tokens pre-claim)
sender_ft1 = bal(airdrop_fungible_token_id_1, sender_info)
sender_ft2 = bal(airdrop_fungible_token_id_2, sender_info)
print(f"Sender FT1 balance (expect 1000): {sender_ft1}")
print(f"Sender FT2 balance (expect 300): {sender_ft2}")

assert sender_ft1 == 1000
assert sender_ft2 == 300

nft_info = TokenNftInfoQuery(airdrop_nft_1).execute(client)
print(f"NFT owner pre-claim (expect sender {sender_id}): {nft_info.account_id}")
assert str(nft_info.account_id) == str(sender_id)

# Receiver balances (should still be 0 pre-claim)
receiver_info = AccountInfoQuery(receiver_id).execute(client)

receiver_ft1 = bal(airdrop_fungible_token_id_1, receiver_info)
receiver_ft2 = bal(airdrop_fungible_token_id_2, receiver_info)
print(f"Receiver FT1 balance (expect 0): {receiver_ft1}")
print(f"Receiver FT2 balance (expect 0): {receiver_ft2}")

assert receiver_ft1 == 0
assert receiver_ft2 == 0

# Double-check NFT is NOT owned by receiver yet
nft_info = TokenNftInfoQuery(airdrop_nft_1).execute(client)
print(f"NFT owner pre-claim (still expect sender {sender_id}): {nft_info.account_id}")
assert str(nft_info.account_id) == str(sender_id)

# We will now claim the airdrops which will change the sender and receiver balances
## Pending Airdrops To Claim
pending_fungible_1 = PendingAirdropId(sender_id, receiver_id, airdrop_fungible_token_id_1, None)
pending_fungible_2 = PendingAirdropId(sender_id, receiver_id, airdrop_fungible_token_id_2, None)
pending_nft_1 = PendingAirdropId(sender_id, receiver_id, None, airdrop_nft_1)

## We turn it into a list of pending airdrop ids to claim
pending_airdrop_ids = []
pending_airdrop_ids.append(pending_fungible_1)
pending_airdrop_ids.append(pending_fungible_2)
pending_airdrop_ids.append(pending_nft_1)

print(f"Here is the list of pending airdrop ids to claim: {pending_airdrop_ids}")

claim_tx = (
   TokenClaimAirdropTransaction()
   .add_pending_airdrop_ids(pending_airdrop_ids)
   .freeze_with(client)
   .sign(receiver_private_key)
)

print("Transaction str:", str(claim_tx))

try:
   print("Airdrop Claiming commencing...")
   airdrop_claim_receipt = claim_tx.execute(client)
   try:
       status_enum = ResponseCode(airdrop_claim_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(airdrop_claim_receipt.status)

   print(f"Airdrop claim status: {status_name}{airdrop_claim_receipt.status}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"Airdrop claim failed {status_name} ({airdrop_claim_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to claim airdrops: {e}")

# Re-query account infos after the claim
sender_info   = AccountInfoQuery(sender_id).execute(client)
receiver_info = AccountInfoQuery(receiver_id).execute(client)

def bal(token_id, info):
    for rel in info.token_relationships:
        if str(rel.token_id) == str(token_id):
            return getattr(rel, "balance", 0)
    return 0

# --- Sender balances (post-claim) ---
sender_ft1 = bal(airdrop_fungible_token_id_1, sender_info)
sender_ft2 = bal(airdrop_fungible_token_id_2, sender_info)
print("\n Sender balances after claim:")
print(f"  FT1 (expect 100): {sender_ft1}")
print(f"  FT2 (expect 100): {sender_ft2}")

receiver_ft1 = bal(airdrop_fungible_token_id_1, receiver_info)
receiver_ft2 = bal(airdrop_fungible_token_id_2, receiver_info)
print("\nReceiver balances after claim:")
print(f"  FT1 (expect 900): {receiver_ft1}")
print(f"  FT2 (expect 200): {receiver_ft2}")

nft_info = TokenNftInfoQuery(airdrop_nft_1).execute(client)
print("\nNFT ownership after claim:")
print(f"  Owner (expect receiver {receiver_id}): {nft_info.account_id}")

assert sender_ft1 == 100
assert sender_ft2 == 100
assert receiver_ft1 == 900
assert receiver_ft2 == 200
assert str(nft_info.account_id) == str(receiver_id)
