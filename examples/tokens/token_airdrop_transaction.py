"""
uv run examples/tokens/token_airdrop_transaction.py
python examples/tokens/token_airdrop_transaction.py
"""

import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
 Client,
 Network,
 AccountId,
 PrivateKey,
 Hbar,
 AccountCreateTransaction,
 TokenCreateTransaction,
 TokenAirdropTransaction,
 TokenAssociateTransaction,
 TokenMintTransaction,
 TokenType,
 ResponseCode,
 NftId,
 TransactionRecordQuery,
 TokenNftInfoQuery
)
from hiero_sdk_python.query.account_info_query import AccountInfoQuery

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")

    client = Client(network)


    try:
            operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
            operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
            client.set_operator(operator_id, operator_key)
            print(f"Client set up with operator id {client.operator_account_id}")

            return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

def create_account(client, operator_key):
    """Create a new recipient account"""
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate()

    try:
        account_tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        account_receipt = account_tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = account_receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")

        return recipient_key, recipient_id
    except Exception as e:
        print(f"❌ Error creating new recipient account: {e}")
        sys.exit(1)

def create_token(client, operator_id, operator_key):
    """Create a fungible token"""
    print("\nCreating a token...")
    try:
        token_tx = (
            TokenCreateTransaction()
            .set_token_name("Token A")
            .set_token_symbol("TKA")
            .set_initial_supply(1)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_treasury_account_id(operator_id)
        )
        token_receipt = token_tx.freeze_with(client).sign(operator_key).execute(client)
        token_id = token_receipt.token_id

        print(f"✅ Success! Created token: {token_id}")

        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

def create_nft(client, operator_key, operator_id):
    """Create a NFT"""
    print("\nCreating a nft...")
    try:
        nft_tx = (
            TokenCreateTransaction()
            .set_token_name("Token B")
            .set_token_symbol("NFTA")
            .set_initial_supply(0)
            .set_supply_key(operator_key)
            .set_token_type(TokenType.NON_FUNGIBLE_UNIQUE)
            .set_treasury_account_id(operator_id)
        )
        nft_receipt = nft_tx.freeze_with(client).sign(operator_key).execute(client)
        nft_id = nft_receipt.token_id

        print(f"✅ Success! Created nft: {nft_id}")
        return nft_id
    except Exception as e:
        print(f"❌ Error creating nft: {e}")
        sys.exit(1)

def mint_nft(client, operator_key, nft_id):
    """Mint the NFT with metadata"""
    print("\nMinting a nft...")
    try:
        mint_tx = TokenMintTransaction(token_id=nft_id, metadata=[b"NFT data"])
        mint_tx.freeze_with(client)
        mint_tx.sign(operator_key)
        mint_receipt = mint_tx.execute(client)

        serial_number = mint_receipt.serial_numbers[0]
        print(f"✅ Success! Nft minted serial: { serial_number }.")
        return serial_number
    except Exception as e:
        print(f"❌ Error minting nft: {e}")
        sys.exit(1)

def associate_tokens(client, recipient_id, recipient_key, tokens):
    """Associate the token and nft with the recipient"""
    print("\nAssociating tokens to recipient...")
    try:
        assocciate_tx = TokenAssociateTransaction(
            account_id=recipient_id,
            token_ids=tokens
        )
        assocciate_tx.freeze_with(client)
        assocciate_tx.sign(recipient_key)
        assocciate_tx.execute(client)

        # Use AccountInfoQuery to check token associations
        info = AccountInfoQuery(account_id=recipient_id).execute(client)
        
        # Get the list of associated token IDs from token_relationships
        associated_token_ids = [rel.token_id for rel in info.token_relationships]

        print("\nTokens associated with recipient:")
        for token_id in tokens:
            associated = token_id in associated_token_ids
            print(f"  {token_id}: {'Associated' if associated else 'NOT Associated'}")

        print("\n✅ Success! Token association complete.")

    except Exception as e:
        print(f"❌ Error associating tokens: {e}")
        sys.exit(1)


def airdrop_tokens(client, operator_id, operator_key, recipient_id, token_id, nft_id, serial_number):
    """
    Build and execute a TokenAirdropTransaction that transfers one fungible token
    and the specified NFT serial. Returns the airdrop receipt.
    """
    print(f"\nStep 6: Airdropping tokens to recipient {recipient_id}:")
    print(f"  - 1 fungible token TKA ({token_id})")
    print(f"  - NFT from NFTA collection ({nft_id}) with serial number #{serial_number}")
    try:
        airdrop_tx = (
            TokenAirdropTransaction()
            .add_token_transfer(token_id=token_id, account_id=operator_id, amount=-1)
            .add_token_transfer(token_id=token_id, account_id=recipient_id, amount=1)
            .add_nft_transfer(
                nft_id=NftId(token_id=nft_id, serial_number=serial_number),
                sender_id=operator_id,
                receiver_id=recipient_id,
            )
        )
        airdrop_tx.freeze_with(client)
        airdrop_tx.sign(operator_key)
        airdrop_receipt = airdrop_tx.execute(client)

        if airdrop_receipt.status != ResponseCode.SUCCESS:
            print(f"❌ Fail to airdrop: Status: {airdrop_receipt.status}")
            sys.exit(1)

        print(f"Token airdrop ID: {airdrop_receipt.transaction_id}")
        return airdrop_receipt
    except Exception as e:
        print(f"❌ Error airdropping tokens: {e}")
        sys.exit(1)


def _check_token_transfer_for_pair(record, token_id, operator_id, recipient_id):
    """Return True if record shows operator sent -1 and recipient got +1 for token_id."""
    try:
        token_transfers = getattr(record, "token_transfers", {}) or {}
        # Try direct mapping lookup, otherwise fall back to equality-match in a generator
        transfers = token_transfers.get(token_id) or next((v for k, v in token_transfers.items() if k == token_id), None)
        # Validate shape and compare expected amounts in a single expression
        return isinstance(transfers, dict) and transfers.get(operator_id) == -1 and transfers.get(recipient_id) == 1
    except Exception:
        return False


def _extract_nft_transfers(record):
    """Return list of (token_key, serial, sender, receiver) tuples from record.nft_transfers."""
    nft_list = []
    # Defensive access: handle missing or unexpected shapes without silencing errors
    nft_transfers_map = getattr(record, "nft_transfers", {}) or {}
    if not isinstance(nft_transfers_map, dict):
        return nft_list

    for token_key, nft_transfers in nft_transfers_map.items():
        if nft_transfers is None:
            continue
        # Skip non-iterable or string-like values
        if not hasattr(nft_transfers, "__iter__") or isinstance(nft_transfers, (str, bytes)):
            continue

        for nft_transfer in nft_transfers:
            sender = getattr(nft_transfer, "sender_id", None)
            receiver = getattr(nft_transfer, "receiver_id", None)
            serial = getattr(nft_transfer, "serial_number", None)
            nft_list.append((token_key, serial, sender, receiver))
    return nft_list


def verify_transaction_record(
    client: Client,
    airdrop_receipt,
    operator_id,
    recipient_id,
    token_id,
    nft_id,
    serial_number,
):
    """
    Verify the airdrop transaction record for expected token and NFT transfers.
    Returns a dict summarizing results for further analysis.
    """
    result = {
        "record": None,
        "expected_token_transfer": False,
        "nft_transfer_confirmed": False,
        "nft_serials_transferred": [],
    }

    try:
        record = TransactionRecordQuery(transaction_id=airdrop_receipt.transaction_id).execute(client)
    except Exception as e:
        print(f"❌ Error fetching transaction record: {e}")
        return result

    result["record"] = record

    # Token transfer check (delegated)
    result["expected_token_transfer"] = _check_token_transfer_for_pair(
        record, token_id, operator_id, recipient_id
    )

    # NFT transfers: extract and then look for a matching entry
    nft_serials = _extract_nft_transfers(record)
    result["nft_serials_transferred"] = nft_serials

    # Single-pass confirmation using any() to keep branching minimal
    result["nft_transfer_confirmed"] = any(
        token_key == nft_id and sender == operator_id and receiver == recipient_id and serial == serial_number
        for token_key, serial, sender, receiver in nft_serials
    )

    return result


def verify_post_airdrop_balances(
    client: Client,
    operator_id,
    recipient_id,
    token_id,
    nft_id,
    serial_number,
    balances_before,
    record_verification,
):
    """
    Verify post-airdrop balances and NFT ownership to confirm successful transfer.
    Uses AccountInfoQuery for robust token association and balance verification.
    Accepts a `balances_before` mapping with keys 'sender' and 'recipient'.
    Returns (fully_verified_bool, details_dict)
    """
    sender_balances_before = balances_before.get("sender", {})
    recipient_balances_before = balances_before.get("recipient", {})

    details = {
        "sender_balances_before": sender_balances_before,
        "recipient_balances_before": recipient_balances_before,
        "sender_balances_after": None,
        "recipient_balances_after": None,
        "nft_owner": None,
        "owner_matches": False,
        "record_checks": record_verification,
    }

    # Get current account info and balances using AccountInfoQuery (more robust)
    try:
        sender_info = AccountInfoQuery(account_id=operator_id).execute(client)
        sender_current = {rel.token_id: rel.balance for rel in sender_info.token_relationships}
    except Exception as e:
        details["error"] = f"Error fetching sender account info: {e}"
        details["fully_verified"] = False
        return False, details

    try:
        recipient_info = AccountInfoQuery(account_id=recipient_id).execute(client)
        recipient_current = {rel.token_id: rel.balance for rel in recipient_info.token_relationships}
    except Exception as e:
        details["error"] = f"Error fetching recipient account info: {e}"
        details["fully_verified"] = False
        return False, details

    details["sender_balances_after"] = sender_current
    details["recipient_balances_after"] = recipient_current

    sender_nft_before = sender_balances_before.get(nft_id, 0)
    sender_nft_after = sender_current.get(nft_id, 0)
    recipient_nft_before = recipient_balances_before.get(nft_id, 0)
    recipient_nft_after = recipient_current.get(nft_id, 0)

    print(f"\n  - NFT balance changes: sender {sender_nft_before} -> {sender_nft_after}, recipient {recipient_nft_before} -> {recipient_nft_after}")

    # Query NFT info for the serial to confirm ownership (optional)
    nft_serial_id = NftId(token_id=nft_id, serial_number=serial_number)
    try:
        nft_info = TokenNftInfoQuery(nft_id=nft_serial_id).execute(client)
        nft_owner = getattr(nft_info, "account_id", None)
    except Exception as e:
        nft_owner = None
        print(f"    Error querying NFT info: {e}")

    details["nft_owner"] = nft_owner
    details["owner_matches"] = nft_owner == recipient_id

    # Combine checks in a single boolean expression
    fully_verified = (
        record_verification.get("nft_transfer_confirmed", False)
        and record_verification.get("expected_token_transfer", False)
        and (sender_nft_after < sender_nft_before)
        and (recipient_nft_after > recipient_nft_before)
        and details["owner_matches"]
    )

    details["fully_verified"] = fully_verified
    return fully_verified, details


def _log_balances_before(client, operator_id, recipient_id, token_id, nft_id):
    """Fetch and print sender/recipient token balances and associations before airdrop."""
    print("\nStep 5: Checking balances and associations before airdrop...")
    
    # Get account info to verify associations
    sender_info = AccountInfoQuery(account_id=operator_id).execute(client)
    recipient_info = AccountInfoQuery(account_id=recipient_id).execute(client)
    
    # Build dictionaries for balances from token_relationships (more robust than balance query)
    sender_balances_before = {rel.token_id: rel.balance for rel in sender_info.token_relationships}
    recipient_balances_before = {rel.token_id: rel.balance for rel in recipient_info.token_relationships}
    
    print(f"Sender ({operator_id}) balances before airdrop:")
    print(f"  {token_id}: {sender_balances_before.get(token_id, 0)}")
    print(f"  {nft_id}: {sender_balances_before.get(nft_id, 0)}")
    print(f"Recipient ({recipient_id}) balances before airdrop:")
    print(f"  {token_id}: {recipient_balances_before.get(token_id, 0)}")
    print(f"  {nft_id}: {recipient_balances_before.get(nft_id, 0)}")
    
    return sender_balances_before, recipient_balances_before


def _print_verification_summary(record_result, verification_details, operator_id, recipient_id, nft_id, serial_number):
    """Print a concise verification summary based on results."""
    print(f"  - Token transfer verification (fungible): {'OK' if record_result.get('expected_token_transfer') else 'MISSING'}")
    print(f"  - NFT transfer seen in record: {'OK' if record_result.get('nft_transfer_confirmed') else 'MISSING'}")
    print(f"  - NFT owner according to TokenNftInfoQuery: {verification_details.get('nft_owner')}")
    print(f"  - NFT owner matches recipient: {'YES' if verification_details.get('owner_matches') else 'NO'}")

    if verification_details.get('fully_verified'):
        print(f"\n  ✅ Success! NFT {nft_id} serial #{serial_number} was transferred from {operator_id} to {recipient_id} and verified by record + balances + TokenNftInfoQuery")
    else:
        print(f"\n  ⚠️ Warning: Could not fully verify NFT {nft_id} serial #{serial_number}. Combined checks result: {verification_details.get('fully_verified')}")


def _print_final_summary(client, operator_id, recipient_id, token_id, nft_id, serial_number, verification_details):
    """Print final balances after airdrop and a small summary table."""
    # Use AccountInfoQuery for accurate balance retrieval if not already cached
    if verification_details.get("sender_balances_after") is None:
        sender_info = AccountInfoQuery(account_id=operator_id).execute(client)
        sender_balances_after = {rel.token_id: rel.balance for rel in sender_info.token_relationships}
    else:
        sender_balances_after = verification_details.get("sender_balances_after")
    
    if verification_details.get("recipient_balances_after") is None:
        recipient_info = AccountInfoQuery(account_id=recipient_id).execute(client)
        recipient_balances_after = {rel.token_id: rel.balance for rel in recipient_info.token_relationships}
    else:
        recipient_balances_after = verification_details.get("recipient_balances_after")

    print("\nBalances after airdrop:")
    print(f"Sender ({operator_id}):")
    print(f"  {token_id}: {sender_balances_after.get(token_id, 0)}")
    print(f"  {nft_id}: {sender_balances_after.get(nft_id, 0)}")
    print(f"Recipient ({recipient_id}):")
    print(f"  {token_id}: {recipient_balances_after.get(token_id, 0)}")
    print(f"  {nft_id}: {recipient_balances_after.get(nft_id, 0)}")

    print("\nSummary Table:")
    print("+----------------+----------------------+----------------------+----------------------+----------------------+")
    print("| Token Type     | Token ID             | NFT Serial          | Sender Balance       | Recipient Balance    |")
    print("+----------------+----------------------+----------------------+----------------------+----------------------+")
    print(f"| Fungible (TKA) | {str(token_id):20} | {'N/A':20} | {str(sender_balances_after.get(token_id, 0)):20} | {str(recipient_balances_after.get(token_id, 0)):20} |")
    print(f"| NFT (NFTA)     | {str(nft_id):20} | #{str(serial_number):19} | {str(sender_balances_after.get(nft_id, 0)):20} | {str(recipient_balances_after.get(nft_id, 0)):20} |")
    print("+----------------+----------------------+----------------------+----------------------+----------------------+")
    print("\n✅ Finished token airdrop example (see summary above).")


def token_airdrop():
    """
    A full example that creates an account, a token, associate token, and 
    finally perform token airdrop.
    """
    # Setup Client
    client, operator_id, operator_key = setup_client()

    # Create a new account
    recipient_key, recipient_id = create_account(client, operator_key)

    # Create a tokens
    token_id = create_token(client, operator_id, operator_key)

    # Create a nft
    nft_id = create_nft(client, operator_key, operator_id)

    #Mint nft
    serial_number = mint_nft(client, operator_key, nft_id)

    # Associate tokens
    associate_tokens(client, recipient_id, recipient_key, [token_id, nft_id])

    # Fetch and print balances before airdrop
    sender_balances_before, recipient_balances_before = _log_balances_before(
        client, operator_id, recipient_id, token_id, nft_id
    )

    # Airdrop the tokens (separated into its own function)
    airdrop_receipt = airdrop_tokens(
        client, operator_id, operator_key, recipient_id, token_id, nft_id, serial_number
    )

    # 1) Verify record contents (token transfers and nft transfers)
    record_result = verify_transaction_record(
        client, airdrop_receipt, operator_id, recipient_id, token_id, nft_id, serial_number
    )

    # 2) Verify post-airdrop balances and nft ownership
    balances_before = {"sender": sender_balances_before, "recipient": recipient_balances_before}
    fully_verified, verification_details = verify_post_airdrop_balances(
        client,
        operator_id,
        recipient_id,
        token_id,
        nft_id,
        serial_number,
        balances_before,
        record_result,
    )

    # Print condensed verification summary and final table
    _print_verification_summary(record_result, verification_details, operator_id, recipient_id, nft_id, serial_number)
    _print_final_summary(client, operator_id, recipient_id, token_id, nft_id, serial_number, verification_details)


if __name__ == "__main__":
    token_airdrop()
