"""
uv run examples/query/transaction_record_query.py
python examples/query/transaction_record_query.py
"""

import sys
from hiero_sdk_python import (
    Client,
    Hbar,
    AccountCreateTransaction,
    TransactionRecordQuery,
    ResponseCode,
    TokenCreateTransaction,
    TokenAssociateTransaction,
    TokenType,
    SupplyType,
    TransferTransaction,
    PrivateKey,
)


def create_account_transaction(client):
    """Create a new account to get a transaction ID for record query"""
    new_account_key = PrivateKey.generate_ed25519()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(new_account_key.public_key())
        .set_initial_balance(Hbar(1))
        .freeze_with(client)
        .sign(client.operator_private_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Account created with ID: {receipt.account_id}")
    return receipt.account_id, new_account_key, receipt.transaction_id


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
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Fungible token created with ID: {receipt.token_id}")
    return receipt.token_id


def associate_token(client, token_id, account_id, account_key):
    """Associate token with an account"""
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Token {token_id} associated with account {account_id}")


def transfer_tokens(client, token_id, receiver_id, amount=10):
    """Transfer tokens to the receiver account"""
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key

    receipt = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id, -amount)
        .add_token_transfer(token_id, receiver_id, amount)
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        print(f"Transfer failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    print(f"Transferred {amount} tokens to {receiver_id}")
    return receipt


def print_transaction_record(record):
    """Print transaction record details"""
    print(f"Transaction ID: {record.transaction_id}")
    print(f"Transaction Fee: {record.transaction_fee}")
    print(f"Transaction Memo: {record.transaction_memo}")
    print(f"Account ID: {record.receipt.account_id}")

    print("\nHbar Transfers:")
    for account_id, amount in record.transfers.items():
        print(f"  {account_id}: {amount}")

    print("\nToken Transfers:")
    for token_id, transfers in record.token_transfers.items():
        print(f"  Token {token_id}:")
        for account_id, amount in transfers.items():
            print(f"    {account_id}: {amount}")


def query_record():
    """Full transaction record query example"""
    client = Client.from_env()

    # Create account transaction
    account_id, account_key, tx_id = create_account_transaction(client)
    record = TransactionRecordQuery().set_transaction_id(tx_id).execute(client)
    print("Account creation record:")
    print_transaction_record(record)

    # Create fungible token
    token_id = create_fungible_token(client)

    # Associate token
    associate_token(client, token_id, account_id, account_key)

    # Transfer tokens
    transfer_receipt = transfer_tokens(client, token_id, account_id)

    transfer_record = TransactionRecordQuery() \
        .set_transaction_id(transfer_receipt.transaction_id) \
        .execute(client)
    print("Token transfer record:")
    print_transaction_record(transfer_record)


if __name__ == "__main__":
    query_record()
