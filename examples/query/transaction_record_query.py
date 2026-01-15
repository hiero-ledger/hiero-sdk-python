"""
uv run examples/query/transaction_record_query.py
python examples/query/transaction_record_query.py
"""

import sys

from hiero_sdk_python import (
    AccountCreateTransaction,
    Client,
    Hbar,
    ResponseCode,
    TokenAssociateTransaction,
    TokenCreateTransaction,
    TokenType,
    SupplyType,
    TransactionRecordQuery,
    TransferTransaction,
)


def setup_client():
    """Initialize and set up the client with operator account using env vars."""
    client = Client.from_env()
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_account_transaction(client):
    """Create a new account"""
    # Derive public key from private key
    transaction = (
        AccountCreateTransaction()
        .set_key_without_alias(client.operator_private_key.public_key())
        .set_initial_balance(Hbar(1))
        .freeze_with(client)
    )

   
    tx_response = transaction.sign(client.operator_private_key).execute(client)

    # FIX: Check status before proceeding
    if tx_response.status != ResponseCode.SUCCESS:
        print(
            f"Account creation failed with status: {ResponseCode(tx_response.status).name}"
        )
        sys.exit(1)

    # Get the account ID
    new_account_id = tx_response.account_id

    print(f"The new account ID is {new_account_id}")
    return new_account_id


def create_fungible_token(client):
    """Create a fungible token"""
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(100)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    token_id = receipt.token_id
    print(f"\nFungible token created with ID: {token_id}")

    return token_id


def associate_token(client, account_id, token_id):
    """Associate token with account"""
    transaction = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .set_token_ids([token_id])
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    tx_response = transaction.execute(client)
    receipt = tx_response

    if receipt.status != ResponseCode.SUCCESS:
        print(
            f"Token association failed with status: {ResponseCode(receipt.status).name}"
        )
        sys.exit(1)

    print(f"Associated account {account_id} with token {token_id}")


def transfer_tokens(client, token_id, sender_id, receiver_id, amount):
    """Transfer tokens between accounts"""
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, sender_id, -amount)
        .add_token_transfer(token_id, receiver_id, amount)
        .freeze_with(client)
        .sign(client.operator_private_key)
    )

    tx_response = transaction.execute(client)
    receipt = tx_response

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token transfer failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Transferred {amount} tokens from {sender_id} to {receiver_id}")
    return tx_response.transaction_id


def query_record(client, transaction_id):
    """Query the record of a transaction"""
    record = TransactionRecordQuery().set_transaction_id(transaction_id).execute(client)

    print(f"\nRecord for transaction {transaction_id}:")
    print(f"Receipt status: {ResponseCode(record.receipt.status).name}")
    print(f"Transaction hash: {record.transaction_hash}")
    print(f"Consensus timestamp: {record.consensus_timestamp}")
    print(f"Transaction fee: {record.transaction_fee}")


def main():
    client = setup_client()

    # Create an account
    new_account_id = create_account_transaction(client)

    # Create a token
    token_id = create_fungible_token(client)

    # Associate the token with the new account
    associate_token(client, new_account_id, token_id)

    # Transfer tokens to the new account
    transaction_id = transfer_tokens(
        client, token_id, client.operator_account_id, new_account_id, 10
    )

    # Query the record of the transfer transaction
    query_record(client, transaction_id)


if __name__ == "__main__":
    main()