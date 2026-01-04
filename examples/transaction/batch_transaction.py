"""
uv run examples/transaction/batch_transaction.py
"""

import os
import sys

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    Client,
    Network,
    PrivateKey,
    AccountCreateTransaction,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
    TokenCreateTransaction,
    TokenFreezeTransaction,
    TokenType,
    TokenUnfreezeTransaction,
    BatchTransaction,
    TransferTransaction,
)

load_dotenv()


def get_balance(client, account_id, token_id):
    tokens_balance = (
        CryptoGetAccountBalanceQuery(account_id=account_id)
        .execute(client)
        .token_balances
    )

    print(f"Account: {account_id}: {tokens_balance[token_id] if tokens_balance else 0}")


def setup_client():
    """
    Set up and configure a Hedera client for testnet operations.
    """
    network_name = os.getenv("NETWORK", "testnet").lower()

    print(f"Connecting to Hedera {network_name} network!")

    try:
        network = Network(network_name)
        client = Client(network)

        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))

        client.set_operator(operator_id, operator_key)
        print(f"Client initialized with operator: {operator_id}")
        return client
    except Exception as e:
        print(f"Failed to set up client: {e}")
        sys.exit(1)


def create_account(client):
    """
    Create a new recipient account.
    """
    print("\nCreating new recipient account...")
    try:
        key = PrivateKey.generate()
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(key.public_key())
            .set_max_automatic_token_associations(
                2
            )  # to transfer token without associating it
            .set_initial_balance(1)
        )

        receipt = tx.freeze_with(client).execute(client)
        recipient_id = receipt.account_id

        print(f"New account created: {receipt.account_id}")
        return recipient_id
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def create_fungible_token(client, freeze_key):
    """
    Create a fungible token with freeze_key.
    """
    print("\nCreating fungible token...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name("FiniteFungibleToken")
            .set_token_symbol("FFT")
            .set_initial_supply(2)
            .set_treasury_account_id(client.operator_account_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_freeze_key(freeze_key)
            .freeze_with(client)
            .sign(client.operator_private_key)
            .sign(freeze_key)
        )
        receipt = tx.execute(client)
        token_id = receipt.token_id

        print(f"Token created: {receipt.token_id}")

        return token_id
    except Exception as e:
        print(f"Error creating token: {e}")
        sys.exit(1)


def freeze_token(client, account_id, token_id, freeze_key):
    """
    Freeze token for an account.
    """
    print(f"\nFreezing token for account {account_id}")
    try:
        tx = (
            TokenFreezeTransaction()
            .set_account_id(account_id)
            .set_token_id(token_id)
            .freeze_with(client)
            .sign(freeze_key)
        )

        receipt = tx.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(f"Freeze failed: {ResponseCode(receipt.status).name})")
            sys.exit(1)

        print("Token freeze successful!")
    except Exception as e:
        print(f"Error freezing token for account: {e}")
        sys.exit(1)


def transfer_token(client, sender, recipient, token_id):
    """
    Perform a token trasfer transaction.
    """
    print(f"\nTransferring token {token_id} from {sender} → {recipient}")
    try:
        tx = (
            TransferTransaction()
            .add_token_transfer(token_id=token_id, account_id=sender, amount=-1)
            .add_token_transfer(token_id=token_id, account_id=recipient, amount=1)
        )

        receipt = tx.execute(client)

        return receipt
    except Exception as e:
        print(f"Error transfering token: {e}")
        sys.exit(1)


def perform_batch_tx(client, sender, recipient, token_id, freeze_key):
    """
    Perform a batch transaction using PrivateKey as batch_key.
    """
    print(
        "\nPerforming batch transaction with PrivateKey (unfreeze → transfer → freeze)..."
    )
    batch_key = PrivateKey.generate()

    unfreeze_tx = (
        TokenUnfreezeTransaction()
        .set_account_id(sender)
        .set_token_id(token_id)
        .batchify(client, batch_key)
        .sign(freeze_key)
    )

    transfer_tx = (
        TransferTransaction()
        .add_token_transfer(token_id, sender, -1)
        .add_token_transfer(token_id, recipient, 1)
        .batchify(client, batch_key)
    )

    freeze_tx = (
        TokenFreezeTransaction()
        .set_account_id(sender)
        .set_token_id(token_id)
        .batchify(client, batch_key)
        .sign(freeze_key)
    )

    # 50 is the maximum limit for internal transaction inside a BatchTransaction
    batch = (
        BatchTransaction()
        .add_inner_transaction(unfreeze_tx)
        .add_inner_transaction(transfer_tx)
        .add_inner_transaction(freeze_tx)
        .freeze_with(client)
        .sign(batch_key)
    )

    receipt = batch.execute(client)
    print(f"Batch transaction status: {ResponseCode(receipt.status).name}")


def perform_batch_tx_with_public_key(client, sender, recipient, token_id, freeze_key):
    """
    Perform a batch transaction using PublicKey as batch_key.
    Demonstrates that batch_key can accept both PrivateKey and PublicKey.
    """
    print(
        "\n✨ Performing batch transaction with PublicKey (unfreeze → transfer → freeze)..."
    )

    # Generate a key pair - we'll use the PublicKey as batch_key
    batch_private_key = PrivateKey.generate()
    batch_public_key = batch_private_key.public_key()

    print(f"Using PublicKey as batch_key: {batch_public_key}")

    # Create inner transactions using PublicKey as batch_key
    unfreeze_tx = (
        TokenUnfreezeTransaction()
        .set_account_id(sender)
        .set_token_id(token_id)
        .batchify(client, batch_public_key)  # Using PublicKey!
        .sign(freeze_key)
    )

    transfer_tx = (
        TransferTransaction()
        .add_token_transfer(token_id, sender, -1)
        .add_token_transfer(token_id, recipient, 1)
        .batchify(client, batch_public_key)  # Using PublicKey!
    )

    freeze_tx = (
        TokenFreezeTransaction()
        .set_account_id(sender)
        .set_token_id(token_id)
        .batchify(client, batch_public_key)  # Using PublicKey!
        .sign(freeze_key)
    )

    # Assemble the batch transaction
    batch = (
        BatchTransaction()
        .add_inner_transaction(unfreeze_tx)
        .add_inner_transaction(transfer_tx)
        .add_inner_transaction(freeze_tx)
        .freeze_with(client)
        .sign(batch_private_key)  # Sign with PrivateKey for execution
    )

    receipt = batch.execute(client)
    print(
        f"Batch transaction with PublicKey status: {ResponseCode(receipt.status).name}"
    )
    print(
        "   This demonstrates that batch_key now accepts both PrivateKey and PublicKey!"
    )


def main():
    client = setup_client()
    freeze_key = PrivateKey.generate()

    recipient_id = create_account(client)
    token_id = create_fungible_token(client, freeze_key)

    # Freeze operator for token
    freeze_token(client, client.operator_account_id, token_id, freeze_key)

    # Confirm transfer fails
    receipt = transfer_token(client, client.operator_account_id, recipient_id, token_id)
    if receipt.status == ResponseCode.ACCOUNT_FROZEN_FOR_TOKEN:
        print("\nCorrect: Account is frozen for token transfers.")
    else:
        print("\nExpected freeze to block transfer!")
        sys.exit(1)

    # Show balances
    print("\nBalances before batch:")
    get_balance(client, client.operator_account_id, token_id)
    get_balance(client, recipient_id, token_id)

    # Batch unfreeze → transfer → freeze (using PrivateKey)
    perform_batch_tx(
        client, client.operator_account_id, recipient_id, token_id, freeze_key
    )

    print("\nBalances after first batch:")
    get_balance(client, client.operator_account_id, token_id)
    get_balance(client, recipient_id, token_id)

    # Verify that token is frozen again
    receipt = transfer_token(client, client.operator_account_id, recipient_id, token_id)
    if receipt.status == ResponseCode.ACCOUNT_FROZEN_FOR_TOKEN:
        print("\n✅ Correct: Account is frozen again after first batch")
    else:
        print("\nAccount should be frozen again!")
        sys.exit(1)

    # Now demonstrate using PublicKey as batch_key
    print("\n" + "=" * 80)
    print("Demonstrating PublicKey support for batch_key")
    print("=" * 80)

    perform_batch_tx_with_public_key(
        client, client.operator_account_id, recipient_id, token_id, freeze_key
    )

    print("\nBalances after second batch (with PublicKey):")
    get_balance(client, client.operator_account_id, token_id)
    get_balance(client, recipient_id, token_id)

    # Verify that token is frozen again
    receipt = transfer_token(client, client.operator_account_id, recipient_id, token_id)
    if receipt.status == ResponseCode.ACCOUNT_FROZEN_FOR_TOKEN:
        print(
            "\n✅ Success! Account is frozen again, PublicKey batch_key works correctly!"
        )
    else:
        print("\nAccount should be frozen again!")
        sys.exit(1)


if __name__ == "__main__":
    main()
