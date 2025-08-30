"""
uv run examples/transfer_hbar.py
"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
    AccountCreateTransaction,
    Hbar,
    CryptoGetAccountBalanceQuery
)

load_dotenv()

def setup_client():
    """Initialize and set up the client with operator account"""
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)


def create_account(client, operator_key):
    """Create a new recipient account"""
    print("\nSTEP 1: Creating a new recipient account...")
    recipient_key = PrivateKey.generate()
    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
        return recipient_id, recipient_key
    
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)

def transfer_hbar():
    """
    A full example to create a new recipent account and transfer hbar to that account
    """
    # Config Client
    client, operator_id, operator_key = setup_client()

    # Create a new recipient account.
    recipient_id, _ = create_account(client, operator_key)

    # Transfer HBAR
    print("\nSTEP 2: Transfering HBAR...")

    try:
        # Check balance before HBAR transfer
        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .hbars
        )
        print(f"Recipient account balance before transfer: {balance_before} hbars")

        transfer_tx = (
            TransferTransaction()
            .add_hbar_transfer(operator_id, -100000000)  # send 1 HBAR in tinybars
            .add_hbar_transfer(recipient_id, 100000000)
            .freeze_with(client)
        )
        transfer_tx.execute(client)
        
        print("\n✅ Success! HBAR transfer successful.\n")

        # Check balance after HBAR transfer
        balance_after = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .hbars
        )
        print(f"Recipient account balance after transfer: {balance_after} hbars")
    except Exception as e:
        print(f"❌ HBAR transfer failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transfer_hbar()
