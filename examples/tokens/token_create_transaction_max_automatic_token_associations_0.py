"""
Example: demonstrate how max_automatic_token_associations=0 behaves.
The script walks through:
1. Creating a fungible token on Hedera testnet (default network).
2. Creating an account whose max automatic associations is zero.
3. Attempting a token transfer (it fails because no association exists).
4. Associating the token for that account.
5. Transferring again, this time succeeding.
Run with:
    uv run examples/tokens/token_create_transaction_max_automatic_token_associations_0
"""

import sys
from typing import Tuple

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    AccountInfoQuery,
    Client,
    Hbar,
    PrivateKey,
    ResponseCode,
    TokenAssociateTransaction,
    TokenCreateTransaction,
    TokenId,
    TransferTransaction,
)
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.transaction.transaction_receipt import TransactionReceipt


TOKENS_TO_TRANSFER = 10


def setup_client():
    client = Client.from_env()
    print(f"Network: {client.network.network}")
    print(f"Client set up with operator id {client.operator_account_id}")
    return client

def create_demo_token(
    client: Client, operator_id: AccountId, operator_key: PrivateKey
) -> TokenId:
    """Create a fungible token whose treasury is the operator."""
    print("\nSTEP 1: Creating the fungible demo token...")
    # Build and sign the fungible token creation transaction using the operator as treasury.
    tx = (
        TokenCreateTransaction()
        .set_token_name("MaxAssociationsToken")
        .set_token_symbol("MAX0")
        .set_decimals(0)
        .set_initial_supply(1_000)
        .set_treasury_account_id(operator_id)
        .freeze_with(client)
        .sign(operator_key)
    )
    receipt = _receipt_from_response(tx.execute(client), client)
    status = _as_response_code(receipt.status)
    if status != ResponseCode.SUCCESS or receipt.token_id is None:
        print(f"ERROR: Token creation failed with status {status.name}.")
        sys.exit(1)

    print(f"Token created: {receipt.token_id}")
    return receipt.token_id


def create_max_account(
    client: Client, operator_key: PrivateKey
) -> Tuple[AccountId, PrivateKey]:
    """Create an account whose max automatic associations equals zero."""
    print(
        "\nSTEP 2: Creating account 'max' with max automatic associations set to 0..."
    )
    max_key = PrivateKey.generate()
    # Configure the new account to require explicit associations before accepting tokens.
    tx = (
        AccountCreateTransaction()
        .set_key(max_key.public_key())
        .set_initial_balance(Hbar(5))
        .set_account_memo("max (auto-assoc = 0)")
        .set_max_automatic_token_associations(0)
        .freeze_with(client)
        .sign(operator_key)
    )
    receipt = _receipt_from_response(tx.execute(client), client)
    status = _as_response_code(receipt.status)
    if status != ResponseCode.SUCCESS or receipt.account_id is None:
        print(f"ERROR: Account creation failed with status {status.name}.")
        sys.exit(1)

    print(f"Account created: {receipt.account_id}")
    return receipt.account_id, max_key


def show_account_settings(client: Client, account_id: AccountId) -> None:
    """Print the account's max automatic associations and known token relationships."""
    print("\nSTEP 3: Querying account info...")
    # Fetch account information to verify configuration before attempting transfers.
    info = AccountInfoQuery(account_id).execute(client)
    print(
        f"Account {account_id} max_automatic_token_associations: "
        f"{info.max_automatic_token_associations}"
    )
    print(f"Token relationships currently tracked: {len(info.token_relationships)}")


def try_transfer(
    client: Client,
    operator_id: AccountId,
    operator_key: PrivateKey,
    receiver_id: AccountId,
    token_id: TokenId,
    expect_success: bool,
) -> bool:
    """Attempt a token transfer and return True if it succeeds."""
    desired = "should succeed" if expect_success else "expected to fail"
    print(
        f"\nSTEP 4: Attempting to transfer {TOKENS_TO_TRANSFER} tokens ({desired}) "
        f"from {operator_id} to {receiver_id}..."
    )
    try:
        # Transfer tokens from the operator treasury to the new account.
        tx = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, -TOKENS_TO_TRANSFER)
            .add_token_transfer(token_id, receiver_id, TOKENS_TO_TRANSFER)
            .freeze_with(client)
            .sign(operator_key)
        )
        receipt = _receipt_from_response(tx.execute(client), client)
        status = _as_response_code(receipt.status)
        success = status == ResponseCode.SUCCESS
        if success:
            print(f"Transfer status: {status.name}")
        else:
            print(f"Transfer failed with status: {status.name}")
        return success
    except PrecheckError as err:
        print(f"Precheck failed with status { _response_code_name(err.status) }")
        return False
    except Exception as exc:  # pragma: no cover - unexpected runtime/network failures
        print(f"Unexpected error while transferring tokens: {exc}")
        return False


def associate_token(
    client: Client, account_id: AccountId, account_key: PrivateKey, token_id: TokenId
) -> None:
    """Explicitly associate the token so the account can hold balances."""
    print("\nSTEP 5: Associating the token for account 'max'...")
    # Submit the token association signed by the new account's private key.
    tx = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_key)
    )
    receipt = _receipt_from_response(tx.execute(client), client)
    status = _as_response_code(receipt.status)
    if status != ResponseCode.SUCCESS:
        print(f"ERROR: Token association failed with status {status.name}.")
        sys.exit(1)
    print(f"Token {token_id} successfully associated with account {account_id}.")


def _receipt_from_response(result, client) -> TransactionReceipt:
    """Normalize transaction return types to a TransactionReceipt instance."""
    if isinstance(result, TransactionReceipt):
        return result
    return result.get_receipt(client)


def _response_code_name(status) -> str:
    """Convert an enum/int status into a readable ResponseCode name."""
    return _as_response_code(status).name


def _as_response_code(value) -> ResponseCode:
    """Ensure we always treat codes as ResponseCode enums.

    Some transactions return raw integer codes rather than ResponseCode enums,
    so we normalize before accessing `.name`.
    """
    if isinstance(value, ResponseCode):
        return value
    return ResponseCode(value)


def main() -> None:
    """Execute the entire flow end-to-end."""
    client = setup_client()
    operator_id = client.operator_account_id
    operator_key = client.operator_private_key
    token_id = create_demo_token(client, operator_id, operator_key)
    max_account_id, max_account_key = create_max_account(client, operator_key)
    show_account_settings(client, max_account_id)

    first_attempt_success = try_transfer(
        client,
        operator_id,
        operator_key,
        max_account_id,
        token_id,
        expect_success=False,
    )
    if first_attempt_success:
        print(
            "WARNING: transfer succeeded even though no association existed. "
            "The account may already be associated with this token."
        )
    else:
        associate_token(client, max_account_id, max_account_key, token_id)
        second_attempt_success = try_transfer(
            client,
            operator_id,
            operator_key,
            max_account_id,
            token_id,
            expect_success=True,
        )
        if second_attempt_success:
            print("\nTransfer succeeded after explicitly associating the token.")
        else:
            print(
                "\nTransfer still failed after associating the token. "
                "Verify balances, association status, and token configuration."
            )


if __name__ == "__main__":
    main()
