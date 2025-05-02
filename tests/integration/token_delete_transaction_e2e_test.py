import pytest

from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token


@pytest.mark.integration
def test_integration_token_delete_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        if token_id is None:
            raise Exception("TokenID not found in receipt. Token may not have been created.")
    except Exception as e:
        pytest.fail(f"Token deletion test failed: {str(e)}")
    finally:
        env.close(token_id) 