"""
uv run examples/transfer_token.py
python examples/transfer_token.py

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
    TokenAssociateTransaction
)
from hiero_sdk_python.tokens.token_transfer import TokenTransfer

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

def transfer_tokens():
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

    # Transfer Token
    print("\nSTEP 4: Transfering Token...")
    try:
        # Check balance before transfer
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
        
        print("\n✅ Success! Token transfer complete.\n")

        # Check balance after transfer
        balance_after = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        print("Token balance after token transfer:")
        print(f"{token_id}: {balance_after.get(token_id)}")
        
        # Demonstrate TokenTransfer __repr__ method
        print("\n" + "="*70)
        print("BONUS: Demonstrating TokenTransfer __repr__ method")
        print("="*70)
        print("\nThe TokenTransfer class now has a __repr__ method for better debugging.")
        print("This provides an unambiguous representation of the object.\n")
        
        # Create a sample TokenTransfer object
        sample_transfer = TokenTransfer(
            token_id=token_id,
            account_id=recipient_id,
            amount=1,
            expected_decimals=None,
            is_approved=False
        )
        
        print("Using str() - Human-readable format:")
        print(f"  {str(sample_transfer)}\n")
        
        print("Using repr() - Unambiguous format for debugging:")
        print(f"  {repr(sample_transfer)}\n")
        
        print("The repr() format uses !r to show exact object representations,")
        print("which is helpful when debugging or logging transfer details.")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error transferring token: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transfer_tokens()
