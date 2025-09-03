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

def transfer_hbar():
    """
    A full example to create a new recipent account and transfer hbar to that account
    """
    # Config Client
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)

    # Create a new recipient account.
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate("ed25519")
    try:
        tx = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating new recipient account: {e}")
        sys.exit(1)

    # Check balance before HBAR transfer
    before_balance_query = CryptoGetAccountBalanceQuery().set_account_id(recipient_id)
    before_balance = before_balance_query.execute(client)

    print(f"Recipient account balance before transfer: {before_balance.hbars} hbars")

    # Transfer HBAR
    print("\nTransfering HBAR...")
    transaction = (
        TransferTransaction()
        .add_hbar_transfer(operator_id, -100000000)  # send 1 HBAR in tinybars
        .add_hbar_transfer(recipient_id, 100000000)
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)

        # Check balance after HBAR transfer
        after_balance_query = CryptoGetAccountBalanceQuery().set_account_id(recipient_id)
        after_balance = after_balance_query.execute(client)

        print(f"Recipient account balance after transfer: {after_balance.hbars} hbars")

        print("✅ Success! HBAR transfer successful.")
    except Exception as e:
        print(f"❌ HBAR transfer failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transfer_hbar()
