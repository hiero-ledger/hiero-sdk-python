"""
uv run examples/tokens/token_airdrop_transaction_cancel.py
python examples/tokens/token_airdrop_transaction_cancel.py
"""

import sys

from hiero_sdk_python import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    Hbar,
    TokenCreateTransaction,
    TokenAirdropTransaction,
    TransactionRecordQuery,
    TokenCancelAirdropTransaction,
    CryptoGetAccountBalanceQuery,
    ResponseCode,
)

# Load environment variables from .env file


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client


def create_account(
    client, operator_key, initial_balance=Hbar.from_tinybars(100_000_000)
):
    """Create a new account with the given initial balance."""
    print("\nCreating a new account...")
    recipient_key = PrivateKey.generate("ed25519")
    try:
        tx = (
            AccountCreateTransaction()
            .set_key_without_alias(recipient_key.public_key())
            .set_initial_balance(initial_balance)
        )
        receipt = tx.freeze_with(client).sign(operator_key).execute(client)
        recipient_id = receipt.account_id
        print(f"Created a new account with ID: {recipient_id}")
        return recipient_id, recipient_key
    except Exception as e:
        print(f"Error creating new account: {e}")
        sys.exit(1)


def create_token(
    client, operator_account_id, operator_account_key, token_name, token_symbol, initial_supply=1
):
    """Create a new token and return its token ID."""
    print(f"\nCreating token: {token_name} ({token_symbol})...")
    try:
        tx = (
            TokenCreateTransaction()
            .set_token_name(token_name)
            .set_token_symbol(token_symbol)
            .set_initial_supply(initial_supply)
            .set_treasury_account_id(operator_account_id)
        )
        receipt = tx.freeze_with(client).sign(operator_account_key).execute(client)
        token_id = receipt.token_id
        print(f"Created token {token_name} with ID: {token_id}")
        return token_id
    except Exception as e:
        print(f"Error creating token {token_name}: {e}")
        sys.exit(1)


def airdrop_tokens(client, operator_account_id, operator_account_key, recipient_id, token_ids):
    """Airdrop the provided tokens to a recipient account."""
    print(
        f"\nAirdropping tokens {', '.join([str(t) for t in token_ids])} to recipient {recipient_id}..."
    )

    try:
        # Balances before airdrop
        sender_balances_before = (
            CryptoGetAccountBalanceQuery(account_id=operator_account_id)
            .execute(client)
            .token_balances
        )
        recipient_balances_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )

        print("\nBalances before airdrop:")
        for t in token_ids:
            # token_ids elements are TokenId objects (not strings), so use them as dict keys
            sender_balance = sender_balances_before.get(t, 0)
            recipient_balance = recipient_balances_before.get(t, 0)
            print(f" {str(t)}: sender={sender_balance} recipient={recipient_balance}")
        tx = TokenAirdropTransaction()
        for token_id in token_ids:
            tx.add_token_transfer(token_id=token_id, account_id=operator_account_id, amount=-1)
            tx.add_token_transfer(token_id=token_id, account_id=recipient_id, amount=1)

        receipt = tx.freeze_with(client).sign(operator_account_key).execute(client)
        print(
            f"Token airdrop executed: status={receipt.status} "
            f"transaction_id={receipt.transaction_id}"
        )

        # Get record to inspect pending airdrops
        airdrop_record = TransactionRecordQuery(receipt.transaction_id).execute(client)
        pending = getattr(airdrop_record, "new_pending_airdrops", []) or []

        # Balances after airdrop
        sender_balances_after = (
            CryptoGetAccountBalanceQuery(account_id=operator_account_id)
            .execute(client)
            .token_balances
        )
        recipient_balances_after = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )

        print("\nBalances after airdrop:")
        for t in token_ids:
            # token_ids elements are TokenId objects (not strings), so use them as dict keys
            sender_balance = sender_balances_after.get(t, 0)
            recipient_balance = recipient_balances_after.get(t, 0)
            print(f" {str(t)}: sender={sender_balance} recipient={recipient_balance}")

        return pending
    except Exception as e:
        print(f"Error airdropping tokens: {e}")
        sys.exit(1)


def cancel_airdrops(client, operator_key, pending_airdrops):
    """Cancel all pending airdrops."""
    print("\nCanceling airdrops...")
    try:
        cancel_airdrop_tx = TokenCancelAirdropTransaction()
        if not pending_airdrops:
            print("No pending airdrops to cancel.")
            return

        for record in pending_airdrops:
            # `record.pending_airdrop_id` is already a PendingAirdropId object
            # use it directly (no need to try other attribute names)
            pid = record.pending_airdrop_id
            cancel_airdrop_tx.add_pending_airdrop(pid)

        cancel_airdrop_tx = cancel_airdrop_tx.freeze_with(client).sign(operator_key)
        cancel_airdrop_receipt = cancel_airdrop_tx.execute(client)

        if cancel_airdrop_receipt.status != ResponseCode.SUCCESS:
            print(
                f"Failed to cancel airdrop: " f"Status: {cancel_airdrop_receipt.status}"
            )
            sys.exit(1)

        print("Airdrop cancel transaction successful")
    except Exception as e:
        print(f"Error executing cancel airdrop token: {e}")
        sys.exit(1)


def token_airdrop_cancel():
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key
    recipient_id, _ = create_account(client, operator_key)

    # Create two tokens
    token_id_1 = create_token(client, operator_id, operator_key, "First Token", "TKA")
    token_id_2 = create_token(client, operator_id, operator_key, "Second Token", "TKB")

    # Airdrop tokens
    pending_airdrops = airdrop_tokens(
        client, operator_id, operator_key, recipient_id, [token_id_1, token_id_2]
    )

    # Cancel airdrops
    cancel_airdrops(client, operator_key, pending_airdrops)


if __name__ == "__main__":
    token_airdrop_cancel()
