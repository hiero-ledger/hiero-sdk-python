# uv run -m examples.account.account_create_transaction_evm_alias
# python -m examples.account.account_create_transaction_evm_alias
"""
Example: Create an account using an EVM-style alias (evm_address).
"""

import os
import sys
import json
from dotenv import load_dotenv

from examples.utils import info_to_dict

from hiero_sdk_python import (
    Client,
    PrivateKey,
    AccountCreateTransaction,
    AccountInfoQuery,
    Network,
    AccountId,
    Hbar,
)

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # Get the operator account from the .env file
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        # Set the operator (payer) account for the client
        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client
    except Exception:
        print("Error: Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

def generate_alias_key():
    print("\nSTEP 1: Generating a new ECDSA key pair for the account alias...")
    private_key = PrivateKey.generate('ecdsa')
    public_key = private_key.public_key()
    evm_address = public_key.to_evm_address()
    if evm_address is None:
        print("❌ Error: Failed to generate EVM address from public key.")
        sys.exit(1)
    print(f"✅ Generated new ECDSA key pair. EVM Address (alias): {evm_address}")
    return private_key, public_key, evm_address

def create_account_with_alias(client, private_key, public_key, evm_address):
    print("\nSTEP 2: Creating the account with the EVM address alias...")
    transaction = (
        AccountCreateTransaction()
        .set_key(public_key)
        .set_initial_balance(Hbar(5))
        .set_alias(evm_address)
    )

    # Sign the transaction with both the new key and the operator key
    transaction = transaction.freeze_with(client) \
        .sign(private_key) \
        .sign(client.operator_private_key)

    # Execute the transaction
    response = transaction.execute(client)
    new_account_id = response.account_id
    print(f"✅ Account created with ID: {new_account_id}\n")
    return new_account_id

def fetch_account_info(client, account_id):
    return AccountInfoQuery().set_account_id(account_id).execute(client)

def print_account_summary(account_info):
    # Print the account info
    out = info_to_dict(account_info)
    print("🧾 Account Info:")
    print(json.dumps(out, indent=2) + "\n")
    if account_info.contract_account_id is not None:
        print(f"✅ Contract Account ID (alias): {account_info.contract_account_id}")
    else:
        print("❌ Error: Contract Account ID (alias) does not exist.")

def main():
    client = setup_client()
    try:
        private_key, public_key, evm_address = generate_alias_key()
        
        new_account_id = create_account_with_alias(client, private_key, public_key, evm_address)
        
        account_info = fetch_account_info(client, new_account_id)
        
        print_account_summary(account_info)

    except Exception as error:
        print(f"❌ Error: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()