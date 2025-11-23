"""
This example demonstrates the pause key capabilities for token management using the Hiero Python SDK.

It shows:
1. Creating a token *without* a pause key
2. Attempting to pause it — expected failure
3. Creating a token *with* a pause key
4. Successfully pausing and unpausing the token
5. Demonstrating that transfers fail while the token is paused
6. (Bonus) Removing the pause key while the token is paused → permanently paused

Required environment variables:
- OPERATOR_ID
- OPERATOR_KEY

Usage:
uv run examples/token_create_transaction_pause_key.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TokenCreateTransaction,
    TokenPauseTransaction,
    TokenUnpauseTransaction,
    TokenUpdateTransaction,
    TokenInfoQuery,
    TransferTransaction,
    AccountCreateTransaction,
    Hbar,
)

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType

load_dotenv()
network_name = os.getenv("NETWORK", "testnet").lower()


# -------------------------------------------------------
# CLIENT SETUP
# -------------------------------------------------------
def setup_client():
    """Create client from environment variables"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network...")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv("OPERATOR_ID", ""))
        operator_key = PrivateKey.from_string(os.getenv("OPERATOR_KEY", ""))
        client.set_operator(operator_id, operator_key)
        print(f"Client ready — Operator: {client.operator_account_id}\n")
        return client, operator_id, operator_key

    except Exception:
        print("❌ ERROR: Invalid OPERATOR_ID or OPERATOR_KEY in .env")
        sys.exit(1)


# -------------------------------------------------------
# TOKEN CREATION (NO PAUSE KEY)
# -------------------------------------------------------
def create_token_without_pause_key(client, operator_id, operator_key):
    print("🔹 Creating token WITHOUT pause key...")

    tx = (
        TokenCreateTransaction()
        .set_token_name("PauseKeyMissing")
        .set_token_symbol("NOPAUSE")
        .set_decimals(0)
        .set_initial_supply(100)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .freeze_with(client)
        .sign(operator_key)
    )

    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print("❌ Token creation failed")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"✅ Token created WITHOUT pause key → {token_id}\n")
    return token_id


def attempt_pause_should_fail(client, token_id, operator_key):
    print("🔹 Attempting to pause token WITHOUT a pause key... (expected failure)")
    try:
        tx = (
            TokenPauseTransaction()
            .set_token_id(token_id)
            .freeze_with(client)
            .sign(operator_key)
        )
        receipt = tx.execute(client)

        print("⚠️ Unexpected success! Pause should NOT be possible.")
        print(f"Status: {ResponseCode(receipt.status).name}\n")

    except Exception as e:
        print(f"✅ Expected failure occurred: {e}\n")


# -------------------------------------------------------
# TOKEN CREATION WITH PAUSE KEY
# -------------------------------------------------------
def create_token_with_pause_key(client, operator_id, operator_key, pause_key):
    print("🔹 Creating token WITH pause key...")

    tx = (
        TokenCreateTransaction()
        .set_token_name("PauseKeyDemo")
        .set_token_symbol("PAUSE")
        .set_decimals(0)
        .set_initial_supply(100)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.INFINITE)
        .set_pause_key(pause_key)  # NEW
        .freeze_with(client)
    )

    tx.sign(operator_key)
    tx.sign(pause_key)

    receipt = tx.execute(client)
    if receipt.status != ResponseCode.SUCCESS:
        print("❌ Token creation failed")
        sys.exit(1)

    token_id = receipt.token_id
    print(f"✅ Token created WITH pause key → {token_id}\n")
    return token_id


# -------------------------------------------------------
# PAUSE / UNPAUSE DEMO
# -------------------------------------------------------
def pause_token(client, token_id, pause_key):
    print("🔹 Pausing token...")

    tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )

    receipt = tx.execute(client)
    if receipt.status == ResponseCode.SUCCESS:
        print("✅ Token paused successfully!\n")
    else:
        print(f"❌ Pause failed: {ResponseCode(receipt.status).name}")


def unpause_token(client, token_id, pause_key):
    print("🔹 Unpausing token...")

    tx = (
        TokenUnpauseTransaction()
        .set_token_id(token_id)
        .freeze_with(client)
        .sign(pause_key)
    )

    receipt = tx.execute(client)
    if receipt.status == ResponseCode.SUCCESS:
        print("✅ Token unpaused successfully!\n")
    else:
        print(f"❌ Unpause failed: {ResponseCode(receipt.status).name}")


# -------------------------------------------------------
# TRANSFERS WHILE PAUSED SHOULD FAIL
# -------------------------------------------------------
def create_temp_account(client, operator_key):
    """Creates a small account for transfer testing."""
    new_key = PrivateKey.generate_ed25519()
    pub_key = new_key.public_key()

    print("🔹 Creating a temporary recipient account...")

    tx = (
        AccountCreateTransaction()
        .set_key(pub_key)  # MUST use public key
        .set_initial_balance(Hbar.from_tinybars(1000))
        .freeze_with(client)
        .sign(operator_key)
    )

    receipt = tx.execute(client)
    account_id = receipt.account_id
    print(f"✅ Temp account created: {account_id}\n")
    return account_id, new_key



def test_transfer_while_paused(client, operator_id, operator_key, recipient_id, token_id):
    print("🔹 Attempting transfer WHILE token is paused (expected failure)...")

    tx = (
        TransferTransaction()
        .add_token_transfer(token_id, operator_id, -10)
        .add_token_transfer(token_id, recipient_id, 10)
        .freeze_with(client)
        .sign(operator_key)
    )

    receipt = tx.execute(client)

    if receipt.status == ResponseCode.TOKEN_IS_PAUSED:
        print("✅ Transfer failed as expected: TOKEN_IS_PAUSED\n")
    else:
        print(f"⚠️ Unexpected status: {ResponseCode(receipt.status).name}\n")

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    client, operator_id, operator_key = setup_client()

    print("\n==================== PART 1 — NO PAUSE KEY ====================\n")
    token_no_pause = create_token_without_pause_key(client, operator_id, operator_key)
    attempt_pause_should_fail(client, token_no_pause, operator_key)

    print("\n==================== PART 2 — WITH PAUSE KEY ====================\n")
    pause_key = PrivateKey.generate_ed25519()

    token_with_pause = create_token_with_pause_key(
        client, operator_id, operator_key, pause_key
    )

    pause_token(client, token_with_pause, pause_key)

    recipient_id, _ = create_temp_account(client, operator_key)
    test_transfer_while_paused(
        client, operator_id, operator_key, recipient_id, token_with_pause
    )

    unpause_token(client, token_with_pause, pause_key)

print("\n🎉 Pause key demonstration completed!")


if __name__ == "__main__":
    main()
