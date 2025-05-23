import pytest

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