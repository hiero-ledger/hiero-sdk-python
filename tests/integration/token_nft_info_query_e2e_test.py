import pytest

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_nft_info import TokenNftInfo
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_nft_token
from hiero_sdk_python.tokens.nft_id import NftId

@pytest.mark.integration
def test_integration_token_nft_info_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_nft_token(env)
        
        metadata = b"Token A"
        
        mint = TokenMintTransaction(
            token_id=token_id,
            metadata=metadata
        )
        
        receipt = mint.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Token minting failed with status: {ResponseCode(receipt.status).name}"
        nft_id = NftId(token_id, receipt.serial_numbers[0])
        
        info = TokenNftInfoQuery(nft_id).execute(env.client)
        
        assert str(info.nft_id) == str(nft_id), f"NFT ID mismatch"
        assert info.nft_id == nft_id, f"NFT ID mismatch"
        assert info.metadata == metadata, f"Metadata mismatch"
    finally:
        env.close()
        
@pytest.mark.integration
def test_integration_token_nft_info_query_fail_nonexistent_nft():
    env = IntegrationTestEnv()
    
    try:
        token_id = create_nft_token(env)
        
        nft_id = NftId(token_id, 1)
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_NFT_ID"):
            TokenNftInfoQuery(nft_id).execute(env.client)
    finally:
        env.close()