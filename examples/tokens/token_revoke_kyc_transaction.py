"""
uv run examples/tokens/token_revoke_kyc_transaction.py.py
python examples/tokens/token_revoke_kyc_transaction.py.py

"""
import os
import sys
from dotenv import load_dotenv

from hiero_sdk_python import (
    Client,
    AccountId,
    PrivateKey,
    Network,
)
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction

load_dotenv()
network_name = os.getenv('NETWORK', 'testnet').lower()

def setup_client():
    """Initialize and set up the client with operator account"""
    network = Network(network_name)
    print(f"Connecting to Hedera {network_name} network!")
    client = Client(network)

    operator_id = AccountId.from_string(os.getenv('OPERATOR_ID', ''))
    operator_key = PrivateKey.from_string(os.getenv('OPERATOR_KEY', ''))
    client.set_operator(operator_id, operator_key)
    print(f"Client set up with operator id {client.operator_account_id}")

    return client, operator_id, operator_key

def create_fungible_token(client, operator_id, operator_key, kyc_private_key):
    """Create a fungible token"""
    receipt = (
        TokenCreateTransaction()
        .set_token_name("MyExampleFT")
        .set_token_symbol("EXFT")
        .set_decimals(2)
        .set_initial_supply(100)
        .set_treasury_account_id(operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1000)
        .set_admin_key(operator_key)
        .set_supply_key(operator_key)
        .set_kyc_key(kyc_private_key)  # Required key for granting/revoking KYC approval to accounts
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Fungible token creation failed with status: {ResponseCode(receipt.status).name}")
        sys.exit(1)
    
    token_id = receipt.token_id
    print(f"Fungible token created with ID: {token_id}")
    
    return token_id

def associate_token(client, token_id, account_id, account_private_key):
    """Associate a token with an account"""
    associate_transaction = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(client)
        .sign(account_private_key) # Has to be signed by new account's key
    )
    
    receipt = associate_transaction.execute(client)
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token association failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print("Token successfully associated with account")

def create_test_account(client):
    """Create a new account for testing"""
    # Generate private key for new account
    new_account_private_key = PrivateKey.generate()
    new_account_public_key = new_account_private_key.public_key()
    
    # Create new account with initial balance of 1 HBAR
    transaction = (
        AccountCreateTransaction()
        .set_key(new_account_public_key)
        .set_initial_balance(Hbar(1))
        .freeze_with(client)
    )
    
    receipt = transaction.execute(client)
    
    # Check if account creation was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Account creation failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    # Get account ID from receipt
    account_id = receipt.account_id
    print(f"New account created with ID: {account_id}")
    
    return account_id, new_account_private_key

def grant_kyc(client, token_id, account_id, kyc_private_key):
    """Grant KYC to an account"""
    receipt = (
        TokenGrantKycTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
        .sign(kyc_private_key)  # Has to be signed by the KYC key
        .execute(client)
    )
    
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token grant KYC failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Granted KYC for account {account_id} on token {token_id}")

def token_revoke_kyc():
    """
    Demonstrates the token revoke KYC functionality by:
    1. Setting up client with operator account
    2. Creating a fungible token with KYC key
    3. Creating a new account
    4. Associating the token with the new account
    5. Granting KYC to the new account
    6. Revoking KYC from the new account
    """
    client, operator_id, operator_key = setup_client()
    
    # Create KYC key
    kyc_private_key = PrivateKey.generate_ed25519()
    
    # Create a fungible token with KYC key
    token_id = create_fungible_token(client, operator_id, operator_key, kyc_private_key)
    
    # Create a new account
    account_id, account_private_key = create_test_account(client)
    
    # Associate the token with the new account
    associate_token(client, token_id, account_id, account_private_key)
    
    # Grant KYC to the new account first
    grant_kyc(client, token_id, account_id, kyc_private_key)
    
    # Revoke KYC from the new account
    receipt = (
        TokenRevokeKycTransaction()
        .set_token_id(token_id)
        .set_account_id(account_id)
        .freeze_with(client)
        .sign(kyc_private_key)  # Has to be signed by the KYC key
        .execute(client)
    )
    
    # Check if the transaction was successful
    if receipt.status != ResponseCode.SUCCESS:
        print(f"Token revoke KYC failed with status: {ResponseCode.get_name(receipt.status)}")
        sys.exit(1)
    
    print(f"Revoked KYC for account {account_id} on token {token_id}")

if __name__ == "__main__":
    token_revoke_kyc() 