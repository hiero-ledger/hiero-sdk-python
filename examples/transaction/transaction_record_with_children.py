import os
from hiero_sdk_python.client import Client
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery

def main():
    # Setup client
    client = Client.for_testnet()
    # ... (add operator credentials) ...

    # 1. Execute a transaction that is likely to have child records
    # (e.g., a complex Smart Contract call)
    print("Executing transaction...")
    
    # 2. Query the record and explicitly request children
    tx_id = "..." # your transaction id
    
    query = (
        TransactionRecordQuery()
        .set_transaction_id(tx_id)
        .set_include_children(True) # The new feature!
    )
    
    record = query.execute(client)
    
    # 3. Demonstrate accessing the children
    print(f"Parent Transaction ID: {record.transaction_id}")
    print(f"Number of child records found: {len(record.children)}")
    
    for i, child in enumerate(record.children):
        print(f"Child {i+1} Status: {child.receipt.status}")

if __name__ == "__main__":
    main()