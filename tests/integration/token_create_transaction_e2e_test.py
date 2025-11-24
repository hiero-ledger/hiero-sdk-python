import datetime
import pytest

from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import TokenFeeScheduleUpdateTransaction
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction, TokenParams
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token


@pytest.mark.integration
def test_integration_fungible_token_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
    finally:
        env.close()


@pytest.mark.integration
def test_integration_nft_token_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_nft_token(env)
        
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_sets_default_autorenew_values():
    """Test that when no expiration_time or auto_renew_account is explicitly provided default values are set"""
    env = IntegrationTestEnv()
    try:
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON,
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None, "TokenID not found in receipt. Token may not have been created."

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.auto_renew_period == Duration(7890000), "Token auto renew period mismatch"
        assert token_info.auto_renew_account == env.client.operator_account_id, "Token auto renew account mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_with_expiration_time():
    """Test create fungible token with expiration_time"""
    env = IntegrationTestEnv()
    try:
        expiration_time = Timestamp.from_date(datetime.datetime.now() + datetime.timedelta(days=30))
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            expiration_time=expiration_time,
            token_type=TokenType.FUNGIBLE_COMMON
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None, "TokenID not found in receipt. Token may not have been created."
    
        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)

        assert token_info.expiry.seconds == expiration_time.seconds, "Token expiry mismatch" 
        assert token_info.auto_renew_period == Duration(0)
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_auto_assigns_account_if_autorenew_period_present():
    """
    Test that if an auto_renew_period is set but auto_renew_account is not set 
    it get automatically assigns the client's operator account or transaction_id account_id.
    """
    env = IntegrationTestEnv()

    try:
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON,
        )

        receipt = TokenCreateTransaction(params).freeze_with(env.client).execute(env.client)
        assert receipt.token_id is not None,"TokenID not found in receipt. Token may not have been created."

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.auto_renew_period == Duration(7890000), "Token auto renew period mismatch" # Defaut around ~90 days
        # Client operator account if no auto_renew_account set
        assert token_info.auto_renew_account == env.client.operator_account_id, "Token auto renew account missmatch"
    finally:
        env.close()

@pytest.mark.integration
def test_fungible_token_create_with_fee_schedule_key():
    """
    Test create fungible token with fee_schedule_key
    """
    env = IntegrationTestEnv()

    try:
        fee_schedule_key = PrivateKey.generate()
        params = TokenParams(
            token_name="Hiero FT",
            token_symbol="HFT",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON
        )

        receipt = (
            TokenCreateTransaction(params)
            .set_fee_schedule_key(fee_schedule_key)
            .freeze_with(env.client)
            .execute(env.client)
        )
        assert receipt.token_id is not None

        token_id = receipt.token_id
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert token_info.fee_schedule_key.to_string() == fee_schedule_key.public_key().to_string(), "Fee schedule key missmatch"
        assert len(token_info.custom_fees) == 0

        # Validate Fee schedule key
        update_receipt = (
            TokenFeeScheduleUpdateTransaction()
            .set_token_id(token_id)
            .set_custom_fees([CustomFixedFee(amount=1, fee_collector_account_id=env.client.operator_account_id)])
            .freeze_with(env.client)
            .sign(fee_schedule_key)
            .execute(env.client)
        )

        assert update_receipt.status == ResponseCode.SUCCESS
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    
        assert len(token_info.custom_fees) == 1
        assert token_info.custom_fees[0].amount == 1
        assert token_info.custom_fees[0].fee_collector_account_id == env.client.operator_account_id

    finally:
        env.close()

@pytest.mark.integration
def test_token_create_non_custodial_flow():
    """
    Tests the full non-custodial flow:
    1. Operator builds a TX using only a PublicKey.
    2. Operator gets the transaction bytes.
    3. User (with the PrivateKey) signs the bytes.
    4. Operator executes the signed transaction.
    """
    
    env = IntegrationTestEnv()
    client = env.client

    try:
        # 1. SETUP: Create a new key pair for the "user"
        user_private_key = PrivateKey.generate_ed25519()
        user_public_key = user_private_key.public_key()

        # =================================================================
        # STEP 1 & 2: OPERATOR (CLIENT) BUILDS THE TRANSACTION
        # =================================================================
        
        tx = (
            TokenCreateTransaction()
            .set_token_name("NonCustodialToken")
            .set_token_symbol("NCT")
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_treasury_account_id(client.operator_account_id)
            .set_initial_supply(100)
            .set_admin_key(user_public_key)  # <-- The new feature!
            .freeze_with(client)
        )

        tx_bytes = tx.to_bytes()

        # =================================================================
        # STEP 3: USER (SIGNER) SIGNS THE TRANSACTION
        # =================================================================
        
        tx_from_bytes = Transaction.from_bytes(tx_bytes)
        tx_from_bytes.sign(user_private_key)

        # =================================================================
        # STEP 4: OPERATOR (CLIENT) EXECUTES THE SIGNED TX
        # =================================================================
        
        receipt = tx_from_bytes.execute(client)
        
        assert receipt is not None
        token_id = receipt.token_id
        assert token_id is not None
        
        # PROOF: Query the new token and check if the admin key matches
        token_info = TokenInfoQuery(token_id=token_id).execute(client)
        
        assert token_info.admin_key is not None
        
        # This is the STRONG assertion:
        # Compare the bytes of the key from the network
        # with the bytes of the key we originally used.
        admin_key_bytes = token_info.admin_key.to_bytes_raw()
        public_key_bytes = user_public_key.to_bytes_raw()
        
        assert admin_key_bytes == public_key_bytes

    finally:
        # Clean up the environment
        env.close()

def test_fungible_token_create_with_metadata():
    """
    Test creating a fungible token with on-ledger metadata and verifying
    the metadata via TokenInfoQuery.
    """
    env = IntegrationTestEnv()

    try:
        # On-ledger token metadata bytes (must not exceed 100 bytes)
        metadata = b"Integration test token metadata"

        params = TokenParams(
            token_name="Hiero FT Metadata",
            token_symbol="HFTM",
            initial_supply=1,
            treasury_account_id=env.client.operator_account_id,
            token_type=TokenType.FUNGIBLE_COMMON,
        )

        # Build, freeze and execute the token creation transaction with metadata
        receipt = (
            TokenCreateTransaction(params)
            .set_metadata(metadata)
            .freeze_with(env.client)
            .execute(env.client)
        )

        assert receipt.token_id is not None, "TokenID not found in receipt. Token may not have been created."

        token_id = receipt.token_id

        # Query the created token to verify that metadata has been set
        token_info = TokenInfoQuery(token_id=token_id).execute(env.client)

        assert token_info.metadata == metadata, "Token metadata mismatch"

    finally:
        env.close()
