"""
Token KYC Key Demonstration

This script demonstrates how to work with KYC (Know Your Customer) keys on Hedera tokens:
1. Creating a token WITHOUT a KYC key and attempting KYC operations (fails)
2. Creating a token WITH a KYC key
3. Understanding why KYC keys are required for KYC operations
4. Granting KYC to accounts with the KYC key
5. Demonstrating token transfers with and without KYC

KYC Key Behavior:
- The KYC key is required to grant or revoke KYC for token accounts
- Without a KYC key, KYC operations cannot be performed
- Previously granted KYC remains if the KYC key is removed
- KYC is orthogonal to freeze (different keys control different features)

Run with:
  uv run examples/token_create_transaction_kyc_key.py
  python examples/token_create_transaction_kyc_key.py

"""
import os
import sys
import time
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    Hbar,
    ResponseCode,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.hapi.services.basic_types_pb2 import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery

load_dotenv()


def setup_client():
    """
    Initialize and set up the client with operator account credentials.

    Returns:
        tuple: (client, operator_id, operator_key)
    """
    print("Connecting to Hedera testnet...")
    client = Client(Network(network='testnet'))

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
        client.set_operator(operator_id, operator_key)
        print(f" Client configured with operator: {operator_id}\n")
        return client, operator_id, operator_key
    except (TypeError, ValueError) as e:
        print(f" Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file")
        sys.exit(1)


def create_account(client, operator_key, initial_balance=Hbar(2)):
    """
    Create a new test account on the Hedera network.

    Args:
        client: The Hiero SDK client
        operator_key: The operator's private key for signing
        initial_balance: Initial HBAR balance for the account

    Returns:
        tuple: (account_id, account_private_key)
    """
    account_private_key = PrivateKey.generate("ed25519")
    account_public_key = account_private_key.public_key()

    try:
        transaction = (
            AccountCreateTransaction()
            .set_key(account_public_key)
            .set_initial_balance(initial_balance)
            .freeze_with(client)
        )
        transaction.sign(operator_key)
        receipt = transaction.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" Account creation failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        account_id = receipt.account_id
        print(f" New account created: {account_id}")
        return account_id, account_private_key
    except Exception as e:
        print(f" Error creating account: {e}")
        sys.exit(1)


def create_token_without_kyc_key(client, operator_id, operator_key):
    """
    Demonstrate creating a token WITHOUT a KYC key.
    This shows that KYC operations will fail for this token.

    Returns:
        str: The token ID
    """
    print("\n" + "=" * 70)
    print("STEP 1: Creating a token WITHOUT KYC key")
    print("=" * 70)

    try:
        receipt = (
            TokenCreateTransaction()
            .set_token_name("Token Without KYC")
            .set_token_symbol("NOKYC")
            .set_decimals(2)
            .set_initial_supply(100)
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(1000)
            .set_admin_key(operator_key.public_key())
            .set_supply_key(operator_key.public_key())
            # NOTE: No KYC key is set!
            .freeze_with(client)
            .sign(operator_key)
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" Token creation failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        token_id = receipt.token_id
        print(f" Token created without KYC key: {token_id}\n")
        return token_id
    except Exception as e:
        print(f" Error creating token: {e}")
        sys.exit(1)


def attempt_kyc_without_key(client, token_id, account_id, kyc_private_key):
    """
    Attempt to grant KYC on a token that has no KYC key.
    This should fail with an appropriate error.

    This demonstrates why having a KYC key is essential for KYC operations.
    """
    print("\n" + "=" * 70)
    print("STEP 2: Attempting to grant KYC on token without KYC key (will fail)")
    print("=" * 70)

    try:
        receipt = (
            TokenGrantKycTransaction()
            .set_token_id(token_id)
            .set_account_id(account_id)
            .freeze_with(client)
            .sign(kyc_private_key)
            .execute(client)
        )

        # Check the response status
        status_name = ResponseCode(receipt.status).name
        if receipt.status != ResponseCode.SUCCESS:
            print(f" KYC grant failed as expected with status: {status_name}")
            print(f"   Reason: Token {token_id} has no KYC key defined\n")
            return False
        else:
            print(f"  Unexpected ! Status: {status_name}\n")
            return True
    except Exception as e:
        print(f" Error attempting KYC grant: {e}\n")
        return False


def create_token_with_kyc_key(client, operator_id, operator_key, kyc_private_key):
    """
    Create a token WITH a KYC key.
    This demonstrates the proper way to create a token that requires KYC.

    Returns:
        str: The token ID
    """
    print("\n" + "=" * 70)
    print("STEP 3: Creating a token WITH KYC key")
    print("=" * 70)

    try:
        receipt = (
            TokenCreateTransaction()
            .set_token_name("Token With KYC")
            .set_token_symbol("WITHKYC")
            .set_decimals(2)
            .set_initial_supply(100)
            .set_treasury_account_id(operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(1000)
            .set_admin_key(operator_key.public_key())
            .set_supply_key(operator_key.public_key())
            .set_kyc_key(kyc_private_key.public_key())  # KYC key is set!
            .freeze_with(client)
            .sign(operator_key)
            .sign(kyc_private_key)  # The KYC key must sign the transaction
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" Token creation failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        token_id = receipt.token_id
        print(f" Token created WITH KYC key: {token_id}\n")
        return token_id
    except Exception as e:
        print(f" Error creating token: {e}")
        sys.exit(1)


def associate_token_to_account(client, token_id, account_id, account_private_key):
    """
    Associate a token with an account.
    This is required before the account can receive or hold the token.
    """
    try:
        associate_transaction = (
            TokenAssociateTransaction()
            .set_account_id(account_id)
            .add_token_id(token_id)
            .freeze_with(client)
            .sign(account_private_key)  # Must be signed by the account
        )

        receipt = associate_transaction.execute(client)

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" Token association failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print(f" Token {token_id} associated with account {account_id}")
    except Exception as e:
        print(f" Error associating token: {e}")
        sys.exit(1)


def attempt_transfer_without_kyc(client, token_id, operator_id, recipient_id, operator_key):
    """
    Attempt to transfer tokens to an account that has not been granted KYC.
    Depending on token configuration, this may fail.

    Returns:
        bool: True if transfer succeeded, False if it failed
    """
    print("\n" + "=" * 70)
    print("STEP 5: Attempting token transfer BEFORE KYC grant (may fail)")
    print("=" * 70)

    try:
        # Check balance before transfer
        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        recipient_balance_before = balance_before.get(token_id, 0)
        print(
            f"Recipient's token balance before transfer: {recipient_balance_before}")

        # Attempt transfer
        transfer_tx = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, -10)
            .add_token_transfer(token_id, recipient_id, 10)
            .freeze_with(client)
            .sign(operator_key)
        )
        receipt = transfer_tx.execute(client)

        status_name = ResponseCode(receipt.status).name

        if receipt.status != ResponseCode.SUCCESS:
            print(f" Transfer failed with status: {status_name}")
            print(f"   Reason: Account may require KYC before receiving tokens\n")
            return False
        else:
            print(f" Transfer succeeded with status: {status_name}")
            # Check balance after transfer
            balance_after = (
                CryptoGetAccountBalanceQuery(account_id=recipient_id)
                .execute(client)
                .token_balances
            )
            recipient_balance_after = balance_after.get(token_id, 0)
            print(
                f"Recipient's token balance after transfer: {recipient_balance_after}\n")
            return True
    except Exception as e:
        print(f" Error during transfer attempt: {e}\n")
        return False


def grant_kyc_to_account(client, token_id, account_id, kyc_private_key):
    """
    Grant KYC to an account for a specific token.
    This allows the account to interact with the token (transfer, receive, etc).
    """
    print("\n" + "=" * 70)
    print("STEP 6: Granting KYC to account using KYC key")
    print("=" * 70)

    try:
        receipt = (
            TokenGrantKycTransaction()
            .set_token_id(token_id)
            .set_account_id(account_id)
            .freeze_with(client)
            .sign(kyc_private_key)  # Must be signed by the KYC key
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" KYC grant failed with status: {ResponseCode(receipt.status).name}")
            sys.exit(1)

        print(f" KYC granted for account {account_id} on token {token_id}\n")
    except Exception as e:
        print(f" Error granting KYC: {e}")
        sys.exit(1)


def transfer_token_after_kyc(client, token_id, operator_id, recipient_id, operator_key):
    """
    Transfer tokens to an account that HAS been granted KYC.
    This should succeed.
    """
    print("\n" + "=" * 70)
    print("STEP 7: Transferring tokens AFTER KYC grant (should succeed)")
    print("=" * 70)

    try:
        # Check balance before transfer
        balance_before = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        recipient_balance_before = balance_before.get(token_id, 0)
        print(
            f"Recipient's token balance before transfer: {recipient_balance_before}")

        # Perform transfer
        transfer_tx = (
            TransferTransaction()
            .add_token_transfer(token_id, operator_id, -10)
            .add_token_transfer(token_id, recipient_id, 10)
            .freeze_with(client)
            .sign(operator_key)
        )
        receipt = transfer_tx.execute(client)

        status_name = ResponseCode(receipt.status).name

        if receipt.status != ResponseCode.SUCCESS:
            print(f" Transfer failed with status: {status_name}")
            sys.exit(1)

        print(f" Transfer succeeded with status: {status_name}")

        # Check balance after transfer
        balance_after = (
            CryptoGetAccountBalanceQuery(account_id=recipient_id)
            .execute(client)
            .token_balances
        )
        recipient_balance_after = balance_after.get(token_id, 0)
        print(
            f"Recipient's token balance after transfer: {recipient_balance_after}\n")
    except Exception as e:
        print(f" Error transferring token: {e}")
        sys.exit(1)


def revoke_kyc_from_account(client, token_id, account_id, kyc_private_key):
    """
    Revoke KYC from an account (optional bonus demonstration).
    This prevents the account from further interacting with the token.
    """
    print("\n" + "=" * 70)
    print("BONUS: Revoking KYC from account using KYC key")
    print("=" * 70)

    try:
        receipt = (
            TokenRevokeKycTransaction()
            .set_token_id(token_id)
            .set_account_id(account_id)
            .freeze_with(client)
            .sign(kyc_private_key)  # Must be signed by the KYC key
            .execute(client)
        )

        if receipt.status != ResponseCode.SUCCESS:
            print(
                f" KYC revoke failed with status: {ResponseCode(receipt.status).name}")
            return False

        print(f" KYC revoked for account {account_id} on token {token_id}")
        print(f"   The account can no longer transfer or receive this token\n")
        return True
    except Exception as e:
        print(f" Error revoking KYC: {e}\n")
        return False


def main():
    """
    Main workflow demonstrating KYC key functionality:
    1. Create a token without KYC key and show KYC operations fail
    2. Create a token with KYC key
    3. Demonstrate successful KYC operations
    4. Show how KYC affects token transfers
    """
    try:
        # Setup
        client, operator_id, operator_key = setup_client()

        # Generate a KYC key for our token
        print("=" * 70)
        print("Generating KYC key for demonstration")
        print("=" * 70)
        kyc_private_key = PrivateKey.generate("ed25519")
        print(f" KYC key generated\n")

        # ===== PART 1: Token WITHOUT KYC Key =====
        token_without_kyc = create_token_without_kyc_key(
            client, operator_id, operator_key)

        # Create test account for failed KYC attempt
        test_account_1, test_account_key_1 = create_account(
            client, operator_key)
        associate_token_to_account(
            client, token_without_kyc, test_account_1, test_account_key_1)

        # Try to grant KYC (should fail)
        attempt_kyc_without_key(client, token_without_kyc,
                                test_account_1, kyc_private_key)

        # ===== PART 2: Token WITH KYC Key =====
        token_with_kyc = create_token_with_kyc_key(
            client, operator_id, operator_key, kyc_private_key)

        # Create and associate an account for KYC testing
        print("\n" + "=" * 70)
        print("STEP 4: Creating a new account for KYC testing")
        print("=" * 70)
        test_account_2, test_account_key_2 = create_account(
            client, operator_key)
        associate_token_to_account(
            client, token_with_kyc, test_account_2, test_account_key_2)

        # Try to transfer without KYC (may fail)
        transfer_without_kyc_result = attempt_transfer_without_kyc(
            client, token_with_kyc, operator_id, test_account_2, operator_key
        )

        # Grant KYC
        grant_kyc_to_account(client, token_with_kyc,
                             test_account_2, kyc_private_key)

        # Wait a moment for state to be consistent
        time.sleep(1)

        # Transfer after KYC (should succeed)
        transfer_token_after_kyc(
            client, token_with_kyc, operator_id, test_account_2, operator_key)

        # ===== BONUS: Revoke KYC =====
        revoke_kyc_from_account(client, token_with_kyc,
                                test_account_2, kyc_private_key)

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY: KYC Key Demonstration Complete")
        print("=" * 70)
        print(f" Token without KYC key: {token_without_kyc}")
        print(f"   - KYC operations fail on this token (no KYC key defined)")
        print(f"\n Token with KYC key: {token_with_kyc}")
        print(f"   - KYC can be granted/revoked using the KYC key")
        print(f"   - Accounts must have KYC before interacting with the token")
        print(f"\n Key Takeaways:")
        print(f"   1. KYC keys are essential for token-level KYC control")
        print(f"   2. Without a KYC key, KYC operations cannot be performed")
        print(f"   3. KYC keys must sign any KYC grant/revoke transaction")
        print(f"   4. Previously granted KYC persists even if the key is removed")
        print(f"   5. KYC is independent of other keys (freeze key, admin key, etc)")
        print("=" * 70)

    except Exception as e:
        print(f" Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
