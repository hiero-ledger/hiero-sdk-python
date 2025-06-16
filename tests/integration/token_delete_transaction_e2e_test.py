import pytest

from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode

@pytest.mark.integration
def test_integration_token_delete_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        assert token_id is not None, "TokenID not found in receipt. Token may not have been created."
        
        transaction = TokenDeleteTransaction(token_id=token_id)
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token deletion failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 