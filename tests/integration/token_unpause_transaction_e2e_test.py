from pytest import fixture
import pytest
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from tests.integration.utils_for_test import env, create_fungible_token

pause_key = PrivateKey.generate()

@fixture
def pausable_token(env):
    """"Fixture to create a token that supports pausing."""
    return create_fungible_token(
        env, 
        opts=[lambda tx: tx.set_pause_key(pause_key)]
    )

def pause_token(env, token_id: TokenId):
    """Helper function to pause the token with the given token_id."""
    token_pasue_tx = (
        TokenPauseTransaction()
        .set_token_id(token_id)
        .freeze_with(env.client)
        .sign(pause_key)
    )

    return token_pasue_tx.execute(env.client)

def get_pause_status(env, token_id: TokenId):
    """Helper to query and return the pause status of a token."""
    token_info = TokenInfoQuery().set_token_id(token_id).execute(env.client)
    return token_info.pause_status.name

def test_unpause_token(env, pausable_token):
    """Test successful unpause of a paused token."""
    pause_receipt = pause_token(env, pausable_token)

    assert pause_receipt.status == ResponseCode.SUCCESS 
    assert get_pause_status(env, pausable_token) == "PAUSED"

    unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(pausable_token)
        .freeze_with(env.client)
        .sign(pause_key)
    )

    unpause_receipt = unpause_tx.execute(env.client)
    assert unpause_receipt.status == ResponseCode.SUCCESS
    assert get_pause_status(env, pausable_token) == "UNPAUSED"


def test_unpause_token_without_pause_key_signature(env, pausable_token):
    """Test unpause transaction without pause key signature."""
    pause_receipt = pause_token(env, pausable_token)

    assert pause_receipt.status == ResponseCode.SUCCESS
    assert get_pause_status(env, pausable_token) == "PAUSED"

    unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(pausable_token)
        .freeze_with(env.client)
    )

    unpause_receipt = unpause_tx.execute(env.client)
    assert unpause_receipt.status == ResponseCode.INVALID_SIGNATURE

def test_unpause_token_with_invalid_pasue_key(env, pausable_token):
    """Test unpause transaction with invalid pause key."""
    pause_receipt = pause_token(env, pausable_token)

    assert pause_receipt.status == ResponseCode.SUCCESS
    assert get_pause_status(env, pausable_token) == "PAUSED"

    unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(pausable_token)
        .freeze_with(env.client)
        .sign(PrivateKey.generate())
    )

    unpause_receipt = unpause_tx.execute(env.client)
    assert unpause_receipt.status == ResponseCode.INVALID_SIGNATURE

def test_unpause_token_when_token_id_not_set(env):
    """Test unpause transaction when token_id is not provided."""

    unpause_tx = TokenUnpauseTransaction()
    with pytest.raises(ValueError, match="Missing token ID"):
        unpause_tx.freeze_with(env.client)

def test_unpause_token_with_invalid_token_id(env):
    """Test unpause transaction using an invalid token ID."""
    token_id = TokenId(0, 0, 999)

    unpause_tx = (
        TokenUnpauseTransaction()
        .set_token_id(token_id)
        .freeze_with(env.client)
        .sign(pause_key)
    )

    unpause_receipt = unpause_tx.execute(env.client)
    assert unpause_receipt.status == ResponseCode.INVALID_TOKEN_ID
