"""
uv run examples/token_cancel_airdrop.py
python examples/token_cancel_airdrop.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    Network,
    PrivateKey,
    AccountCreateTransaction,
    Hbar,
    TokenCreateTransaction,
    TokenAirdropTransaction,
    TransactionRecordQuery,
    TokenCancelAirdropTransaction,
    ResponseCode
)

# Load environment variables from .env file
load_dotenv()


def setup_client():
    """Initialize the Hedera client using environment variables."""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))
    
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("Error: Creating client, Please check your .env file")
        sys.exit(1)


def create_account(client, operator_key, initial_balance=Hbar.from_tinybars(100_000_000)):
    """Create a new account with the given initial balance."""
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate("ed25519")
    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(initial_balance)
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"Created a new account with ID: {recipient_id}")
        return recipient_id, recipient_key
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def create_token(client, operator_id, operator_key, token_name, token_symbol, initial_supply=1):
    """Create a new token and return its token ID."""
    print(f"\nCreating token: {token_name} ({token_symbol})...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name(token_name)
            .set_token_symbol(token_symbol)
            .set_initial_supply(initial_supply)
            .set_treasury_account_id(operator_id)
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        token_id = receipt.token_id
        print(f"Created token {token_name} with ID: {token_id}")
        return token_id
    # Create two new tokens.
    print("\nStep 1: Creating two new fungible tokens...")
    try:
        tx1 = TokenCreateTransaction().set_token_name("First Token").set_token_symbol("TKA").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt1 = tx1.freeze_with(client).sign(operator_key).execute(client)
        token_id_1 = receipt1.token_id

        tx2 = TokenCreateTransaction().set_token_name("Second Token").set_token_symbol("TKB").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt2 = tx2.freeze_with(client).sign(operator_key).execute(client)
        token_id_2 = receipt2.token_id

        print(f"✅ Created tokens: {token_id_1} (TKA) and {token_id_2} (TKB)")
    except Exception as e:
        print(f"Error creating token {token_name}: {e}")
        sys.exit(1)

    # Log balances before airdrop
    print("\nStep 2: Checking balances before airdrop...")
    from hiero_sdk_python import CryptoGetAccountBalanceQuery
    sender_balances_before = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client).token_balances

    recipient_balances_before = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client).token_balances
    print(f"Sender ({operator_id}) balances before airdrop:")

    print(f"  {str(token_id_1)}: {sender_balances_before.get(str(token_id_1), 0)}")

    print(f"  {str(token_id_2)}: {sender_balances_before.get(str(token_id_2), 0)}")

    print(f"Recipient ({recipient_id}) balances before airdrop:")

    print(f"  {str(token_id_1)}: {recipient_balances_before.get(str(token_id_1), 0)}")

    print(f"  {str(token_id_2)}: {recipient_balances_before.get(str(token_id_2), 0)}")

def airdrop_tokens(client, operator_id, operator_key, recipient_id, token_ids):
    """Airdrop the provided tokens to a recipient account."""
    print(f"\nStep 3: Airdroppingping tokens TKA ({token_id_1}) and TKB ({token_id_2}) to recipient {recipient_id}...")

    try:
        tx = TokenAirdropTransaction()
        for token_id in token_ids:
            tx.add_token_transfer(token_id=token_id, account_id=operator_id, amount=-1)
            tx.add_token_transfer(token_id=token_id, account_id=recipient_id, amount=1)

        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        print(f"Token airdrop complete: (status: {receipt.status}, transaction_id: {receipt.transaction_id})")

        airdrop_record = TransactionRecordQuery(receipt.transaction_id).execute(client)
        return airdrop_record.new_pending_airdrops
        # Log balances after airdrop
        sender_balances_after = CryptoGetAccountBalanceQuery(account_id=operator_id).execute(client).token_balances

        recipient_balances_after = CryptoGetAccountBalanceQuery(account_id=recipient_id).execute(client).token_balances

        print("\nBalances after airdrop:")

        print(f"Sender ({operator_id}):")

        print(f"  {str(token_id_1)}: {sender_balances_after.get(str(token_id_1), 0)}")

        print(f"  {str(token_id_2)}: {sender_balances_after.get(str(token_id_2), 0)}")

        print(f"Recipient ({recipient_id}):")

        print(f"  {str(token_id_1)}: {recipient_balances_after.get(str(token_id_1), 0)}")

        print(f"  {str(token_id_2)}: {recipient_balances_after.get(str(token_id_2), 0)}")



        # Summary table

        print("\nSummary Table:")

        print("+----------------+----------------------+----------------------+----------------------+\n"

              "| Token Symbol   | Token ID             | Sender Balance       | Recipient Balance    |\n"

              "+----------------+----------------------+----------------------+----------------------+")

        print(f"| TKA            | {str(token_id_1):<20} | {str(sender_balances_after.get(str(token_id_1), 0)):<20} | {str(recipient_balances_after.get(str(token_id_1), 0)):<20} |")

        print(f"| TKB            | {str(token_id_2):<20} | {str(sender_balances_after.get(str(token_id_2), 0)):<20} | {str(recipient_balances_after.get(str(token_id_2), 0)):<20} |")

        print("+----------------+----------------------+----------------------+----------------------+")

    except Exception as e:
        print(f"Error airdropping tokens: {e}")
        sys.exit(1)


def cancel_airdrops(client, operator_key, pending_airdrops):
    """Cancel all pending airdrops."""
    print("\nCanceling airdrops...")
    try:
        cancel_airdrop_tx = TokenCancelAirdropTransaction()
        for record in pending_airdrops:
            cancel_airdrop_tx.add_pending_airdrop(record.pending_airdrop_id)

        cancel_airdrop_tx.freeze_with(client).sign(operator_key)
        cancel_airdrop_receipt = cancel_airdrop_tx.execute(client)

        if cancel_airdrop_receipt.status != ResponseCode.SUCCESS:
            print(f"Failed to cancel airdrop: Status: {cancel_airdrop_receipt.status}")
            sys.exit(1)

        print("Airdrop cancel transaction successful")
    except Exception as e:
        print(f"Error executing cancel airdrop token: {e}")
        sys.exit(1)


def token_cancel_airdrop():
    client, operator_id, operator_key = setup_client()
    recipient_id, _ = create_account(client, operator_key)

    # Create two tokens
    token_id_1 = create_token(client, operator_id, operator_key, "First Token", "TKA")
    token_id_2 = create_token(client, operator_id, operator_key, "Second Token", "TKB")

    # Airdrop tokens
    pending_airdrops = airdrop_tokens(client, operator_id, operator_key, recipient_id, [token_id_1, token_id_2])

    # Cancel airdrops
    cancel_airdrops(client, operator_key, pending_airdrops)


if __name__ == "__main__":
    token_cancel_airdrop()
