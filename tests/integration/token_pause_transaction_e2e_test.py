import pytest
from pytest import mark, fixture

from hiero_sdk_python.crypto.private_key       import PrivateKey
from hiero_sdk_python.exceptions              import PrecheckError, ReceiptStatusError
from hiero_sdk_python.response_code           import ResponseCode

from hiero_sdk_python.tokens import (
    TokenCreateTransaction,
    TokenPauseTransaction,
    TokenId,
    TokenType,
    SupplyType,
)

from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, Account

@fixture
def env():
    """Integration test environment with client/operator set up."""
    e = IntegrationTestEnv()
    yield e
    e.close()

@fixture
def account(env):
    """A fresh account funded with 1 HBAR balance."""
    return env.create_account()

@fixture
def pausable_token(env):
    """Create a token that has a pause key."""
    pause_key = env.operator_key

    return create_fungible_token(env, [
        lambda tx: tx
            .set_pause_key(pause_key)
            .freeze_with(env.client)
            .sign(pause_key),
    ])

@fixture
def unpausable_token(env):
    """Create a token with no pause key."""
    tx = (
        TokenCreateTransaction()
        .set_token_name("NoPause")
        .set_token_symbol("NOP")
        .set_decimals(0)
        .set_initial_supply(1)
        .set_treasury_account_id(env.operator_id)
        .set_token_type(TokenType.FUNGIBLE_COMMON)
        .set_supply_type(SupplyType.FINITE)
        .set_max_supply(1)
    )

    receipt = env.freeze_sign_execute(tx, env.operator_key)
    return receipt.tokenId

@mark.integration
@mark.parametrize(
    "token_id, exception, msg",
    [
        (None,                              ValueError,    "token_id must be set"),
        (TokenId(0, 0, 99999999),           PrecheckError, str(ResponseCode.INVALID_TOKEN_ID)),
        # (lazy_fixture("unpausable_token"),  PrecheckError, ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),
    ],
)
def test_pause_error_cases(env, token_id, exception, msg):
    """
    Invalid-pause scenarios:
      1) missing token_id
      2) non-existent token_id
      3) token exists but has no pause key
    """
    tx = TokenPauseTransaction()
    if token_id is not None:
        tx.set_token_id(token_id)

    if exception is ValueError:
        with pytest.raises(ValueError, match=msg):
            tx.freeze_with(env.client)
    else:
        tx.freeze_with(env.client)
        with pytest.raises(exception, match=msg):
            tx.execute(env.client)

@mark.integration
class TestTokenPause:
    """Integration tests for pausing tokens."""

    def test_transfer_before_pause(self, env, account: Account, pausable_token):
        """
        A pausable token is transferred in 10 units to a fresh account that has them associated.
        The receiver's balance increases by 10.
        """
        env.associate_and_transfer(account.id, account.key, pausable_token, 10)

        balance = env.get_balance(account.id).token_balances[pausable_token]
        assert balance == 10

    def test_pause_sets_token_status_to_paused(self, env, pausable_token):
        """
        Take a pausable token, that is not paused, it should be UNPAUSED.
        A token pause transaction to an unpaused token now makes it PAUSED.
        """
        # pre-pause sanity check
        info = env.get_token_info(pausable_token)
        assert info.token_status.name == "UNPAUSED"

        # pause via fixture
        env.pause_token(pausable_token)

        # verify
        info2 = env.get_token_info(pausable_token)
        assert info2.token_status.name == "PAUSED"

    def test_transfers_blocked_when_paused(self, env, account: Account, pausable_token):
        """
        Pause a token.
        Now that the token is PAUSED, it cannot perform operations.
        For example, an attempt to transfer tokens fails with TOKEN_IS_PAUSED.
        """
        env.pause_token(pausable_token)
        with pytest.raises(ReceiptStatusError, match=ResponseCode.TOKEN_IS_PAUSED.name):
            env.associate_and_transfer(account.id, account.key, pausable_token, 1)

    @mark.parametrize("bad_key, exc_cls, msg", [
        (None,                  ReceiptStatusError, ResponseCode.get_name(ResponseCode.TOKEN_HAS_NO_PAUSE_KEY)),
        (PrivateKey.generate(), ReceiptStatusError, ResponseCode.get_name(ResponseCode.INVALID_PAUSE_KEY)),
    ])
    def test_double_pause_errors(self, env, pausable_token, bad_key, exc_cls, msg):
        env.pause_token(pausable_token)
        with pytest.raises(exc_cls, match=msg):
            env.pause_token(pausable_token, key=bad_key)
