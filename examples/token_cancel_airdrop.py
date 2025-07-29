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


def token_cancel_airdrop():
    """
    A full example that creates an account, two tokens, perform airdrop,
    and finally cancel the airdrop.
    """
    # Config Client
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
    except (TypeError, ValueError):
        print("Error: Creating client, Please check your .env file")
        sys.exit(1)

    # Create a new account.
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
        print(f"Created a new account with ID: {recipient_id}")
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)

    # Create two new tokens.
    print("\nCreating two new tokens...")
    try:
        tx1 = TokenCreateTransaction().set_token_name("First Token").set_token_symbol("TKA").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt1 = tx1.freeze_with(client).sign(operator_key).execute(client)
        token_id_1 = receipt1.tokenId

        tx2 = TokenCreateTransaction().set_token_name("Second Token").set_token_symbol("TKB").set_initial_supply(1).set_treasury_account_id(operator_id)
        receipt2 = tx2.freeze_with(client).sign(operator_key).execute(client)
        token_id_2 = receipt2.tokenId

        print(f"Created tokens: {token_id_1} and {token_id_2}")
    except Exception as e:
        print(f"Error creating tokens: {e}")
        sys.exit(1)

    # Airdrop the tokens.
    print("\nAirdrop tokens...")
    try:
        receipt = (
            TokenAirdropTransaction()
            .add_approved_token_transfer(token_id=token_id_1, account_id=operator_id, amount=-1)
            .add_approved_token_transfer(token_id=token_id_1, account_id=recipient_id, amount=1)
            .add_approved_token_transfer(token_id=token_id_2, account_id=operator_id, amount=-1)
            .add_approved_token_transfer(token_id=token_id_2, account_id=recipient_id, amount=1)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        print(f"Token airdrop complete: (status: {receipt.status}, transaction_id: {receipt.transaction_id})")
        airdrop_record = TransactionRecordQuery(receipt.transaction_id()).execute(client)
        pending_airdrops_record = airdrop_record.new_pending_airdrops
    except Exception as e:
        print(f"Error airdroping tokens: {e}")
        sys.exit(1)

    # Cancel the airdrop
    print("\nCancel airdrop...")
    try:
        cancel_airdrop_tx = TokenCancelAirdropTransaction()
        for record in pending_airdrops_record:
            cancel_airdrop_tx.add_pending_airdrop(record.pending_airdrop_id)

        cancel_airdrop_tx.freeze_with(client)
        cancel_airdrop_tx.sign(operator_key)
        cancel_airdrop_recipt = cancel_airdrop_tx.execute(client)

        if (cancel_airdrop_recipt.status != ResponseCode.SUCCESS):
            print(f"Fail to cancel airdrop: Status: {cancel_airdrop_recipt.status}")
            sys.exit(1)

        print(f"Airdrop cancel transaction successfull")
    except Exception as e:
        print(f"Error executing cancel airdrop token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    token_cancel_airdrop()