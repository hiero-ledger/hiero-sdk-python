"""
Transfer HBAR to a Hedera account using an EVM (public) address.

Steps:
1. Create an ECDSA private key
2. Extract the ECDSA public key
3. Derive the Ethereum (EVM) address
4. Transfer HBAR to the EVM address (auto-creates a hollow account)
5. Get the child receipt to obtain the new Hedera AccountId
6. Query AccountInfo to verify it is a hollow account (no public key)
7. (Optional) Complete the hollow account by signing a transaction
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
    TransferTransaction,
    Hbar,
    ResponseCode,
    AccountInfoQuery,
    TransactionGetReceiptQuery,
)

# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

load_dotenv()

NETWORK_NAME = os.getenv("NETWORK", "testnet").lower()
OPERATOR_ID = os.getenv("OPERATOR_ID")
OPERATOR_KEY = os.getenv("OPERATOR_KEY")


def setup_client() -> Client:
    """
    Initialize and return a Hedera Client using operator credentials.
    """
    if not OPERATOR_ID or not OPERATOR_KEY:
        print("OPERATOR_ID or OPERATOR_KEY not set in .env")
        sys.exit(1)

    network = Network(NETWORK_NAME)
    client = Client(network)

    try:
        operator_id = AccountId.from_string(OPERATOR_ID)
        operator_key = PrivateKey.from_string(OPERATOR_KEY)
    except ValueError as e:
        print(f"Invalid operator credentials: {e}")
        sys.exit(1)

    client.set_operator(operator_id, operator_key)

    print(f"Connected to {NETWORK_NAME}")
    print(f"Operator: {operator_id}")

    return client



def transfer_hbar_to_evm_address(client: Client, evm_address: bytes) -> AccountId:
    """
    Transfer HBAR to an EVM address.
    This auto-creates a hollow account if the address does not already exist.
    """
    print("\nSTEP 4: Transferring HBAR to EVM address...")

    recipient_id = AccountId.from_evm_address(
        evm_address=evm_address,
        shard=0,
        realm=0,
    )

    tx = (
        TransferTransaction()
        .add_hbar_transfer(client.operator_account_id, Hbar(-1).to_tinybars())
        .add_hbar_transfer(recipient_id, Hbar(1).to_tinybars())
    )

    tx_response = tx.execute(client)

    receipt = (
        TransactionGetReceiptQuery()
        .set_transaction_id(tx_response.transaction_id)
        .set_include_children(True)
        .execute(client)
    )

    if receipt.status != ResponseCode.SUCCESS:
        raise RuntimeError(f"Transfer failed: {receipt.status}")

    # Child receipt contains the auto-created account
    new_account_id = receipt.children[0].account_id
    print(f"New account created: {new_account_id}")

    return new_account_id


def show_account_info(client: Client, account_id: AccountId) -> None:
    """
    Query AccountInfo and print whether the account is hollow or complete.
    """
    info = (
        AccountInfoQuery()
        .set_account_id(account_id)
        .execute(client)
    )

    print(info)
    # if info.key is None:
    #     print(f"Account {account_id} has no public key → hollow account")
    # else:
    #     print(f"Account {account_id} has public key → complete account")
    #     print(f"Public key: {info.key}")



def main():
    client = setup_client()
    client.set_transport_security(False)

    try:
        private_key = PrivateKey.generate("ecdsa")
        print(f"\nSTEP 1: Generated ECDSA private key")

        public_key = private_key.public_key()
        print("STEP 2: Extracted public key")

        evm_address = public_key.to_evm_address()
        print(f"STEP 3: EVM address: 0x{evm_address.to_string()}")

        new_account_id = transfer_hbar_to_evm_address(client, evm_address)

        print("\nSTEP 6: Querying account info...")
        show_account_info(client, new_account_id)

    finally:
        client.close()


if __name__ == "__main__":
    main()
