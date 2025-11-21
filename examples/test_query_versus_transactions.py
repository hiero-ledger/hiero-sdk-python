import sys
import os
import dotenv
from hiero_sdk_python import Client, PrivateKey, ResponseCode
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.client.network import Network
 
dotenv.load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()


def setup_client():
    """Initialize and return a Hiero SDK client based on environment variables."""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network")
    client = Client(network)

    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
        client.set_operator(operator_id, operator_key)
        print(f"Client set-up with operator id {client.operator_account_id}.")
        return client, operator_id, operator_key

    except (TypeError, ValueError):
        print("Error: please check OPERATOR_ID and OPERATOR_KEY in your environment file.")
        sys.exit(1)


def hbar_precheck_failure(client, operator, fake_account):
    """Test HBAR transfer that fails precheck due to insufficient balance."""
    print("\n-- HBAR Transfer Precheck Failure --")
    try:
        bad_hbar = (
            TransferTransaction()
            .add_hbar_transfer(operator, -99999999999999)
            .add_hbar_transfer(fake_account, 99999999999999)
        )
        bad_hbar.execute(client)
    except Exception as e:
        print(f"✔ Correct: HBAR transfer precheck failed as expected: {e}")


def token_transfer_receipt_failure(client, operator, fake_account, fake_token):
    """Test token transfer that passes precheck but fails in receipt."""
    print("\n-- Token Transfer Receipt Failure --")
    try:
        bad_token_transfer = (
            TransferTransaction()
            .add_token_transfer(fake_token, operator, -1)
            .add_token_transfer(fake_token, fake_account, 1)
        )
        receipt = bad_token_transfer.execute(client)
        status = ResponseCode(receipt.status).name
        print(f"Token transfer ResponseCode: {status}")

        if status != "SUCCESS":
            print("✔ Correct: Token transfer failed via receipt without exception")
        else:
            print("❌ ERROR: Token transfer unexpectedly succeeded")
    except Exception as e:
        print(f"❌ Unexpected exception during token transfer: {e}")


def nft_transfer_receipt_failure(client, operator, fake_account, fake_nft_token):
    """Test NFT transfer that fails in receipt (operator does not own NFT)."""
    print("\n-- NFT Transfer Receipt Failure --")
    try:
        bad_nft_transfer = (
            TransferTransaction()
            .add_nft_transfer(fake_nft_token, operator, fake_account, 1)
        )
        receipt = bad_nft_transfer.execute(client)
        status = ResponseCode(receipt.status).name
        print(f"NFT transfer ResponseCode: {status}")

        if status != "SUCCESS":
            print("✔ Correct: NFT transfer failed via receipt without exception")
        else:
            print("❌ ERROR: NFT transfer unexpectedly succeeded")
    except Exception as e:
        print(f"✔ Correct: NFT transfer precheck failed as expected: {e}")


def query_failure(client):
    """Queries should throw an exception if something is invalid."""
    print("\n=== Testing Query Failures ===")
    fake_token = TokenId.from_string("0.0.9999999")
    try:
        TokenInfoQuery().set_token_id(fake_token).execute(client)
        print("❌ ERROR: Query unexpectedly succeeded!")
    except Exception as e:
        print(f"✔ Correct: Query threw exception: {e}")


def main():
    client, operator_id, operator_key = setup_client()

    fake_account = AccountId.from_string("0.0.12345")
    fake_token = TokenId.from_string("0.0.9999999")
    fake_nft_token = TokenId.from_string("0.0.8888888")

    hbar_precheck_failure(client, client.operator_account_id, fake_account)
    token_transfer_receipt_failure(client, client.operator_account_id, fake_account, fake_token)
    nft_transfer_receipt_failure(client, client.operator_account_id, fake_account, fake_nft_token)
    query_failure(client)


if __name__ == "__main__":
    main()
