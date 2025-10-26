import pytest
import os
from datetime import timedelta
from typing import Tuple

# --- Hiero SDK Imports ---
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_info_query import TokenInfoQuery
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.transfer_transaction import TransferTransaction
from hiero_sdk_python.tokens.account_create_transaction import AccountCreateTransaction # Assuming this exists
from hiero_sdk_python.tokens.fee_assessment_method import FeeAssessmentMethod 

# Flag the file as an integration test
pytestmark = pytest.mark.integration

# --- SETUP FIXTURES ---

@pytest.fixture(scope="session")
def client() -> Client:
    """Initializes and returns a configured Hiero SDK Client for the Testnet."""
    # Ensure OPERATOR_ID and OPERATOR_KEY are set in your environment
    operator_id_str = os.environ.get("OPERATOR_ID")
    operator_key_str = os.environ.get("OPERATOR_KEY")
    
    if not operator_id_str or not operator_key_str:
        pytest.fail("FATAL: OPERATOR_ID or OPERATOR_KEY env vars missing.")
        
    try:
        # NOTE: Replace 'forTestnet' if you use a different network
        sdk_client = Client.forTestnet().setOperator(
            AccountId.fromString(operator_id_str), 
            PrivateKey.fromString(operator_key_str)
        )
        return sdk_client
    except Exception as e:
        pytest.fail(f"Client initialization failed: {e}")

@pytest.fixture
def fresh_treasury(client: Client) -> Tuple[AccountId, PrivateKey]:
    """Creates and returns a new account to act as treasury and fee collector."""
    treasury_key = PrivateKey.generate() # Generate a new key pair
    
    try:
        # Create account with a small starting balance (10 HBAR)
        tx = AccountCreateTransaction(initialBalance=10)
        tx.setKey(treasury_key.publicKey)

        # Execute transaction and get the new AccountId
        treasury_id = tx.freezeWith(client).sign(treasury_key).execute(client).getReceipt().accountId
        
        # Verify creation was successful
        assert treasury_id is not None
        
        yield treasury_id, treasury_key
        
        # TODO: Implement account deletion in a final tear-down if necessary
        
    except Exception as e:
        pytest.fail(f"Failed to create fresh treasury account: {e}")

# --- CORE INTEGRATION TEST CASES ---

def test_token_creation_with_fixed_fee(client: Client, fresh_treasury: Tuple[AccountId, PrivateKey]):
    """Verifies a FixedFee is correctly applied and queryable on the network."""
    treasury_id, treasury_key = fresh_treasury
    fee_collector_id = treasury_id # Use treasury as collector for simplicity
    
    # 1. Define the Fixed Fee (e.g., 5 units of HBAR)
    fixed_fee = CustomFixedFee(
        amount=5,
        denominatingTokenId=None, # None for HBAR
        feeCollectorAccountId=fee_collector_id,
        allCollectorsAreExempt=False
    )
    
    # 2. Create the Token
    tx = TokenCreateTransaction(
        tokenName="FixedFeeTest",
        tokenSymbol="FFT",
        initialSupply=1000,
        treasuryAccountId=treasury_id,
        adminKey=treasury_key,
        supplyKey=treasury_key,
        customFees=[fixed_fee] # Apply the custom fee
    )
    
    # Execute and get Token ID
    token_id = tx.freezeWith(client).sign(treasury_key).execute(client).getReceipt().tokenId
    assert token_id is not None
    
    # 3. Verification Query (Crucial)
    token_info = TokenInfoQuery(tokenId=token_id).execute(client)
    
    # 4. Assertions
    assert len(token_info.customFees) == 1
    retrieved_fixed_fee = token_info.customFees[0]
    
    # Assert type and values match the definition
    assert isinstance(retrieved_fixed_fee, CustomFixedFee)
    assert retrieved_fixed_fee.amount == 5
    assert retrieved_fixed_fee.feeCollectorAccountId == fee_collector_id

def test_token_creation_with_fractional_fee(client: Client, fresh_treasury: Tuple[AccountId, PrivateKey]):
    """Verifies a FractionalFee is correctly applied and queryable on the network."""
    treasury_id, treasury_key = fresh_treasury
    fee_collector_id = treasury_id

    # 1. Define the Fractional Fee (1/10th, min 1, max 10)
    fractional_fee = CustomFractionalFee(
        numerator=1,
        denominator=10,
        minAmount=1,
        maxAmount=10,
        assessmentMethod=FeeAssessmentMethod.INCLUSIVE,
        feeCollectorAccountId=fee_collector_id,
    )
    
    # 2. Create the Token
    tx = TokenCreateTransaction(
        tokenName="FractionalFeeTest",
        tokenSymbol="FRT",
        initialSupply=1000,
        treasuryAccountId=treasury_id,
        adminKey=treasury_key,
        supplyKey=treasury_key,
        customFees=[fractional_fee]
    )
    
    token_id = tx.freezeWith(client).sign(treasury_key).execute(client).getReceipt().tokenId
    assert token_id is not None
    
    # 3. Verification Query
    token_info = TokenInfoQuery(tokenId=token_id).execute(client)
    
    # 4. Assertions
    retrieved_fractional_fee = token_info.customFees[0]
    assert isinstance(retrieved_fractional_fee, CustomFractionalFee)
    assert retrieved_fractional_fee.numerator == 1
    assert retrieved_fractional_fee.denominator == 10
    assert retrieved_fractional_fee.minAmount == 1
    
# TODO: Add a comprehensive test_fee_collection_on_token_transfer to fully cover the module.
# This test requires transferring tokens and querying account balances before and after.