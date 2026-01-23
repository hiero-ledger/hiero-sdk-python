"""
Demonstrates how to manually freeze, serialize, deserialize, 
sign, and execute a transaction using hiero_sdk_python.

uv run examples/transaction/transaction_freeze_manually.py
python examples/transaction/transaction_freeze_manually.py
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
    ResponseCode
)

load_dotenv()

NETWORK_NAME = os.getenv("NETWORK", "testnet").lower()
OPERATOR_ID = os.getenv("OPERATOR_ID")
OPERATOR_KEY = os.getenv("OPERATOR_KEY")
NODE_ACCOUNT_ID = AccountId.from_string("0.0.3")

def setup_client():
    """
    Initialize and return a Hedera Client using operator credentials.
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

def build_unsigned_tx(executor_client):
    """
    Build a Transaction, manually freeze it for a specific node, and return serialized unsigned bytes.
    """
    tx_id = TransactionId.generate(executor_client.operator_account_id)

    tx = (
        TopicCreateTransaction()
        .set_memo("Test Topic Creation")
        .set_transaction_id(tx_id)
    )

    # Explicit node binding (important for deterministic freeze)
    tx.node_account_id = NODE_ACCOUNT_ID

    # Freeze generates a body for ONLY the specified node
    tx.freeze()

    print(f"Transaction frozen for node {NODE_ACCOUNT_ID}")
    return tx.to_bytes()

def sign_and_execute(unsigned_bytes, executor_client):
    """
    Deserialize, sign, and execute a transaction.
    """
    try:
        # Deserialize
        tx = Transaction.from_bytes(unsigned_bytes)
        print("Transaction deserialized (unsigned).")

        # Sign with executor client private key
        tx.sign(executor_client.operator_private_key)
        print("Transaction signed.")

        receipt = tx.execute(executor_client)

        if receipt.status != ResponseCode.SUCCESS:
            raise RuntimeError(f"Transaction failed with status: {ResponseCode(receipt.status).name}")

        print("Transaction executed successfully.")
        print("Receipt:", receipt)
    
    except Exception as exc:
        raise RuntimeError(f"Transaction execution failed: {exc}") from exc 

def main():
    """
    1. Set up a client.
    2. Create a Transaction and explicitly:
        - Set the TransactionId
        - Set the NodeAccountId (e.g. 0.0.3)
        - Call `freeze()` to build the TransactionBody for the specified node
        - Serialize the unsigned transaction to bytes
    3. Deserialize the transaction from bytes, sign it, and execute it on the network.
    """
    try:
        client = setup_client()
        unsigned_bytes = build_unsigned_tx(client)
        sign_and_execute(unsigned_bytes, client)

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
