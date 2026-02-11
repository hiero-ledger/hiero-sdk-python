"""
Demonstrate creating, executing, and retrieving an account creation transaction
without immediately waiting for the receipt.

uv run examples/transaction/transaction_without_wait_for_receipt.py
python examples/transaction/transaction_without_wait_for_receipt.py
"""

import sys

from hiero_sdk_python import Client, AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode


def build_transaction() -> AccountCreateTransaction:
    """
    Build a new AccountCreateTransaction with a generated private key
    and a minimal initial balance.
    """
    key = PrivateKey.generate()
    return AccountCreateTransaction().set_key_without_alias(key).set_initial_balance(1)


def main():
    """
    1. Initialize a client from environment variables (operator required in env).
    2. Build an AccountCreateTransaction.
    3. Execute the transaction asynchronously (without waiting for receipt).
    4. Retrieve the receipt and record after execution.
    """
    try:
        client = Client.from_env()
        tx = build_transaction()

        # Execute the transaction without waiting for receipt immediately
        response = tx.execute(client, wait_for_receipt=False)
        
        print("Transaction executed successfully!")
        print(f"Transaction submitted with ID: {response.transaction_id}")

        # Retrieve receipt and record after submission
        receipt = response.get_receipt(client)
        print(f"Receipt status: {ResponseCode(receipt.status).name}")
  
        
        record = response.get_record(client)
        print("Record:", record)

    except Exception as exc:
        print(f"Error during transaction execution: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
