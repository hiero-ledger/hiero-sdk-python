import os
from dotenv import load_dotenv
from hiero_sdk_python import (
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    TransactionId,
    Client,
    Network,
    Transaction,
)

# Setup
load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()

executor_id: AccountId = AccountId.from_string(os.getenv("OPERATOR_ID"))
executor_key: PrivateKey = PrivateKey.from_string(os.getenv("OPERATOR_KEY"))

# Create the client that will eventually execute the transaction
executor_client: Client = Client(Network(network=network_name))
executor_client.set_operator(executor_id, executor_key)

# 1. Create Transaction
tx = TopicCreateTransaction().set_memo("Test Topic Creation")
tx_id = TransactionId.generate(executor_client.operator_account_id)

# 2. Manually set Node and ID
tx.set_transaction_id(tx_id)
tx.node_account_id = AccountId.from_string("0.0.3") # Explicitly set to 0.0.3

# 3. Manual Freeze (Generates body ONLY for 0.0.3)
tx.freeze() 

# 4. Serialize
unsigned_bytes = tx.to_bytes()
print(f"Transaction bytes: {unsigned_bytes.hex()}")

# 5. Deserialize
tx2 = Transaction.from_bytes(unsigned_bytes)
print("Transaction deserialized. Status: Unsigned.")

# 6. Sign
tx2.sign(executor_key)
print("Transaction signed with operator key.")

# 7. Execute
# FAILURE: executor_client selects a node other than 0.0.3 (e.g. 0.0.4 or 0.0.8)
receipt = tx2.execute(executor_client) 
print(receipt)