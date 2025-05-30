import pytest
from pytest import mark, fixture

from hiero_sdk_python.crypto.private_key      import PrivateKey
from hiero_sdk_python.exceptions              import PrecheckError, ReceiptStatusError
from hiero_sdk_python.response_code           import ResponseCode

from hiero_sdk_python.tokens import (
    TokenPauseTransaction,
    TokenId
)

from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token, Account
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery

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

# Uses lambda opts to add a pause key → pausable
# Signing by the treasury account handled by the executable method in env
@fixture
def pausable_token(env):
    pause_key = env.operator_key
    return create_fungible_token(env, opts=[
        lambda tx: tx.set_pause_key(pause_key)
    ])

# Fungible token in env has no pause key
@fixture
def unpausable_token(env):
    return create_fungible_token(env)

@mark.integration
@mark.parametrize(
    "token_id, exception, msg",
    [
        (None,                    ValueError,    "token_id must be set"),
        (TokenId(0, 0, 99999999), PrecheckError, ResponseCode.get_name(ResponseCode.INVALID_TOKEN_ID)),
    ],
)
def test_pause_error_invalid_token_id(env, token_id, exception, msg):
    """
    Invalid-pause scenarios:
      1) missing token_id
      2) non-existent token_id
    """
    tx = TokenPauseTransaction()
    if token_id is not None:
        tx.set_token_id(token_id)

    if exception is ValueError:
        with pytest.raises(ValueError, match=msg):
            tx.freeze_with(env.client)
    else:
        with pytest.raises(PrecheckError, match=msg):
            # .execute() will auto‐freeze and auto‐sign with the operator key
            tx.execute(env.client)

@mark.integration
def test_pause_error_without_pause_key(env, unpausable_token):
    """
    Invalid-pause scenario: missing pause key for a valid token.
    """
    tx = TokenPauseTransaction().set_token_id(unpausable_token)

    with pytest.raises(
        PrecheckError,
        match=ResponseCode.get_name(ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),
    ):
        # .execute() will auto‐freeze and auto‐sign with the operator key
        tx.execute(env.client)

@mark.integration
@mark.parametrize("second_key, expected_code", [
    (None,                          ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),
    (lambda env: PrivateKey.generate(), ResponseCode.INVALID_PAUSE_KEY),
    (lambda env: env.operator_key,  ResponseCode.TOKEN_IS_PAUSED),
])
def test_double_pause_errors(env, pausable_token, second_key, expected_code):
    # 1st pause must succeed (signed with real pause key) via fixture
    pause_key = env.operator_key
    env.pause_token(pausable_token, key=pause_key)

    # prepare the second‐pause key, which could be: None, a different key or the previously set pause key:
    key = second_key(env) if callable(second_key) else second_key

    # 2nd pause attempt in all these scenarios should fail in exactly the expected way
    with pytest.raises(ReceiptStatusError,match=ResponseCode.get_name(expected_code)):
        env.pause_token(pausable_token, key=key)

@mark.integration
class TestTokenPause:
    """Integration tests for pausing tokens."""

    def test_transfer_before_pause(self, env, account: Account, pausable_token):
        """
        A pausable token is transferred in 10 units to a fresh account that has them associated.
        The receiver's balance increases by 10.
        """
        env.associate_and_transfer(account.id, account.key, pausable_token, 10)

        balance = (CryptoGetAccountBalanceQuery(account.id).execute(env.client).token_balances[pausable_token])
        assert balance == 10

    def test_pause_sets_token_status_to_paused(self, env, pausable_token):
        """
        Take a pausable token, that is not paused, it should be UNPAUSED.
        A token pause transaction to an unpaused token now makes it PAUSED.
        """
        # pre-pause sanity check
        info = (TokenInfoQuery().set_token_id(pausable_token).execute(env.client))
        assert info.token_status.name == "UNPAUSED"

        # pause via fixture
        env.pause_token(pausable_token, key=env.operator_key)

        # verify
        info2 = (TokenInfoQuery().set_token_id(pausable_token).execute(env.client))
        assert info2.token_status.name == "PAUSED"

    def test_transfers_blocked_when_paused(self, env, account: Account, pausable_token):
        """
        Pause a token.
        Now that the token is PAUSED, it cannot perform operations.
        For example, an attempt to transfer tokens fails with TOKEN_IS_PAUSED.
        """
        # first associate (this must succeed)
        env.freeze_sign_execute(
            TokenAssociateTransaction()
                .set_account_id(account.id)
                .add_token_id(pausable_token),
            account.key,
        )

        # pause the token
        pause_key = env.operator_key
        env.pause_token(pausable_token, key=pause_key)

        # attempt to transfer 1 token
        tx = (
            TransferTransaction()
            .add_token_transfer(pausable_token, env.operator_id, -1)
            .add_token_transfer(pausable_token, account.id,      1)
        )

        with pytest.raises(ReceiptStatusError, match=ResponseCode.get_name(ResponseCode.TOKEN_IS_PAUSED)):
            tx.execute(env.client)
