"""
uv run examples/token_create_transaction_freeze_key.py
python examples/token_create_transaction_freeze_key.py

Demonstrates how the Hedera freeze key works by walking through:
1. Creating a token without a freeze key and showing freeze/unfreeze attempts fail
2. Creating a token with a freeze key, freezing/unfreezing a secondary account,
   and verifying how transfers behave while frozen
3. (Bonus) Showing that tokens created with freezeDefault=True start accounts frozen
"""

import os
import sys
from dataclasses import dataclass
from typing import Tuple

from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    Network,
    PrivateKey,
    ResponseCode,
    TokenAssociateTransaction,
    TokenCreateTransaction,
    TokenFreezeTransaction,
    TokenUnfreezeTransaction,
    TransferTransaction,
)

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()
TRANSFER_AMOUNT = 10  # Small token transfer for demonstrations


@dataclass
class DemoAccount:
    account_id: AccountId
    private_key: PrivateKey


def setup_client() -> Tuple[Client, AccountId, PrivateKey]:
    """Initialize the Hedera client using operator credentials."""
    network = Network(network_name)
    print(f"🌐 Connecting to Hedera {network_name} network...")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"✅ Client ready with operator {operator_id}")
        return client, operator_id, operator_key
    except (TypeError, ValueError):
        print("❌ Please provide valid OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)


def generate_freeze_key() -> PrivateKey:
    """Create a fresh freeze key for demonstration."""
    print("\n🔐 Generating a new freeze key...")
    freeze_key = PrivateKey.generate_ed25519()
    print("✅ Freeze key ready.")
    return freeze_key


def create_token_without_freeze_key(
    client: Client, operator_id: AccountId, operator_key: PrivateKey
):
    """Create a fungible token that does not include a freeze key."""
    print("\nSTEP 1️⃣  Creating token WITHOUT a freeze key...")
    receipt = (
        TokenCreateTransaction()
        .set_token_name("Freeze Key Absence Token")
        .set_token_symbol("NOFRZ")
        .set_decimals(2)
        .set_initial_supply(50_000)
        .set_treasury_account_id(operator_id)
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"✅ Token (without freeze key) created: {token_id}")
    return token_id


def demonstrate_missing_freeze_key(
    client: Client, token_id, operator_id: AccountId, operator_key: PrivateKey
):
    """Attempt freeze/unfreeze operations when no freeze key exists."""
    print("\nSTEP 2️⃣  Demonstrating that freeze operations fail without a freeze key...")
    try:
        receipt = (
            TokenFreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        status = ResponseCode(receipt.status)
        if status == ResponseCode.SUCCESS:
            print("⚠️ Unexpectedly froze account without a freeze key!")
        else:
            print(
                f"✅ Freeze attempt rejected (as expected): {status.name}. "
                "Tokens without freeze keys cannot freeze accounts."
            )
    except Exception as exc:
        print(f"✅ Freeze attempt failed as expected: {exc}")

    try:
        receipt = (
            TokenUnfreezeTransaction()
            .set_token_id(token_id)
            .set_account_id(operator_id)
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )
        status = ResponseCode(receipt.status)
        if status == ResponseCode.SUCCESS:
            print("⚠️ Unexpectedly unfroze account without a freeze key!")
        else:
            print(
                f"✅ Unfreeze attempt rejected (as expected): {status.name}. "
                "Without a freeze key, unfreeze is impossible."
            )
    except Exception as exc:
        print(f"✅ Unfreeze attempt failed as expected: {exc}")


def create_token_with_freeze_key(
    client: Client,
    operator_id: AccountId,
    operator_key: PrivateKey,
    freeze_key: PrivateKey,
    *,
    freeze_default: bool = False,
    name: str = "Freeze Key Demo Token",
    symbol: str = "FRZ",
):
    """Create a token equipped with a freeze key (and optional freeze default)."""
    label = "with freezeDefault=True" if freeze_default else "with freeze key"
    print(f"\nSTEP 3️⃣  Creating token {label} ...")
    tx = (
        TokenCreateTransaction()
        .set_token_name(name)
        .set_token_symbol(symbol)
        .set_decimals(2)
        .set_initial_supply(100_000)
        .set_treasury_account_id(operator_id)
        .set_freeze_key(freeze_key)
    )
    if freeze_default:
        tx.set_freeze_default(True)

    receipt = tx.freeze_with(client).sign(operator_key).sign(freeze_key).execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Token creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    token_id = receipt.token_id
    extra = " (accounts start frozen)" if freeze_default else ""
    print(f"✅ Token created: {token_id}{extra}")
    return token_id


def create_demo_account(client: Client, operator_key: PrivateKey) -> DemoAccount:
    """Create a secondary account for transfers."""
    print("\nSTEP 4️⃣  Creating a secondary account for testing...")
    new_key = PrivateKey.generate_ed25519()
    receipt = (
        AccountCreateTransaction()
        .set_key(new_key.public_key())
        .set_initial_balance(Hbar(2))
        .set_account_memo("Freeze key demo account")
        .freeze_with(client)
        .sign(operator_key)
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Account creation failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)

    account_id = receipt.account_id
    print(f"✅ Secondary account created: {account_id}")
    return DemoAccount(account_id, new_key)


def associate_token(
    client: Client, token_id, account: DemoAccount, signer: PrivateKey
):
    """Associate a token with a given account."""
    print(f"\nSTEP 5️⃣  Associating token {token_id} with account {account.account_id}...")
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account.account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(signer)
        .execute(client)
    )
    if receipt.status != ResponseCode.SUCCESS:
        print(f"❌ Association failed: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    print("✅ Token association complete.")


def attempt_transfer(
    client: Client,
    token_id,
    treasury_id: AccountId,
    treasury_key: PrivateKey,
    recipient: DemoAccount,
    *,
    note: str,
):
    """
    Try to transfer tokens from the treasury to a recipient and log the result.
    Returns True when the transfer succeeds, False otherwise.
    """
    print(f"\n➡️  Attempting transfer ({note}) ...")
    try:
        receipt = (
            TransferTransaction()
            .add_token_transfer(token_id, treasury_id, -TRANSFER_AMOUNT)
            .add_token_transfer(token_id, recipient.account_id, TRANSFER_AMOUNT)
            .freeze_with(client)
            .sign(treasury_key)
            .execute(client)
        )
        status = ResponseCode(receipt.status)
        if status == ResponseCode.SUCCESS:
            print("✅ Transfer succeeded.")
            return True

        print(f"⚠️ Transfer failed: {status.name}")
        return False
    except Exception as exc:
        print(f"⚠️ Transfer threw exception: {exc}")
        return False


def freeze_account(
    client: Client, token_id, account_id: AccountId, freeze_key: PrivateKey
):
    """Freeze an account for the given token."""
    print(f"\n🧊 Freezing account {account_id} for token {token_id}...")
    receipt = (
        TokenFreezeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
        .sign(freeze_key)
        .execute(client)
    )
    status = ResponseCode(receipt.status)
    if status != ResponseCode.SUCCESS:
        print(f"❌ Freeze failed: {status.name}")
        sys.exit(1)
    print("✅ Account frozen.")


def unfreeze_account(
    client: Client, token_id, account_id: AccountId, freeze_key: PrivateKey
):
    """Unfreeze an account for the given token."""
    print(f"\n🔥 Unfreezing account {account_id} for token {token_id}...")
    receipt = (
        TokenUnfreezeTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
        .sign(freeze_key)
        .execute(client)
    )
    status = ResponseCode(receipt.status)
    if status != ResponseCode.SUCCESS:
        print(f"❌ Unfreeze failed: {status.name}")
        sys.exit(1)
    print("✅ Account unfrozen.")


def demonstrate_freeze_default_flow(
    client: Client,
    operator_id: AccountId,
    operator_key: PrivateKey,
    freeze_key: PrivateKey,
):
    """
    Bonus: Show that freezeDefault=True starts new accounts frozen until explicitly unfrozen.
    """
    print("\nBONUS 🌟 Demonstrating freezeDefault=True behavior...")
    token_id = create_token_with_freeze_key(
        client,
        operator_id,
        operator_key,
        freeze_key,
        freeze_default=True,
        name="Freeze Default Token",
        symbol="FDF",
    )
    default_frozen_account = create_demo_account(client, operator_key)
    associate_token(client, token_id, default_frozen_account, default_frozen_account.private_key)

    success_before_unfreeze = attempt_transfer(
        client,
        token_id,
        operator_id,
        operator_key,
        default_frozen_account,
        note="freezeDefault=True (should FAIL)",
    )
    if success_before_unfreeze:
        print("⚠️ Unexpected success: account should start frozen when freezeDefault=True.")
    else:
        print("✅ Transfer blocked as expected because the account was frozen by default.")

    unfreeze_account(client, token_id, default_frozen_account.account_id, freeze_key)
    attempt_transfer(
        client,
        token_id,
        operator_id,
        operator_key,
        default_frozen_account,
        note="after unfreezing default-frozen account",
    )


def main():
    print("🚀 Hedera Freeze Key Demonstration")
    print("=" * 60)

    client, operator_id, operator_key = setup_client()

    # Token without a freeze key
    token_without_key = create_token_without_freeze_key(client, operator_id, operator_key)
    demonstrate_missing_freeze_key(client, token_without_key, operator_id, operator_key)

    # Token with a freeze key
    freeze_key = generate_freeze_key()
    token_with_freeze = create_token_with_freeze_key(
        client, operator_id, operator_key, freeze_key
    )

    demo_account = create_demo_account(client, operator_key)
    associate_token(client, token_with_freeze, demo_account, demo_account.private_key)

    # Transfers while account is unfrozen
    attempt_transfer(
        client,
        token_with_freeze,
        operator_id,
        operator_key,
        demo_account,
        note="while account is unfrozen",
    )

    # Freeze, attempt transfer, then unfreeze
    freeze_account(client, token_with_freeze, demo_account.account_id, freeze_key)
    transfer_success = attempt_transfer(
        client,
        token_with_freeze,
        operator_id,
        operator_key,
        demo_account,
        note="while account is frozen (should fail)",
    )
    if transfer_success:
        print("⚠️ Transfer succeeded but should have failed because account was frozen.")

    unfreeze_account(client, token_with_freeze, demo_account.account_id, freeze_key)
    attempt_transfer(
        client,
        token_with_freeze,
        operator_id,
        operator_key,
        demo_account,
        note="after unfreezing the account",
    )

    # Bonus behavior
    demonstrate_freeze_default_flow(client, operator_id, operator_key, freeze_key)

    print("\n🎉 Freeze key demonstration completed! Review the log above for each step.")


if __name__ == "__main__":
    main()

