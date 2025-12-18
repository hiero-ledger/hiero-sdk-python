"""
uv run examples/transaction/transfer_transaction_fungible.py
python examples/transaction/transfer_transaction_fungible.py

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
    TokenCreateTransaction,
    CryptoGetAccountBalanceQuery,
    TokenAssociateTransaction,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


# --------------------------
#  CLIENT SETUP
# --------------------------
def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")

        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Error: Creating client, Please check your .env file")
        sys.exit(1)


# --------------------------
#  ACCOUNT CREATION
# --------------------------
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


# --------------------------
#  TOKEN CREATION
# --------------------------
def create_token(client, operator_id, operator_key):
    print("\nSTEP 2: Creating a new token...")
    try:
        token_tx = (
            TokenCreateTransaction()
            .set_token_name("First Token")
            .set_token_symbol("TKA")
            .set_initial_supply(1)
            .set_treasury_account_id(operator_id)
            .freeze_with(client)
            .sign(operator_key)
        )
        token_receipt = token_tx.execute(client)
        token_id = token_receipt.token_id

        print(f"✅ Success! Created a token with Token ID: {token_id}")
        return token_id
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)


# --------------------------
#  TOKEN ASSOCIATION
# --------------------------
def associate_token(client, recipient_id, recipient_key, token_id):
    print("\nSTEP 3: Associating Token...")
    try:
        association_tx = (
            TokenAssociateTransaction(account_id=recipient_id, token_ids=[token_id])
            .freeze_with(client)
            .sign(recipient_key)
        )
        association_tx.execute(client)

        print("✅ Success! Token association complete.")
    except Exception as e:
        print(f"❌ Error associating token: {e}")
        sys.exit(1)


# --------------------------
#  ACCOUNT BALANCE QUERY
# --------------------------
def account_balance_query(client, account_id):
    """Query and return token balances for an account."""
    try:
        result = CryptoGetAccountBalanceQuery(account_id=account_id).execute(client)
        return result.token_balances
    except Exception as e:
        print(f"❌ Error fetching account balance: {e}")
        sys.exit(1)


# --------------------------
#  TRANSFER TRANSACTION
# --------------------------
def transfer_transaction(client, operator_id, operator_key, recipient_id, token_id):
    """Execute a token transfer transaction."""
    print("\nSTEP 4: Transfering Token...")
    try:
        tx = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, -1)
            .add_token_transfer(token_id, recipient_id, 1)
            .freeze_with(client)
            .sign(operator_key)
        )

        tx.execute(client)
        print("✅ Success! Token transfer complete.\n")

    except Exception as e:
        print(f"❌ Error transferring token: {e}")
        sys.exit(1)


# --------------------------
#  MAIN ORCHESTRATOR (RENAMED)
# --------------------------
def main():
    """
    A full example to create a new recipent account, a fungible token, and
    transfer the token to that account
    """
    # Config Client
    client, operator_id, operator_key = setup_client()

    # Create a new recipient account.
    recipient_id, recipient_key = create_account(client, operator_key)

    # Create new tokens.
    token_id = create_token(client, operator_id, operator_key)

    # Associate Token
    associate_token(client, recipient_id, recipient_key, token_id)

    # Balance before transfer
    balance_before = account_balance_query(client, recipient_id)
    print("Token balance BEFORE transfer:")
    print(f"{token_id}: {balance_before.get(token_id)}")

    # Transfer
    transfer_transaction(client, operator_id, operator_key, recipient_id, token_id)

    # Balance after transfer
    balance_after = account_balance_query(client, recipient_id)
    print("Token balance AFTER transfer:")
    print(f"{token_id}: {balance_after.get(token_id)}")


if __name__ == "__main__":
    main()
