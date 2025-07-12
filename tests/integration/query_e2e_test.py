import time
import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token

@pytest.mark.integration
def test_integration_free_query_no_cost():
    """Test that free queries don't cost anything and don't deduct from account balance."""
    env = IntegrationTestEnv()
    
    try:
        new_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_private_key.public_key()
        
        initial_balance = Hbar(1)
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(initial_balance)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS
        account_id = receipt.account_id
        assert account_id is not None
        
        env.client.set_operator(account_id, new_private_key)
        
        # Test free query (account balance query)
        query = CryptoGetAccountBalanceQuery(account_id)
        
        # Cost should be 0 for free queries
        cost = query.get_cost(env.client)
        assert cost.to_tinybars() == 0
        
        # Execute query and verify balance wasn't deducted
        balance_before = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(env.client)
        )
        
        balance_result = query.execute(env.client)
        assert balance_result.hbars.to_tinybars() == initial_balance.to_tinybars()
        
        balance_after = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(env.client)
        )
        
        # Balance should remain unchanged after free query
        assert balance_before.hbars.to_tinybars() == balance_after.hbars.to_tinybars()
    finally:
        env.close()

@pytest.mark.integration
def test_integration_free_query_with_manual_payment():
    """Test that manually setting payment on free queries still results in no cost."""
    env = IntegrationTestEnv()
    
    try:
        new_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_private_key.public_key()
        
        initial_balance = Hbar(1)
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(initial_balance)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS
        account_id = receipt.account_id
        assert account_id is not None
                
        env.client.set_operator(account_id, new_private_key)
        
        # Test free query with manual payment set
        query = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .set_query_payment(Hbar(2))  # Set a high payment
        )
        
        # Cost should still be 0 for free queries even with manual payment
        cost = query.get_cost(env.client)
        assert cost.to_tinybars() == 0
        
        # Execute and verify no balance deduction
        balance_before = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(env.client)
        )
        
        balance_result = query.execute(env.client)
        assert balance_result.hbars.to_tinybars() == initial_balance.to_tinybars()
        
        balance_after = (
            CryptoGetAccountBalanceQuery()
            .set_account_id(account_id)
            .execute(env.client)
        )
        
        # Balance should remain unchanged
        assert balance_before.hbars.to_tinybars() == balance_after.hbars.to_tinybars()
    finally:
        env.close()

@pytest.mark.integration
def test_integration_paid_query_network_cost():
    """Test that paid queries get actual network cost and payment amount is set correctly."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        new_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_private_key.public_key()
        
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS
        account_id = receipt.account_id
        assert account_id is not None
        
        env.client.set_operator(account_id, new_private_key)
        
        # Test paid query (token info query)
        query = TokenInfoQuery(token_id)
        
        # Get the network cost
        network_cost = query.get_cost(env.client)
        assert network_cost.to_tinybars() > 0
        
        # Execute the query
        query.execute(env.client)
        
        # Payment amount should be set to the network cost
        assert query.payment_amount.to_tinybars() == network_cost.to_tinybars()
    finally:
        env.close()

@pytest.mark.integration
def test_integration_paid_query_manual_payment():
    """Test that manually setting payment on paid queries uses the set amount."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        new_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_private_key.public_key()
        
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS
        account_id = receipt.account_id
        assert account_id is not None
        
        env.client.set_operator(account_id, new_private_key)
            
        # Set a custom payment amount
        custom_payment = Hbar.from_tinybars(5000000)  # 0.05 Hbar
        query = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .set_query_payment(custom_payment)
        )
        
        # get_cost should return the manually set amount
        cost = query.get_cost(env.client)
        assert cost.to_tinybars() == custom_payment.to_tinybars()
        
        # Execute the query
        query.execute(env.client)
        assert query.payment_amount is not None
        
        # Payment amount should be the custom amount
        assert query.payment_amount.to_tinybars() == custom_payment.to_tinybars()
    finally:
        env.close()

@pytest.mark.integration
def test_integration_paid_query_payment_too_high_fails():
    """Test that setting payment too high on paid queries fails."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        new_private_key = PrivateKey.generate_ed25519()
        new_account_public_key = new_private_key.public_key()
        
        receipt = (
            AccountCreateTransaction()
            .set_key(new_account_public_key)
            .set_initial_balance(Hbar(1))
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS
        account_id = receipt.account_id
        assert account_id is not None
        
        env.client.set_operator(account_id, new_private_key)
        
        # Set an unreasonably high payment amount
        payment = Hbar(2)
        query = (
            TokenInfoQuery()
            .set_token_id(token_id)
            .set_query_payment(payment)
        )
        # Execute the query - should fail due to insufficient balance
        with pytest.raises(PrecheckError, match="failed precheck with status: INSUFFICIENT_PAYER_BALANCE"):
            query.execute(env.client)
    finally:
        env.close()