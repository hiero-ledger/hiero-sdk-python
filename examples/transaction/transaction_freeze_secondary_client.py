"""
Demonstrate Manually freezing using secondary client, serializing, deserializing, signing,
and executing a Hedera transaction using hiero_sdk_python.

uv run examples/transaction/transaction_freeze_secondary_client.py
python examples/transaction/transaction_freeze_secondary_client.py 
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    TransactionId,
    Client,
    Network,
    Transaction,
    AccountCreateTransaction,
    ResponseCode
)


load_dotenv()

NETWORK_NAME = os.getenv("NETWORK", "testnet").lower()
OPERATOR_ID = os.getenv("OPERATOR_ID")
OPERATOR_KEY = os.getenv("OPERATOR_KEY")


def setup_client():
    """
    Initialize and return the primary Hedera client using operator credentials.
    """
    if not OPERATOR_ID or not OPERATOR_KEY:
        raise RuntimeError("OPERATOR_ID or OPERATOR_KEY not set in .env")

    print(f"Connecting to Hedera {NETWORK_NAME} network!")

    try:
        client = Client(Network(NETWORK_NAME))

        operator_id = AccountId.from_string(OPERATOR_ID)
        operator_key = PrivateKey.from_string(OPERATOR_KEY)

        client.set_operator(operator_id, operator_key)

    except Exception as exc:
        raise RuntimeError(f"Failed to initialize client: {exc}") from exc

    print(f"Client initialized with operator {client.operator_account_id}")
    return client

def create_secondary_client(executor_client):
    """
    Create a secondary account and client.
    """
    private_key = PrivateKey.generate()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(private_key)
        .freeze_with(executor_client)
        .sign(executor_client.operator_private_key)
        .execute(executor_client)
    )

    account_id = receipt.account_id
    print(f"Secondary account created: {account_id}")

    secondary_client = Client(Network(NETWORK_NAME))
    secondary_client.set_operator(account_id, private_key)

    return secondary_client

def build_unsigned_bytes(executor_client, secondary_client):
    """
    Build a TopicCreateTransaction, manually freeze it using a secondary client,
    and return the serialized unsigned transaction bytes.
    """
    tx_id = TransactionId.generate(executor_client.operator_account_id)

    tx = (
        TopicCreateTransaction()
        .set_memo("Test Topic Creation")
        .set_transaction_id(tx_id)
    )

    # Manually freeze the transaction using the secondary client
    tx.freeze_with(secondary_client)

    unsigned_bytes = tx.to_bytes()
    print(f"Transaction frozen and serialized ({len(unsigned_bytes)} bytes).")

    return unsigned_bytes

def sign_and_execute(unsigned_bytes, executor_client):
    """
    Deserialize a transaction from bytes, sign it using the executor client,
    and execute it on the Hedera network.
    """
    try:
        tx = Transaction.from_bytes(unsigned_bytes)
        print("Transaction deserialized (unsigned).")

        tx.sign(executor_client.operator_private_key)
        print("Transaction signed by executor.")

        receipt = tx.execute(executor_client)
        if receipt.status != ResponseCode.SUCCESS:
            raise RuntimeError(f"Transaction failed with status: {ResponseCode(receipt.status).name}")
        
        print("Transaction executed successfully.")
        print("Receipt:", receipt)

    except Exception as exc:
        raise RuntimeError(f"Transaction execution failed: {exc}") from exc 


def main():
    """
    1. Setup an executor client.
    2. Created secondary client used to manually freeze a transaction.
    3. Create a Transaction and explicitly:
        - Set the TransactionId
        - Call `freezeWith()` to build the TransactionBody for the specified node with secondary client
        - Serialize the unsigned transaction to bytes
    4. Deserialize the transaction from bytes, sign it, and execute it on the network.
    """
    try:
        executor_client = setup_client()
        secondary_client = create_secondary_client(executor_client)

        unsigned_bytes = build_unsigned_bytes(
            executor_client,
            secondary_client,
        )

        sign_and_execute(unsigned_bytes, executor_client)

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
