"""
uv run examples/transfer_hbar.py
python examples/transfer_hbar.py

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
network_name = os.getenv('NETWORK', 'testnet').lower()
def setup_client():
    """Initialize and set up the client with operator account"""
    print(f"🌐 Connecting to Hedera {network_name}...")
    client = Client(Network(network_name))

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

def transfer_hbar(client, operator_id, recipient_id):
    """Transfer HBAR from operator account to recipient account"""
    print("\nSTEP 2: Transfering HBAR...")

    try:
        transfer_tx = (
            TransferTransaction()
            .add_hbar_transfer(operator_id, -100000000)  # send 1 HBAR in tinybars
            .add_hbar_transfer(recipient_id, 100000000)
            .freeze_with(client)
        )
        transfer_tx.execute(client)
        
        print("\n✅ Success! HBAR transfer successful.\n")
    except Exception as e:
        print(f"❌ HBAR transfer failed: {str(e)}")
        sys.exit(1)


def account_balance_query(client, account_id, when=""):
    """Query and display account balance"""
    try:
        balance = (
            CryptoGetAccountBalanceQuery(account_id=account_id)
            .execute(client)
            .hbars
        )
        print(f"Recipient account balance{when}: {balance} hbars")
        return balance
    except Exception as e:
        print(f"❌ Balance query failed: {str(e)}")
        sys.exit(1)


def main():
    """
    A full example to create a new recipent account and transfer hbar to that account
    """
    # Config Client
    client, operator_id, operator_key = setup_client()

    # Create a new recipient account.
    recipient_id, _ = create_account(client, operator_key)

    # Check balance before HBAR transfer
    account_balance_query(client, recipient_id, " before transfer")

    # Transfer HBAR
    transfer_hbar(client, operator_id, recipient_id)

    # Check balance after HBAR transfer
    account_balance_query(client, recipient_id, " after transfer")

if __name__ == "__main__":
    main()
