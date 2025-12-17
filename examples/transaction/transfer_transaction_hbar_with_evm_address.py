"""
Transfer HBAR or tokens to a Hedera account using their public-address.

uv run examples/transaction/transfer_transaction_hbar_with_evm_address.py
python examples/transaction/transfer_transaction_hbar_with_evm_address.py

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
    CryptoGetAccountBalanceQuery,
    ResponseCode
)

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()
operator_id_env = os.getenv("OPERATOR_ID")
operator_key_env = os.getenv("OPERATOR_KEY")

def setup_client():
    """Initialize a Hedera client with operator credentials from .env."""
    print(f"Connecting to Hedera {network_name} network...")

    if not operator_id_env or not operator_key_env:
        print("OPERATOR_ID or OPERATOR_KEY not set in .env")
        sys.exit(1)

    network = Network(network_name)
    client = Client(network)

    try:
        operator_id = AccountId.from_string(operator_id_env)
        operator_key = PrivateKey.from_string(operator_key_env)
        
    except Exception:
        print("Invalid OPERATOR_ID or OPERATOR_KEY in .env")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)
    print(f"Client initialized with operator {client.operator_account_id}")
    
    return client


def create_account(client, ecdsa_key):
    """Create a new account using an alias (EVM compatible)."""
    print("\nSTEP 1: Creating a recipient account...")

    try:
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(PrivateKey.generate().public_key())
            .set_alias(ecdsa_key.public_key().to_evm_address())
            .set_initial_balance(Hbar(1))
            .freeze_with(client)
            .sign(client.operator_private_key)
            .sign(ecdsa_key)
        )

        receipt = tx.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(f"Account creation failed: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print(f"Recipient account created: {receipt.account_id}")
        return receipt.account_id

    except Exception as e:
        print(f"Exception during account creation: {e}")
        sys.exit(1)

def transfer_hbar(client, recipient_evm_address):
    """Transfer HBAR using only an EVM address."""
    print("\nSTEP 2: Transferring HBAR using EVM address...")

    try:
        # Set shard and realm to 0 if not known
        recipient_id = AccountId.from_evm_address(recipient_evm_address, 0, 0)

        tx = (
            TransferTransaction()
            .add_hbar_transfer(client.operator_account_id, Hbar(-1).to_tinybars())
            .add_hbar_transfer(recipient_id, Hbar(1).to_tinybars())
            .freeze_with(client)
        )

        tx.execute(client)
        print("HBAR transfer completed successfully!")

    except Exception as e:
        print(f"HBAR transfer failed: {e}")
        sys.exit(1)

def account_balance_query(client, account_id, label = "") -> Hbar:
    """Query and print the HBAR balance of an account."""
    try:
        balance_query = (
            CryptoGetAccountBalanceQuery(account_id=account_id)
            .execute(client)
        )

        balance = balance_query.hbars
        print(f"Balance {label}: {balance} hbars")

        return balance
    except Exception as e:
        print(f"Balance query failed: {e}")
        sys.exit(1)


def main():
    """
    Transfer Hbar to recipient account using EVM Address.:
    1. Create an account using an ECDSA alias (EVM address)
    2. Query its balance
    3. Transfer HBAR using ONLY the EVM address
    4. Query balance again
    """
    client = setup_client()

    # Generate a fresh ECDSA key for alias/EVM address
    ecdsa_key = PrivateKey.generate("ecdsa")
    evm_address = ecdsa_key.public_key().to_evm_address()

    recipient_id = create_account(client, ecdsa_key)

    account_balance_query(client, recipient_id, "before transfer")

    transfer_hbar(client, evm_address)

    account_balance_query(client, recipient_id, "after transfer")

if __name__ == "__main__":
    main()

