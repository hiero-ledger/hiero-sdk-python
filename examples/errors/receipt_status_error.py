#!/usr/bin/env python3
"""
Example demonstrating how to handle ReceiptStatusError in the Hiero SDK.
"""
import os
import sys

# Add the parent directory to the path so we can import the SDK
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TransferTransaction,
    Hbar,
    ResponseCode,
    ReceiptStatusError
)

def main():
    # Initialize the client
    # For this example, we assume we are running against a local node or testnet
    # You would typically load these from environment variables
    operator_id_str = os.environ.get("OPERATOR_ID", "0.0.2")
    operator_key_str = os.environ.get("OPERATOR_KEY", "302e020100300506032b65700422042091132178e72057a1d7528025956fe39b0b847f200ab59b2fdd367017f3087137")
    
    try:
        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)
    except Exception as e:
        print(f"Error parsing operator credentials: {e}")
        return

    client = Client()
    client.set_operator(operator_id, operator_key)

    # Create a transfer transaction that is likely to fail post-consensus
    # For example, transferring to an invalid account or insufficient balance
    # Here we try to transfer a huge amount that we likely don't have
    
    recipient_id = AccountId.from_string("0.0.3")
    huge_amount = Hbar.from_tinybars(100_000_000_000_000) # Very large amount

    print("Creating transaction...")
    tx = TransferTransaction() \
        .add_hbar_transfer(operator_id, huge_amount.negated()) \
        .add_hbar_transfer(recipient_id, huge_amount) \
        .set_transaction_memo("ReceiptStatusError Example")

    try:
        print("Executing transaction...")
        # execute() submits the transaction to the network
        # It might raise PrecheckError if the transaction is malformed
        response = tx.execute(client)
        
        print(f"Transaction submitted. ID: {response.transaction_id}")
        
        # get_receipt() waits for consensus
        # This is where ReceiptStatusError is typically raised if the status is not SUCCESS
        # However, the SDK might not auto-raise it depending on configuration or method used.
        # Let's check manually as per the guide.
        
        receipt = response.get_receipt(client)
        
        # Explicit check (though get_receipt usually throws if configured, let's be explicit)
        if receipt.status != ResponseCode.SUCCESS:
             raise ReceiptStatusError(receipt.status, response.transaction_id, receipt)
             
        print("Transaction successful!")

    except ReceiptStatusError as e:
        print("\nCaught ReceiptStatusError!")
        print(f"Status: {e.status} ({ResponseCode(e.status).name})")
        print(f"Transaction ID: {e.transaction_id}")
        print("This error means the transaction reached consensus but failed logic execution.")
        
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
