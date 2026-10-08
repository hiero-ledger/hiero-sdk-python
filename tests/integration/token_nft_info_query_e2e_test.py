from __future__ import annotations

import pytest

from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query.token_nft_info_query import TokenNftInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from tests.integration.utils import IntegrationTestEnv, create_nft_token


@pytest.mark.integration
def test_integration_token_nft_info_query_can_execute():
    env = IntegrationTestEnv()

    try:
        token_id = create_nft_token(env)

        metadata = b"Token A"

        mint = TokenMintTransaction(token_id=token_id, metadata=metadata)

        receipt = mint.execute(env.client)

        assert receipt.status == ResponseCode.SUCCESS, (
            f"Token minting failed with status: {ResponseCode(receipt.status).name}"
        )
        nft_id = NftId(token_id, receipt.serial_numbers[0])

        info = TokenNftInfoQuery(nft_id).execute(env.client)

        assert str(info.nft_id) == str(nft_id), "NFT ID mismatch"
        assert info.nft_id == nft_id, "NFT ID mismatch"
        assert info.metadata == metadata, "Metadata mismatch"
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


# Requires payment so get_cost() return Hbar > 0
@pytest.mark.integration
def test_integration_token_nft_info_query_get_cost(env):
    """Test the get_cost method for the token_nft_info query."""
    token_id = create_nft_token(env)
    receipt = TokenMintTransaction(token_id=token_id, metadata=b"hello hiero").execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token minting failed with status: {ResponseCode(receipt.status).name}"
    )

    nft_id = NftId(token_id, receipt.serial_numbers[0])

    # With operator
    cost1 = TokenNftInfoQuery().set_nft_id(nft_id).get_cost(env.client)

    assert cost1 is not None
    assert cost1.to_tinybars() > 0, f"Expected cost to be greater than 0 but get {cost1.to_tinybars()}"

    # Without operator
    client = Client(env.client.network)
    cost2 = TokenNftInfoQuery().set_nft_id(nft_id).get_cost(client)

    assert cost2 is not None
    assert cost2.to_tinybars() > 0, f"Expected cost to be greater than 0 but get {cost2.to_tinybars()}"
