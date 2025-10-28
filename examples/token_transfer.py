"""
Example: Modularized Token Transfer Script
"""

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_transfer import create_token_transfer, token_transfer_to_proto
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python import Client


# --------------------------
# Hedera Client Setup
# --------------------------
def get_client():
    import os
    operator_id = os.getenv("OPERATOR_ID")
    operator_key = os.getenv("OPERATOR_KEY")
    network = os.getenv("NETWORK", "testnet")
    return Client.for_name(network).set_operator(operator_id, operator_key)


# --------------------------
# Helper Functions
# --------------------------
def account_balance_query(client: Client, account_id: str):
    """
    Query account balance for the given account.
    """
    acc = AccountId.from_string(account_id)
    balance = client.get_account_balance(acc)
    print(f"Account {account_id} balance: {balance}")
    return balance


def transfer_transaction(client: Client, sender_id: str, recipient_id: str, token_id: str, amount: int):
    """
    Transfer tokens from sender to recipient.
    """
    sender = AccountId.from_string(sender_id)
    recipient = AccountId.from_string(recipient_id)
    token = TokenId.from_string(token_id)

    transfer = create_token_transfer(token, recipient, amount)
    proto_transfer = token_transfer_to_proto(transfer)

    tx_response = client.transfer_tokens(sender, proto_transfer)
    print(f"Transfer transaction response: {tx_response}")
    return tx_response


# --------------------------
# Main Function
# --------------------------
def main():
    client = get_client()
    operator_id = os.getenv("OPERATOR_ID")
    recipient_id = os.getenv("RECIPIENT_ID")
    token_id = os.getenv("TOKEN_ID")
    amount = 10  # Example transfer amount

    print("Before transfer:")
    account_balance_query(client, operator_id)
    account_balance_query(client, recipient_id)

    print("\nTransferring tokens...")
    transfer_transaction(client, operator_id, recipient_id, token_id, amount)

    print("\nAfter transfer:")
    account_balance_query(client, operator_id)
    account_balance_query(client, recipient_id)


if __name__ == "__main__":
    main()
