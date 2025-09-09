import pytest

from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_burn_transaction import TokenBurnTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, create_nft_token


@pytest.mark.integration
def test_integration_token_burn_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        info = TokenInfoQuery(token_id).execute(env.client)
        assert info.total_supply == 1000, f"Total supply is not 1000, but {info.total_supply}"
        
        receipt = (
            TokenBurnTransaction()
            .set_token_id(token_id)
            .set_amount(10)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token burn failed with status: {ResponseCode(receipt.status).name}"
        
        info = TokenInfoQuery(token_id).execute(env.client)
        assert info.total_supply == 990, f"Total supply is not 990, but {info.total_supply}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_burn_transaction_no_amount():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_fungible_token(env)
        assert token_id is not None
        
        # Execute token burn with no amount specified
        receipt = (
            TokenBurnTransaction()
            .set_token_id(token_id)
            .execute(env.client)
        )
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token burn failed with status: {ResponseCode(receipt.status).name}"
        
        info = TokenInfoQuery(token_id).execute(env.client)
        assert info.total_supply == 1000, f"Total supply should remain 1000, but is {info.total_supply}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_burn_transaction_nft():
    env = IntegrationTestEnv()
    
    try:
        # Create NFT token
        token_id = create_nft_token(env)
        assert token_id is not None
        
        # Mint an NFT
        receipt = (
            TokenMintTransaction()
            .set_token_id(token_id)
            .set_metadata([b"Metadata"])
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token mint failed with status: {ResponseCode(receipt.status).name}"
        
        # Try to burn the NFT
        receipt = (
            TokenBurnTransaction()
            .set_token_id(token_id)
            .set_serials([1])
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.SUCCESS, f"Token burn failed with status: {ResponseCode(receipt.status).name}"
        
        info = TokenInfoQuery(token_id).execute(env.client)
        assert info.total_supply == 0, f"Total supply is not 0, but {info.totalSupply}"
    finally:
        env.close()

@pytest.mark.integration
def test_integration_token_burn_transaction_fails_invalid_metadata():
    env = IntegrationTestEnv()
    
    try:
        # Create NFT token
        token_id = create_nft_token(env)
        assert token_id is not None
        
        # Attempt to burn an NFT using set_amount() instead of set_serials()
        # This should fail since NFTs require serial numbers for burning
        receipt = (
            TokenBurnTransaction()
            .set_token_id(token_id)
            .set_amount(1)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.INVALID_TOKEN_BURN_METADATA, f"Token burn should have failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_burn_transaction_fails_no_supply_key():
    env = IntegrationTestEnv()
    
    try:
        # Create fungible token without supply key
        token_id = create_fungible_token(env, [lambda tx: tx.set_supply_key(None)])
        
        # Try to burn tokens - should fail without supply key
        receipt = (
            TokenBurnTransaction()
            .set_token_id(token_id)
            .set_amount(10)
            .execute(env.client)
        )
        assert receipt.status == ResponseCode.TOKEN_HAS_NO_SUPPLY_KEY, f"Token burn should have failed with TOKEN_HAS_NO_SUPPLY_KEY but got: {ResponseCode(receipt.status).name}"
    finally:
        env.close()