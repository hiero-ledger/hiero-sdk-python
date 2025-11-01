import pytest
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
# --- FIX APPLIED HERE ---
from hiero_sdk_python.query.token_info_query import TokenInfoQuery 
# ------------------------
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.exceptions.transaction_exception import TransactionException
from hiero_sdk_python.tokens.custom_fractional_fee import CustomFractionalFee
from hiero_sdk_python.tokens.custom_royalty_fee import CustomRoyaltyFee
from hiero_sdk_python.hbar import Hbar

# Import utility functions and fixtures from utils_for_test.py
from tests.integration.utils_for_test import env, create_fungible_token, create_nft_token
@pytest.mark.integration
def test_custom_fee_can_execute_on_network(env):
    """
    Tests successful execution of a TokenCreateTransaction with a custom fee.
    Verifies base CustomFee fields (collector ID, exempt flag) are correctly
    serialized and retrieved from the Hedera network via TokenInfoQuery.
    """
    
    collector_account = env.create_account(initial_hbar=1.0)
    
    fixed_fee_amount = 50
    custom_fee = (
        CustomFixedFee(
            amount=fixed_fee_amount, 
            denominated_token_id=None, # HBAR fixed fee
        )
        .set_fee_collector_account_id(collector_account.id)
        .set_all_collectors_are_exempt(False)
    )

    token_id = create_fungible_token(
        env,
        custom_fees=[custom_fee]
    )

    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert token_info is not None
    assert len(token_info.custom_fees) == 1
    retrieved_fee = token_info.custom_fees[0]
    
    # Verification of base class fields
    assert retrieved_fee.fee_collector_account_id == collector_account.id
    assert retrieved_fee.all_collectors_are_exempt == False
    assert isinstance(retrieved_fee, CustomFixedFee)


@pytest.mark.integration
def test_custom_fee_collector_account_validation_on_network(env):
    """
    Tests that a TokenCreateTransaction fails if the CustomFee uses an 
    Account ID that is known to be non-existent or invalid on the network.
    This indirectly tests the _validate_checksums logic when executing 
    on the network.
    """
    
    # Choose a high, non-existent AccountId. (e.g., 0.0.999999999)
    non_existent_id = AccountId(
        shard=0, 
        realm=0, 
        num=999999999
    ) 
    
    custom_fee = (
        CustomFixedFee(
            amount=10, 
            denominated_token_id=None,
        )
        .set_fee_collector_account_id(non_existent_id)
        .set_all_collectors_are_exempt(False)
    )
    
    # We expect the transaction to fail because the collector account ID is invalid/non-existent
    with pytest.raises(TransactionException) as excinfo:
        create_fungible_token(
            env,
            custom_fees=[custom_fee]
        )
        
    # The transaction should fail because the fee collector account does not exist.
    assert excinfo.value.receipt.status == ResponseCode.INVALID_CUSTOM_FEE_COLLECTOR
    
@pytest.mark.integration
def test_custom_fractional_fee_dispatch_on_network(env):
    """
    Tests that a fractional fee is correctly dispatched from proto 
    back into a CustomFractionalFee instance after querying the network.
    """
    
    # 1. Setup: Create a new account to serve as the fee collector
    collector_account = env.create_account(initial_hbar=1.0)
    
    # 2. Instantiate a CustomFractionalFee
    numerator = 1
    denominator = 10
    min_amount = 5
    max_amount = 100
    
    custom_fee = (
        CustomFractionalFee(
            numerator=numerator,
            denominator=denominator,
            minimum_amount=min_amount,
            maximum_amount=max_amount,
        )
        .set_fee_collector_account_id(collector_account.id)
    )

    # 3. Network Execution
    token_id = create_fungible_token(
        env,
        custom_fees=[custom_fee]
    )

    # 4. Verification: Query the network
    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert len(token_info.custom_fees) == 1
    retrieved_fee = token_info.custom_fees[0]
    
    # Check base class dispatch and subclass type
    assert isinstance(retrieved_fee, CustomFractionalFee)

    # Check Fractional Fee-specific fields
    assert retrieved_fee.numerator == numerator
    assert retrieved_fee.denominator == denominator
    assert retrieved_fee.minimum_amount == min_amount
    assert retrieved_fee.maximum_amount == max_amount
    assert retrieved_fee.fee_collector_account_id == collector_account.id
    
@pytest.mark.integration
def test_custom_royalty_fee_dispatch_on_network(env):
    """
    Tests that a royalty fee with a fallback fee is correctly dispatched 
    from proto back into a CustomRoyaltyFee instance after querying the network.
    """
    
    # 1. Setup: Create accounts and a denominated token
    collector_account = env.create_account(initial_hbar=1.0)
    # Using create_fungible_token here is correct, as the fallback fee is typically a fungible token
    denominated_token_id = create_fungible_token(env) 
    
    # 2. Instantiate the fallback fee (a Fixed Fee on the new token)
    fallback_fee = CustomFixedFee(
        amount=5,
        denominated_token_id=denominated_token_id
    )
    
    # 3. Instantiate a CustomRoyaltyFee
    numerator = 2
    denominator = 100 # 2% royalty
    
    custom_fee = (
        CustomRoyaltyFee(
            numerator=numerator,
            denominator=denominator,
            fallback_fee=fallback_fee,
        )
        .set_fee_collector_account_id(collector_account.id)
    )

    # 4. Network Execution (Royalty fees must be on NFTs, requiring create_nft_token)
    token_id = create_nft_token(
        env,
        custom_fees=[custom_fee]
    )

    # 5. Verification: Query the network
    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)

    assert len(token_info.custom_fees) == 1
    retrieved_fee = token_info.custom_fees[0]
    
    # Check base class dispatch and subclass type
    assert isinstance(retrieved_fee, CustomRoyaltyFee)

    # Check Royalty Fee-specific fields
    assert retrieved_fee.numerator == numerator
    assert retrieved_fee.denominator == denominator
    assert retrieved_fee.fee_collector_account_id == collector_account.id
    
    # Check the nested fallback fee (should be a CustomFixedFee)
    retrieved_fallback = retrieved_fee.fallback_fee
    assert isinstance(retrieved_fallback, CustomFixedFee)
    assert retrieved_fallback.amount == 5
    assert retrieved_fallback.denominated_token_id == denominated_token_id