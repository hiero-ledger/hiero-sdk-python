import pytest

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token

@pytest.mark.integration
def test_integration_token_info_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env, [
            lambda tx: tx.set_decimals(3),
            lambda tx: tx.set_wipe_key(None) # Set wipe key to None to verify TokenInfoQuery returns correct key state
            ])
        
        info = TokenInfoQuery(token_id).execute(env.client)
        
        assert str(info.token_id) == str(token_id), "Token ID mismatch"
        assert info.name == "PTokenTest34", "Name mismatch"
        assert info.symbol == "PTT34", "Symbol mismatch" 
        assert info.decimals == 3, "Decimals mismatch"
        assert str(info.treasury) == str(env.operator_id), "Treasury mismatch"
        assert info.token_type == TokenType.FUNGIBLE_COMMON, "Token type mismatch"
        assert info.supply_type == SupplyType.FINITE, "Supply type mismatch"
        assert info.max_supply == 10000, "Max supply mismatch"
        
        assert info.admin_key is not None, "Admin key should not be None"
        assert info.freeze_key is not None, "Freeze key should not be None"
        assert info.wipe_key is None, "Wipe key should be None"
        assert info.supply_key is not None, "Supply key should not be None"
        assert info.kyc_key is None, "KYC key should be None"
        
        assert str(info.admin_key) == str(env.operator_key.public_key()), "Admin key mismatch"
        assert str(info.freeze_key) == str(env.operator_key.public_key()), "Freeze key mismatch"
        assert str(info.supply_key) == str(env.operator_key.public_key()), "Supply key mismatch"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_info_query_fails_with_insufficient_tx_fee():
    """Test that token info query fails with insufficient payment."""
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        
        query = TokenInfoQuery(token_id)
        query.set_query_payment(Hbar.from_tinybars(1)) # Set very low query payment
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"):
            query.execute(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_info_query_fails_with_invalid_token_id():
    env = IntegrationTestEnv()
    
    try:
        token_id = TokenId(0,0,123456789)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_TOKEN_ID"):
            TokenInfoQuery(token_id).execute(env.client)
    finally:
        env.close()