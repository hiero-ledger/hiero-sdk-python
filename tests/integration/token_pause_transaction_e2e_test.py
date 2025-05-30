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
# from hiero_sdk_python.query.token_info_query import TokenInfoQuery

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
    return create_fungible_token(env, opts=[lambda tx: tx.set_pause_key(env.operator_key)])

# Fungible token in env has no pause key
@fixture
def unpausable_token(env):
    return create_fungible_token(env)

@mark.integration
def test_pause_missing_token_id_raises_value_error(env):
    """
    If you never set token_id, freeze_with should raise a ValueError.
    """
    tx = TokenPauseTransaction()

    with pytest.raises(ValueError, match="token_id must be set"):
        tx.freeze_with(env.client)

@mark.integration
def test_pause_nonexistent_token_id_raises_precheck_error(env):
    """
    If you set a token_id that doesn’t exist, execute should
    raise a PrecheckError(INVALID_TOKEN_ID).
    """
    fake = TokenId(0, 0, 99999999)
    tx = TokenPauseTransaction().set_token_id(fake)

    with pytest.raises(PrecheckError, match=ResponseCode.get_name(ResponseCode.INVALID_TOKEN_ID)):
        # .execute() will auto‐freeze and auto‐sign with the operator key
        tx.execute(env.client)

@mark.integration
def test_pause_fails_for_unpausable_token(env, unpausable_token):
    """
    Verify that attempting to pause a token that was created without any pause key
    fails with a TOKEN_HAS_NO_PAUSE_KEY precheck error.
    """
    tx = TokenPauseTransaction().set_token_id(unpausable_token)

    with pytest.raises(PrecheckError, match=ResponseCode.get_name(ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),):
        # .execute() will auto‐freeze and auto‐sign with the operator key
        tx.execute(env.client)

@mark.integration
def test_pause_requires_pause_key_signature(env, pausable_token):
    """
    A pausable token has a pause key.  If you submit a pause tx without
    that pause-key signature, you get TOKEN_HAS_NO_PAUSE_KEY.
    """
    # Build & freeze, but never sign with the pause key:
    tx = TokenPauseTransaction().set_token_id(pausable_token)
    tx = tx.freeze_with(env.client)

    with pytest.raises(PrecheckError, match=ResponseCode.get_name(ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),):
        tx.execute(env.client)

@mark.integration
def test_pause_requires_pause_key_signature(env, pausable_token):
    """
    A pausable token has a pause key. If submitting a pause tx without
    that pause-key signature, the network rejects with TOKEN_HAS_NO_PAUSE_KEY
    """
    # Build & freeze, but never sign with the pause key:
    tx = TokenPauseTransaction().set_token_id(pausable_token)
    tx = tx.freeze_with(env.client)

    # execute() will auto-sign with operator, but operator≠pause key → still fails:
    with pytest.raises(PrecheckError,match=ResponseCode.get_name(ResponseCode.TOKEN_HAS_NO_PAUSE_KEY),):
        tx.execute(env.client)

@mark.integration
def test_pause_with_invalid_key_fails_precheck(env, pausable_token):
    """
    A pausable token created with a pause key must be signed with it—
    signing with some other key causes an INVALID_PAUSE_KEY precheck failure.
    """
    bad_key = PrivateKey.generate()
    with pytest.raises(PrecheckError,match=ResponseCode.get_name(ResponseCode.INVALID_PAUSE_KEY)):
        # freeze, sign with wrong key, then execute
        tx = TokenPauseTransaction().set_token_id(pausable_token)
        tx = tx.freeze_with(env.client)
        tx = tx.sign(bad_key)
        tx.execute(env.client)

@mark.integration
def test_pause_already_paused_token_fails(env, pausable_token):
    """
    Attempting to pause a token that is already paused should fail 
    in the handle phase with TOKEN_IS_PAUSED.
    """
    env.pause_token(pausable_token)

    # 2) Second pause (signed with the same pause key by default)
    with pytest.raises(ReceiptStatusError,match=ResponseCode.get_name(ResponseCode.TOKEN_IS_PAUSED)):
        env.pause_token(pausable_token)

@mark.integration
class TestTokenPause:
    """Integration tests for pausing tokens."""

    def test_transfer_before_pause(self, env, account: Account, pausable_token):
        """
        A pausable token is transferred in 10 units to a fresh account that has them associated.
        The receiver's balance increases by 10.
        """
        env.associate_and_transfer(account.id, account.key, pausable_token, 10)

        balance = CryptoGetAccountBalanceQuery(account.id).execute(env.client).token_balances[pausable_token]
        assert balance == 10

    def test_pause_sets_token_status_to_paused(self, env, pausable_token):
        """
        Take a pausable token, that is not paused, it should be UNPAUSED.
        A token pause transaction to an unpaused token now makes it PAUSED.
        """
        # pre-pause sanity check
        info = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
        assert info.token_status.name == "UNPAUSED"

        # pause via fixture
        env.pause_token(pausable_token, key=env.operator_key)

        # verify
        info2 = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
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
