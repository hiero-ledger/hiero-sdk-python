import os
import sys
import pathlib
from dotenv import load_dotenv

CURRENT_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent / "src"
sys.path.insert(0, str(PROJECT_ROOT))

from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_info import TokenId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_airdrop_pending_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction

# Set up Client
load_dotenv()
network = Network(os.environ.get('NETWORK', ''))
client = Client(network)

operator_id = AccountId.from_string(os.environ.get('OPERATOR_ID', ''))
operator_key = PrivateKey.from_string(os.environ.get('OPERATOR_KEY', ''))
client.set_operator(operator_id, operator_key)

# Create Sender and Receiver
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

sender_id = operator_id
sender_key = operator_key

receiver_id, receiver_private_key = create_receiver_account(client)

print(f"The sending account is: {sender_id}")
print(f"The receiver account is: {receiver_id}")

# Set up tokens I want to claim
# Create tokens

fungible_tx = (
   TokenCreateTransaction()
       .set_token_name("FungibleToken")
       .set_token_symbol("FT")
       .set_decimals(2)
       .set_initial_supply(1_000)
       .set_treasury_account_id(operator_id)
       .set_token_type(TokenType.FUNGIBLE_COMMON)
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(100_000_000)
       .freeze_with(client)
       .sign(operator_key)
   )

try:
   fungible_token_create_receipt = fungible_tx.execute(client)
   print("status:", fungible_token_create_receipt.status)
   try:
       status_enum = ResponseCode(fungible_token_create_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(fungible_token_create_receipt.status)

   print(f"Token create status: {status_name}{fungible_token_create_receipt.status}")
   print(f"Success! Fungible token created with id {fungible_token_create_receipt.token_id}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"Token creation failed {status_name} ({fungible_token_create_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to create tokens: {e}")

fungible_tx_2 = (
   TokenCreateTransaction()
       .set_token_name("FungibleToken2")
       .set_token_symbol("FT2")
       .set_decimals(2)
       .set_initial_supply(300)
       .set_treasury_account_id(operator_id)
       .set_token_type(TokenType.FUNGIBLE_COMMON)
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(300)
       .freeze_with(client)
       .sign(operator_key)
   )

try:
   fungible_token_create_2_receipt = fungible_tx_2.execute(client)
   print("status:", fungible_token_create_2_receipt.status)
   try:
       status_enum = ResponseCode(fungible_token_create_2_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(fungible_token_create_2_receipt.status)

   print(f"Token 2 create status: {status_name}{fungible_token_create_2_receipt.status}")
   print(f"Success! Fungible token 2 created with id {fungible_token_create_2_receipt.token_id}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"Token 2 creation failed {status_name} ({fungible_token_create_2_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to create tokens: {e}")

nft_tx = (
   TokenCreateTransaction()
       .set_token_name("NFT")
       .set_token_symbol("Symbol")
       .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
       .set_treasury_account_id(operator_id)
       .set_initial_supply(0)
       .set_supply_type(SupplyType.FINITE)
       .set_max_supply(100)
       .set_supply_key(operator_key)
       .freeze_with(client)
   )

try:
   nft_create_receipt = nft_tx.execute(client)
   print("status:", nft_create_receipt.status)
   try:
       status_enum = ResponseCode(nft_create_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(nft_create_receipt.status)

   print(f"NFT create status: {status_name}{nft_create_receipt.status}")
   print(f"Success! NFT token created with id {nft_create_receipt.token_id}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"NFT creation failed {status_name} ({nft_create_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to create NFT tokens: {e}")

# These are the tokens we will airdrop
fungible_token_id_1: TokenId = fungible_token_create_receipt.token_id
fungible_token_id_2: TokenId = fungible_token_create_2_receipt.token_id
nft_token_id_1: TokenId = nft_create_receipt.token_id

# Mint the NFT as we need a serial number to airdrop
mint_tx = (
   TokenMintTransaction()
       .set_token_id(nft_token_id_1)
       .set_metadata(b"my first NFT")
       .freeze_with(client)
       .sign(operator_key)
)

try:
   nft_mint_receipt = mint_tx.execute(client)
   print("status:", nft_mint_receipt.status)
   try:
       status_enum = ResponseCode(nft_mint_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(nft_mint_receipt.status)

   print(f"NFT create status: {status_name}{nft_mint_receipt.status}")
   print(f"Success! NFT minted with serial {nft_mint_receipt.serial_numbers}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"NFT mint failed {status_name} ({nft_mint_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to mint NFT tokens: {e}")

nft_serial_1 = nft_mint_receipt.serial_numbers[0]

# Regroup
print(f"The fungible token id 1 is : {fungible_token_id_1}")
print(f"The fungible token id 2 is : {fungible_token_id_2}")
print(f"The nft token id 1 is : {nft_token_id_1}")
print(f"The nft serial is : {nft_serial_1}")

# Built NFT instance
nft_id_1 = NftId(nft_token_id_1, nft_serial_1)
print(nft_id_1)

print(f"sender: {sender_id}")
print(f"receiver: {receiver_id}")
print(f"fungible_token_id_1: {fungible_token_id_1}")
print(f"fungible_token_id_2: {fungible_token_id_2}")
print(f"nft_token_id_1: {nft_id_1}")

# Not necessary to send tokens to the sender, as they created the token in this case.

# # Adding verification anyway for information purposes
# sender_info = AccountInfoQuery(sender_id).execute(client)

# def bal(token_id):
#     for rel in sender_info.token_relationships:
#         if str(rel.token_id) == str(token_id):
#             return getattr(rel, "balance", 0)
#     return 0

# assert bal(fungible_token_id_1) >= 900, "Not enough FT to airdrop"
# assert bal(fungible_token_id_2) >= 200, "Not enough FT2 to airdrop"

# print("Sender FT balance:", bal(fungible_token_id_1))  # should be 1000
# print("Sender FT2 balance:", bal(fungible_token_id_2)) # should be 300

# # --- Verify NFT owner is the sender (treasury) ---
# nft_info = (
#     TokenNftInfoQuery()
#     .set_nft_id(nft_id_1)
#     .execute(client)
# )
# assert str(nft_info.account_id) == str(sender_id), "Sender does not own the NFT serial"
# print("NFT owner (should be sender):", nft_info.account_id)

# # Ensure the receiver has the tokens to receive from the airdrop

# start with the fungibles
# associate_tx = (
#     TokenAssociateTransaction()
#     .set_account_id(receiver_id)
#     .add_token_id(fungible_token_id_1)
#     .add_token_id(fungible_token_id_2)
#     .freeze_with(client)
#     .sign(receiver_private_key)
# )

# try:
#     sender_associate_receipt = associate_tx.execute(client)
#     print("status:", sender_associate_receipt.status)
#     try:
#         status_enum = ResponseCode(sender_associate_receipt.status)
#         status_name = status_enum.name
#     except Exception:
#         status_enum = None
#         status_name = str(sender_associate_receipt.status)

#     print(f"Fungible associate status for receiver: {status_name}{sender_associate_receipt.status}")

#     if status_enum is None or status_enum != ResponseCode.SUCCESS:
#         raise RuntimeError(f"Associations failed {status_name} ({sender_associate_receipt.status})")  

# except Exception as e:
#     raise SystemExit(f"failed to associate tokens: {e}")

# # now with the nft id (not the serial)
# associate_tx = (
#     TokenAssociateTransaction()
#     .set_account_id(receiver_id)
#     .add_token_id(nft_token_id_1)
#     .freeze_with(client)
#     .sign(receiver_private_key)
# )

# try:
#     sender_associate_receipt = associate_tx.execute(client)
#     print("status:", sender_associate_receipt.status)
#     try:
#         status_enum = ResponseCode(sender_associate_receipt.status)
#         status_name = status_enum.name
#     except Exception:
#         status_enum = None
#         status_name = str(sender_associate_receipt.status)
#     print(f"NFT associate status for receiver: {status_name}{sender_associate_receipt.status}")
#     if status_enum is None or status_enum != ResponseCode.SUCCESS:
#         raise RuntimeError(f"Associations failed {status_name} ({sender_associate_receipt.status})")  
# except Exception as e:
#     raise SystemExit(f"failed to associate tokens: {e}")

# # # Create list of pending airdrops
pending_fungible_list = []
pending_fungible_list.append(fungible_token_id_1)
pending_fungible_list.append(fungible_token_id_2)
print(f"The list of pending fungible airdrops to create: {pending_fungible_list}")

pending_nft_list = []
pending_nft_list.append(nft_id_1)
print(f"The list of pending nft airdrops to create: {pending_nft_list}")

# info_tx = (AccountInfoQuery(sender_id)
#            .execute(client))
# print("Sender account token balances before airdrop:")
# for rel in info_tx.token_relationships:
#     tid = getattr(rel, "token_id", None)
#     sym = getattr(rel, "symbol", "")
#     bal = getattr(rel, "balance", None)        # fungibles
#     dec = getattr(rel, "decimals", None)
#     sn  = getattr(rel, "serial_numbers", None)
#     # print nicely for both fungible & NFT
#     if bal is not None and dec is not None:
#         print(f"  {tid} ({sym}) | balance: {bal} | decimals: {dec}")
#     else:
#         print(f"  {tid} ({sym}) | NFT relationship")

# # # Create the airdrops for each token
airdrop_tx = (TokenAirdropTransaction()
           .add_token_transfer(fungible_token_id_1, sender_id, -900)
           .add_token_transfer(fungible_token_id_1, receiver_id, +900)
           .add_token_transfer(fungible_token_id_2, sender_id, -200)
           .add_token_transfer(fungible_token_id_2, receiver_id, +200)
           .add_nft_transfer(nft_id_1, sender_id, receiver_id)
           .freeze_with(client)
           .sign(sender_key)
           )
print(f"Airdrop transaction commencing! {airdrop_tx}")

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

# #  associate the receiver to allow claim to finalize balances into their account
# associate_rx = (
#     TokenAssociateTransaction()
#     .set_account_id(receiver_id)
#     .add_token_id(fungible_token_id_1)
#     .add_token_id(fungible_token_id_2)
#     .add_token_id(nft_token_id_1)
#     .freeze_with(client)
#     .sign(receiver_private_key)
# )
# assoc_receipt = associate_rx.execute(client)
# print("Receiver associate status:", ResponseCode(assoc_receipt.status).name, assoc_receipt.status)


# sender_info = AccountInfoQuery(sender_id).execute(client)
# def bal(tid):
#     for rel in sender_info.token_relationships:
#         if str(rel.token_id) == str(tid):
#             return getattr(rel, "balance", 0)
#     return 0
# assert bal(fungible_token_id_1) >= 900
# assert bal(fungible_token_id_2) >= 200
# # Optional: confirm NFT still owned by sender pre-claim
# nft_info = TokenNftInfoQuery().set_nft_id(nft_id_1).execute(client)
# assert str(nft_info.account_id) == str(sender_id)

# # Pending Airdrops To Claim
pending_fungible_1 = PendingAirdropId(sender_id, receiver_id, fungible_token_id_1, None)
pending_fungible_2 = PendingAirdropId(sender_id, receiver_id, fungible_token_id_2, None)
pending_nft_1 = PendingAirdropId(sender_id, receiver_id, None, nft_id_1)

print(f"pending: {pending_fungible_1}")
print(f"pending: {pending_fungible_2}")
print(f"pending: {pending_nft_1}")

# # We turn it into a list of pending airdrop ids to claim
pending_airdrop_ids = []
pending_airdrop_ids.append(pending_fungible_1)
pending_airdrop_ids.append(pending_fungible_2)
pending_airdrop_ids.append(pending_nft_1)

print(f"Here is the list of pending airdrop ids: {pending_airdrop_ids}")

claim_tx = (
   TokenClaimAirdropTransaction()
   .add_pending_airdrop_ids(pending_airdrop_ids)
   .freeze_with(client)
   # .sign(operator_key)
   .sign(receiver_private_key)
)

print("\nTransaction repr:", repr(claim_tx))
print("\nTransaction str:", str(claim_tx))

try:
   airdrop_claim_receipt = claim_tx.execute(client)
   try:
       status_enum = ResponseCode(airdrop_claim_receipt.status)
       status_name = status_enum.name
   except Exception:
       status_enum = None
       status_name = str(airdrop_claim_receipt.status)

   print(f"Airdrop claim status: {status_name}{airdrop_claim_receipt.status}")
   # print(f"Airdrops successfully claimed: {airdrop_claim_receipt.status}")

   if status_enum is None or status_enum != ResponseCode.SUCCESS:
       raise RuntimeError(f"Airdrop claim failed {status_name} ({airdrop_claim_receipt.status})")  

except Exception as e:
   raise SystemExit(f"failed to claim airdrops: {e}")