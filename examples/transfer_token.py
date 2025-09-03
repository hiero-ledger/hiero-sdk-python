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
    TokenAssociateTransaction
)

load_dotenv()

def transfer_tokens():
    """
    A full example to create a new recipent account, a fungible token, and
    transfer the token to that account
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
    print("\nCreating a new recipient account...")
    recipient_key = PrivateKey.generate()
    try:
        account_receipt = (
            AccountCreateTransaction()
            .set_key(recipient_key.public_key())
            .set_initial_balance(Hbar.from_tinybars(100_000_000))
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        recipient_id = account_receipt.account_id
        print(f"✅ Success! Created a new recipient account with ID: {recipient_id}")
    except Exception as e:
        print(f"❌ Error creating new recipient account: {e}")
        sys.exit(1)

    # Create two new tokens.
    print("\nCreating a new tokens...")
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
    except Exception as e:
        print(f"❌ Error creating token: {e}")
        sys.exit(1)

    # Associate Token
    print("\nAssociating Token...")
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

    # Transfer Token
    print("\nTransfering Token...")
    try:
        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Token balance before token transfer:")
        print(f"{token_id}: {balance_before.get(token_id)}")

        transfer_tx = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, -1)
            .add_token_transfer(token_id, recipient_id, 1)
            .freeze_with(client)
            .sign(operator_key)
        )
        transfer_tx.execute(client)

        balance_after = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Token balance after token transfer:")
        print(f"{token_id}: {balance_after.get(token_id)}")

        print("✅ Success! Token transfer complete.")
    except Exception as e:
        print(f"❌ Error transferring token: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transfer_tokens()
