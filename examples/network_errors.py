"""
This is an example of how to create a finite fungible token and test network error scenarios.
It:
1. Loads environment variables.
2. Sets up a client and creates a token with the given parameters.
3. Executes the token creation and prints the result.
4. Includes tests for handling invalid node ports during transaction submission and receipt queries.
"""
import os
import sys
from dotenv import load_dotenv
from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    TokenCreateTransaction,
    Network,
    TransactionGetReceiptQuery,
)
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.node import _Node
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType

# Load environment variables from .env file
load_dotenv()

def create_token_fungible_finite(client: Client, operator_id: AccountId, operator_key: PrivateKey):
    """Function to create a finite fungible token. Now returns the transaction object."""
    transaction = (
        TokenCreateTransaction()
        .set_token_name("FiniteFungibleToken")
        .set_token_symbol("FFT")
        .set_decimals(2)
        .set_initial_supply(10)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .freeze_with(client)
    )

    transaction.sign(operator_key)

    try:
        receipt = transaction.execute(client)
        if receipt and receipt.token_id:
            print(f"Finite fungible token created with ID: {receipt.token_id}")
            return transaction # Return the whole transaction object
        else:
            print("Finite fungible token creation failed: Token ID not returned in receipt.")
            sys.exit(1)
    except Exception:
        # Re-raise the exception but also return the transaction object
        # so the transaction ID can be accessed in the test.
        raise

def test_valid_tx_invalid_receipt_port():
    """
    Submits a transaction to a valid node, then attempts to get the receipt from a valid IP but an invalid port.
    """
    print("\n--- Running Scenario 1: Valid TX, Invalid Receipt Port ---")
    valid_network = Network(network='testnet')
    client = Client(valid_network)
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    client.set_operator(operator_id, operator_key)

    print("Submitting transaction to a valid node...")
    transaction = create_token_fungible_finite(client, operator_id, operator_key)
    print(f"Transaction submitted successfully. Transaction ID: {transaction.transaction_id}")

    print("\nAttempting to query receipt from a valid IP with an invalid port...")
    valid_node = valid_network.nodes[0]
    invalid_address_str = f"{valid_node._address._address}:50219"

    invalid_network_nodes = [_Node(valid_node._account_id, invalid_address_str, None)]
    invalid_network = Network(nodes=invalid_network_nodes)
    invalid_client = Client(invalid_network)
    invalid_client.set_operator(operator_id, operator_key)

    try:
        query = TransactionGetReceiptQuery().set_transaction_id(transaction.transaction_id)
        query.execute(invalid_client)
    except MaxAttemptsError as e:
        print(f"Successfully caught expected error when querying receipt from invalid port: {e}")
    except Exception as e:
        print(f"Caught an unexpected error: {e}")


def test_invalid_tx_port_and_receipt_query():
    """
    Attempts to send a transaction to an incorrect port, confirms it fails,
    then queries for the receipt on a valid port to confirm it was never received.
    """
    print("\n--- Running Scenario 2: Invalid TX Port and Subsequent Receipt Query ---")
    base_network = Network(network='testnet')
    valid_node = base_network.nodes[0]
    invalid_address_str = f"{valid_node._address._address}:50219"

    invalid_network_nodes = [_Node(valid_node._account_id, invalid_address_str, None)]
    invalid_network = Network(nodes=invalid_network_nodes)
    invalid_client = Client(invalid_network)
    
    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
    operator_key = PrivateKey.from_string_ed25519(os.getenv('OPERATOR_KEY'))
    invalid_client.set_operator(operator_id, operator_key)

    # Prepare the transaction so we can get its ID even if execute fails
    transaction = (
        TokenCreateTransaction()
        .set_token_name("FiniteFungibleToken")
        .set_token_symbol("FFT")
        .set_decimals(2)
        .set_initial_supply(10)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(100)
        .freeze_with(invalid_client)
    )
    transaction.sign(operator_key)
    transaction_id_for_failed_tx = transaction.transaction_id

    print(f"Attempting to submit transaction {transaction_id_for_failed_tx} to an invalid port...")
    try:
        transaction.execute(invalid_client)
    except MaxAttemptsError as e:
        print(f"Successfully caught expected network error: {e}")
        
        # Now, attempt to get the receipt from a VALID network
        print("\nQuerying for the receipt on a valid network to confirm it was never received...")
        valid_client = Client(base_network)
        valid_client.set_operator(operator_id, operator_key)
        
        try:
            query = TransactionGetReceiptQuery().set_transaction_id(transaction_id_for_failed_tx)
            query.execute(valid_client)
        except MaxAttemptsError as receipt_error:
            # The SDK retries on RECEIPT_NOT_FOUND until it hits the max attempts
            print(f"Successfully caught expected error: The receipt was not found on the network. Error: {receipt_error}")
        except Exception as receipt_error:
            print(f"Caught an unexpected error while querying for the receipt: {receipt_error}")

    except Exception as e:
        print(f"Caught an unexpected error during transaction submission: {e}")

if __name__ == "__main__":
    test_valid_tx_invalid_receipt_port()
    test_invalid_tx_port_and_receipt_query()