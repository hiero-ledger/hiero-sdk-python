# Association is not required in advance, because the act of claiming will both associate and transfer for the network
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
   tx_create_account = (
       AccountCreateTransaction()
       .set_key(receiver_public_key)
       .set_initial_balance(Hbar(1))
       # Ensure the receiver needs to sign in order to require a claimAirdrop transaction to receive a Pending airdrop
       # When false, the receiver needs to have associated the token or have sufficient association slots.
       .set_receiver_signature_required(True)
       .freeze_with(client)
        # We set the receiver, so we need to sign:
       .sign(receiver_private_key)
   )

   receipt = tx_create_account.execute(client)
  
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

# Ensure the receiver has to sign to receive an airdrop
receiver_info = AccountInfoQuery(receiver_id).execute(client)

# print(f"\nAccount automatic token associations: {receiver_info.max_automatic_token_associations}") #Not yet part of the sdk
print(f"Account receiver signature required: {receiver_info.receiver_signature_required}")


# To claim an airdrop, we need to:
""" Goes through the steps to claim an airdrop

1. We create an account that requires receiver signature signing.
This will force the user to need a token claim airdrop transaction.
(Else automatic association if they have sufficient slots, or, they need to have a prior association)

2. Create tokens to airdrop
In this case, we create a mix of fungible and nft tokens using TokenCreateTransaction.

3. Ensure the sender has the tokens to airdrop 
In this case, they will because they are creating the tokens as the operator.

4. The sender airdrops the tokens to the receiver.
Using TokenAirdropTransaction. Their balance will not change until it is claimed.

5. The receiver will sign and claim the airdrop using TokenClaimAirdropTransaction.
No need to associate tokens to the receiver, this is handled by the network.

6. Verify the balance of sender and receiver before and after the airdrop and claim.

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

# Check receiver has no token associations before claim
# The network will auto-associate these tokens on airdrop claim
preclaim_info = AccountInfoQuery(receiver_id).execute(client)

if not preclaim_info.token_relationships:
    print(f"\nReceiver {receiver_id} has 0 token associations pre-claim (as expected).\n")
else:
    print(f"\nReceiver {receiver_id} already associated with tokens:")
    for rel in preclaim_info.token_relationships:
        print(f" - Token {rel.token_id}, balance={rel.balance}\n")


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

# --- Re-query account infos after the claim ---
sender_info   = AccountInfoQuery(sender_id).execute(client)
receiver_info = AccountInfoQuery(receiver_id).execute(client)

def balance(info, token_id) -> int:
    """Helper to get token balance from AccountInfo by token ID."""
    for rel in info.token_relationships:
        if str(rel.token_id) == str(token_id):
            return rel.balance
    return 0

print("\nSender balances after claim:")
print(f"  FT1 (expect 100): {balance(sender_info, airdrop_fungible_token_id_1)}")
print(f"  FT2 (expect 100): {balance(sender_info, airdrop_fungible_token_id_2)}")

print("\nReceiver balances after claim:")
print(f"  FT1 (expect 900): {balance(receiver_info, airdrop_fungible_token_id_1)}")
print(f"  FT2 (expect 200): {balance(receiver_info, airdrop_fungible_token_id_2)}")

nft_info = TokenNftInfoQuery(airdrop_nft_1).execute(client)
print("\nNFT ownership after claim:")
print(f"  Owner (expect receiver {receiver_id}): {nft_info.account_id}")

expected_tokens = {
    str(airdrop_fungible_token_id_1),
    str(airdrop_fungible_token_id_2),
    str(airdrop_nft_token_id_1)   # Associate by NFT token ID, not serial
}

associated_tokens = {str(rel.token_id) for rel in receiver_info.token_relationships}
print(f"\nReceiver {receiver_id} is associated with: {associated_tokens}")
