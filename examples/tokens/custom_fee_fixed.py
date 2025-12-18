"""
Run with:
uv run examples/tokens/custom_fixed_fee.py
python examples/tokens/custom_fixed_fee.py
"""

import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    AccountId,
    Client,
    PrivateKey,
    Network,
    TokenCreateTransaction,
    TokenType,
    SupplyType as TokenSupplyType,
    TokenInfoQuery,
    CustomFixedFee,
    Hbar
)

load_dotenv()

def setup_client():
    """Setup Client with specific TLS settings for local testing"""

    network_name = os.getenv("HEDERA_NETWORK", "testnet")
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    # --- TLS
    client.set_transport_security(False)
    client.set_verify_certificates(False)

    try:
        operator_id_str = os.getenv('OPERATOR_ID')
        operator_key_str = os.getenv('OPERATOR_KEY')

        if not operator_id_str or not operator_key_str:
            raise ValueError("Environment variables OPERATOR_ID or OPERATOR_KEY are missing.")

        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)

        client.set_operator(operator_id, operator_key)
        print(f"Client set up with operator id {client.operator_account_id}")
        return client, operator_key
    except (TypeError, ValueError) as e:
        print(f"Error: {e}")
        print("Please check OPERATOR_ID and OPERATOR_KEY in your .env file.")
        sys.exit(1)

def custom_fixed_fee_example():
    """

    Demonstrates how to create a token with a Custom Fixed Fee.

    """
    client, operator_key = setup_client()
    operator_id = client.operator_account_id

    print("\n--- Creating Custom Fixed Fee ---")

    fixed_fee = CustomFixedFee(
        amount=Hbar(1).to_tinybars(), 
        fee_collector_account_id=operator_id,
        all_collectors_are_exempt=False
    )

    print(f"Fee Definition: Pay 1 HBAR to {operator_id}")

    print("\n--- Creating Token with Fee ---")
    transaction = (
        TokenCreateTransaction()
        .set_token_name("Fixed Fee Example Token")
        .set_token_symbol("FFET")
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(TokenSupplyType.INFINITE)
        .set_initial_supply(1000)
        .set_decimals(2)
        .set_treasury_account_id(operator_id)
        .set_admin_key(operator_key)
        .set_custom_fees([fixed_fee]) 
        .freeze_with(client)
        .sign(operator_key)
    )

    try:
        receipt = transaction.execute(client)
        token_id = receipt.token_id
        print(f"Token created successfully: {token_id}")

        print("\n--- Verifying Fee on Network ---")
        token_info = TokenInfoQuery().set_token_id(token_id).execute(client)

        retrieved_fees = token_info.custom_fees
        if retrieved_fees:
            print(f"Success! Found {len(retrieved_fees)} custom fee(s) on token.")
            for fee in retrieved_fees:
                print(f"Fee Collector: {fee.fee_collector_account_id}")
                print(f"Fee Details: {fee}")
        else:
            print("Error: No custom fees found on the token.")

    except Exception as e:
        print(f"Transaction failed: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    custom_fixed_fee_example()