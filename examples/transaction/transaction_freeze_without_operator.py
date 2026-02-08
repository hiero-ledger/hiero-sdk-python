"""
Demonstrate manually freezing with client having no operator set, 
serializing, signing, and executing a transaction.

uv run examples/transaction/transaction_freeze_without_operator.py
python examples/transaction/transaction_freeze_without_operator.py
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



def create_client_without_operator():
    """
    Create a client without an operator.
    """
    secondary_client = Client(Network(NETWORK_NAME))

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

    # Manually freeze the transaction using the secondary client having no operator
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
    2. Create a secondary client without an operator.
    3. Create a Transaction and explicitly:
        - Set the TransactionId
        - Call `freezeWith()` to build the TransactionBody for the specified node with client without operator
        - Serialize the unsigned transaction to bytes
    4. Deserialize the transaction from bytes, sign it, and execute it on the network.
    """
    try:
        executor_client = setup_client()
        secondary_client = create_client_without_operator()

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
