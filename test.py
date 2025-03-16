"""
test.py

This script tests various functionalities of the Hiero SDK for the Hedera network, including:

- Loading operator credentials from environment variables
- Creating new accounts
- Querying account balances
- Creating fungible and non-fungible tokens
- Associating and dissociating tokens with accounts
- Transferring tokens between accounts
- Freezing and deleting tokens
- Minting additional supply for tokens
- Creating, updating, querying, and deleting topics

Each is designed to validate expected behavior of each transaction type using the Hiero SDK.

Usage:
    Run the script to execute all test cases sequentially.
"""
import os
import sys
from dotenv import load_dotenv

# Client and network-related imports
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.client.client import Client

# Account-related imports
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction

# Cryptographic imports
from hiero_sdk_python.crypto.private_key import PrivateKey

# Token-related imports
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_create_transaction import (
    TokenCreateTransaction,
    TokenParams,
    TokenKeys
)
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction

# Transaction-related imports
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

# Topic related imports
# from hiero_sdk_python.consensus.topic_id import TopicId #Check
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction
)
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction

# Query-related imports
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery

# Response handling
from hiero_sdk_python.response_code import ResponseCode

load_dotenv()

def load_operator_credentials():
    """Load operator credentials from environment variables."""
    try:
        operator_id = AccountId.from_string(os.getenv('OPERATOR_ID'))
        operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY'))
    except Exception as e:
        print(f"Error parsing operator credentials: {e}")
        sys.exit(1)
    return operator_id, operator_key

def create_new_account(client, initial_balance=100000000):
    """Tests account creation"""
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()

    transaction = AccountCreateTransaction(
        key=new_account_public_key,
        initial_balance=initial_balance,
        memo="Recipient Account"
    )
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
        new_account_id = receipt.accountId
        if new_account_id is not None:
            print(f"Account creation successful. New Account ID: {new_account_id}")
            print(f"New Account Private Key: {new_account_private_key.to_string()}")
            print(f"New Account Public Key: {new_account_public_key.to_string()}")
        else:
            raise Exception("AccountID not found in receipt. Account may not have been created.")
    except Exception as e:
        print(f"Account creation failed: {str(e)}")
        sys.exit(1)

    return new_account_id, new_account_private_key


def query_balance(client, account_id):
    """Tests account balance query"""
    balance = CryptoGetAccountBalanceQuery(account_id=account_id).execute(client)
    print(f"Account {account_id} balance: {balance.hbars}")
    return balance

def create_fungible_token(client, operator_id, admin_key, supply_key, freeze_key): #token params and keys?
    """Tests creation of a fungible token"""

    # Creating TokenParams
    token_params = TokenParams(
        token_name="ExampleToken",
        token_symbol="EXT",
        decimals=2,
        initial_supply=1000,
        treasury_account_id=operator_id,
        token_type=TokenType.FUNGIBLE_COMMON,
    )

    # Creating TokenKeys
    token_keys = TokenKeys(
        admin_key=admin_key,
        supply_key=supply_key,
        freeze_key=freeze_key
    )

    # Creating the transaction using TokenParams and TokenKeys
    transaction = TokenCreateTransaction(token_params, token_keys)

    # Freeze the transaction
    transaction.freeze_with(client)

    # Sign the transaction
    transaction.sign(client.operator_private_key) # Required to sign with operator (treasury)
    # Sign with admin key only if it's provided
    if admin_key:
        transaction.sign(admin_key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Fungible Token creation failed: {str(e)}")
        sys.exit(1)

    if not receipt.tokenId:
        print("Fungible Token creation failed: Token ID not returned in receipt.")
        sys.exit(1)

    token_id = receipt.tokenId
    print(f"Fungible Token creation successful. Token ID: {token_id}")
    return token_id

def create_nft_token(client, operator_id, admin_key, supply_key, freeze_key):
    """Tests creation of a non-fungible unique token"""

    # Creating TokenParams
    token_params = TokenParams(
        token_name="ExampleNFTToken",
        token_symbol="EXTNFT",
        decimals=0,
        initial_supply=0,
        treasury_account_id=operator_id,
        token_type=TokenType.NON_FUNGIBLE_UNIQUE,
    )

    # Creating TokenKeys
    token_keys = TokenKeys(
        admin_key=admin_key,
        supply_key=supply_key,
        freeze_key=freeze_key
    )

    # Creating the transaction using TokenParams and TokenKeys
    transaction = TokenCreateTransaction(token_params, token_keys)

    # Freeze the transaction
    transaction.freeze_with(client)

    # Sign the transaction
    transaction.sign(client.operator_private_key) # Required to sign with operator (treasury)
    # Sign with admin key only if it's provided
    if admin_key:
        transaction.sign(admin_key)
        
    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Non-Fungible Token creation failed: {str(e)}")
        sys.exit(1)

    if not receipt.tokenId:
        print("Non-Fungible Token creation failed: Token ID not returned in receipt.")
        sys.exit(1)

    token_id = receipt.tokenId
    print(f"Non-Fungible Token creation successful. Token ID: {token_id}")
    return token_id

def associate_token(client, recipient_id, recipient_private_key, token_ids):
    """Tests token association"""
    transaction = TokenAssociateTransaction(
        account_id=recipient_id,
        token_ids=token_ids
    )
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(recipient_private_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token association failed with status: {status_message}")
        print("Token association successful.")
    except Exception as e:
        print(f"Token association failed: {str(e)}")
        sys.exit(1)

def dissociate_token(client, recipient_id, recipient_private_key, token_id):
    """Dissociate the specified token with the recipient account."""
    transaction =  TokenDissociateTransaction(
        account_id = recipient_id,
        token_ids = token_id)
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(recipient_private_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token dissociation failed with status: {status_message}")
        print("Token dissociation successful.")
    except Exception as e:
        print(f"Token dissociation failed: {str(e)}")
        sys.exit(1)

def transfer_token(client, source_id, source_private_key, recipient_id, token_id):
    """Transfer the specified token to the recipient account."""
    transaction = (
        TransferTransaction()
        .add_token_transfer(token_id, source_id, -1)
        .add_token_transfer(token_id, recipient_id, 1)
        .freeze_with(client)
    )
    transaction.sign(source_private_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token transfer failed with status: {status_message}")
        print("Token transfer successful.")
    except Exception as e:
        print(f"Token transfer failed: {str(e)}")
        sys.exit(1)


def delete_token(client, token_id, admin_key):
    """Tests token deletion"""
    transaction = TokenDeleteTransaction(token_id=token_id)
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(admin_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token deletion failed with status: {status_message}")
        print("Token deletion successful.")
    except Exception as e:
        print(f"Token deletion failed: {str(e)}")
        sys.exit(1)

def freeze_token(client, token_id, account_id, freeze_key):
    """Tests token freezing from account"""
    transaction = TokenFreezeTransaction(token_id=token_id, account_id=account_id)
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(freeze_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token freeze failed with status: {status_message}")
        print("Token freeze successful.")
    except Exception as e:
        print(f"Token freeze failed: {str(e)}")
        sys.exit(1)

def mint_fungible_token(client, token_id, supply_key, amount=2000):
    """Tests fungible token minting"""
    transaction = TokenMintTransaction(token_id=token_id, amount=amount)
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(supply_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token minting failed with status: {status_message}")
        print("Token minting successful.")
    except Exception as e:
        print(f"Token minting failed: {str(e)}")
        sys.exit(1)

def mint_nft_token(client, token_id, supply_key, metadata=[b"Token A"]):
    """Tests non-fungible token minting"""
    transaction = TokenMintTransaction(token_id=token_id, metadata=metadata  )
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)
    transaction.sign(supply_key)

    try:
        receipt = transaction.execute(client)
        if receipt.status != ResponseCode.SUCCESS:
            status_message = ResponseCode.get_name(receipt.status)
            raise Exception(f"Token minting failed with status: {status_message}")
        print("Token minting successful.")
    except Exception as e:
        print(f"Token minting failed: {str(e)}")
        sys.exit(1)

def create_topic(client):
    """Tests creating a topic"""
    key = client.operator_private_key
    transaction = TopicCreateTransaction(
        memo="Python SDK created topic",
        admin_key=key.public_key()
    )
    transaction.freeze_with(client)
    transaction.sign(key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Topic creation failed: {str(e)}")
        sys.exit(1)

    if not receipt.topicId:
        print("Topic creation failed: Topic ID not returned in receipt.")
        sys.exit(1)

    topic_id = receipt.topicId
    print(f"Topic creation successful. Topic ID: {topic_id}")

    return topic_id


def submit_message(client, topic_id):
    """Tests submitting a message"""
    transaction = TopicMessageSubmitTransaction(
        topic_id=topic_id,
        message="Hello, Python SDK!"
    )
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Message submission failed: {str(e)}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        status_message = ResponseCode.get_name(receipt.status)
        raise Exception(f"Message submission failed with status: {status_message}")

    print("Message submitted successfully.")


def update_topic(client, topic_id):
    """Tests updating a topic"""
    key = client.operator_private_key
    transaction = TopicUpdateTransaction(
        topic_id=topic_id,
        memo="Python SDK updated topic"
    )
    transaction.freeze_with(client)
    transaction.sign(key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Topic update failed: {str(e)}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        status_message = ResponseCode.get_name(receipt.status)
        raise Exception(f"Topic update failed with status: {status_message}")

    print("Topic updated successfully.")


def delete_topic(client, topic_id):
    """Tests deleting a topic"""
    transaction = TopicDeleteTransaction(topic_id=topic_id)
    transaction.freeze_with(client)
    transaction.sign(client.operator_private_key)

    try:
        receipt = transaction.execute(client)
    except Exception as e:
        print(f"Topic deletion failed: {str(e)}")
        sys.exit(1)

    if receipt.status != ResponseCode.SUCCESS:
        status_message = ResponseCode.get_name(receipt.status)
        raise Exception(f"Topic deletion failed with status: {status_message}")

    print("Topic deleted successfully.")


def query_topic_info(client, topic_id):
    """Optional method to show how to query topic info."""
    try:
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(client)
        print(f"Topic Info: {topic_info}")
    except Exception as e:
        print(f"Failed to retrieve topic info: {str(e)}")


def main():
    """Runs the various tests in required sequence for valid testing"""

    # Load operator credentials
    operator_id, operator_key = load_operator_credentials()

    # Generate new keys for the admin, supply, and freeze to use as needed
    admin_key = PrivateKey.generate()
    supply_key = PrivateKey.generate()
    freeze_key = PrivateKey.generate()

    # Set up the client for the given network
    network_type = os.getenv('NETWORK')
    network = Network(network=network_type)
    client = Client(network)
    client.set_operator(operator_id, operator_key)

    # Test creating a new account
    recipient_id, recipient_private_key = create_new_account(client)

    # Test balance of the recipient
    query_balance(client, recipient_id)

    # Test creating a fungible token. Two are created in this case to enable subsequent operations.
    token_id_1 = create_fungible_token(client, operator_id, admin_key, supply_key, freeze_key)
    token_id_2 = create_fungible_token(client, operator_id, admin_key, supply_key, freeze_key)

    # Test creating an NFT token. Two are created in this case to enable subsequent operations.
    token_id_nft_1 = create_nft_token(client, operator_id, admin_key, supply_key, freeze_key)
    token_id_nft_2 = create_nft_token(client, operator_id, admin_key, supply_key, freeze_key)

    # Test the minting of both a fungible and nft token. One of each is sufficient.
    mint_fungible_token(client, token_id_1, supply_key)
    mint_nft_token(client, token_id_nft_1, supply_key)

    # Testing the association of fungible and nft tokens. In this case, a list of token strings to test multiple of each in one go.
    # Multiple associated tokens of each type are needed to test dissociate and delete.
    associate_token(client, recipient_id, recipient_private_key, [token_id_1, token_id_2])
    associate_token(client, recipient_id, recipient_private_key, [token_id_nft_1, token_id_nft_2])

    # Test transfering fungible and nft tokens by moving one token from the operator to the recipient.
    transfer_token(client, operator_id, operator_key, recipient_id, token_id_1)
    transfer_token(client, operator_id, operator_key, recipient_id, token_id_nft_1)

    # Test freezing fungible and nft tokens. In this case from the recipient that just received token 1.
    freeze_token(client, token_id_1, recipient_id, freeze_key)
    freeze_token(client, token_id_nft_1, recipient_id, freeze_key)

    # Test dissociating a fungible and nft token. In this case the tokens that were not transferred or frozen.
    dissociate_token(client, recipient_id, recipient_private_key, [token_id_2])
    dissociate_token(client, recipient_id, recipient_private_key, [token_id_nft_2])

    # Test deleting a fungible and nft token. In this case, the token 1 that was transferred and frozen.
    delete_token(client, token_id_1, admin_key)
    delete_token(client, token_id_nft_1, admin_key)

    # Create a topic and perform various test actions
    topic_id = create_topic(client)
    submit_message(client, topic_id)
    update_topic(client, topic_id)
    query_topic_info(client, topic_id)
    delete_topic(client, topic_id)

if __name__ == "__main__":
    main()
