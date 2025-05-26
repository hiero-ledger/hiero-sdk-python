from collections import namedtuple

import pytest
from pytest import mark, fixture, lazy_fixture

from hiero_sdk_python.crypto.private_key       import PrivateKey
from hiero_sdk_python.exceptions              import PrecheckError, ReceiptStatusException
from hiero_sdk_python.hbar                    import Hbar
from hiero_sdk_python.response_code           import ResponseCode
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction

from hiero_sdk_python.tokens import (
    TokenCreateTransaction,
    TokenAssociateTransaction,
    TokenPauseTransaction,
    TokenId,
    TokenType,
    SupplyType,
    TokenInfoQuery,
)

from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token

Account = namedtuple("Account", ["id", "key"])

def freeze_sign_execute(tx, client, key):
    receipt = tx.freeze_with(client).sign(key).execute(client)
    assert receipt.status == ResponseCode.SUCCESS
    return receipt

def associate_and_transfer(env, receiver, receiver_key, token_id, amount):
    """Associate the token id for the receiver account. Then transfer an amount of the token from the operator (sender) to the receiver."""
    # build and execute the associate transaction
    freeze_sign_execute(
        TokenAssociateTransaction()
        .set_account_id(receiver)
        .add_token_id(token_id),
        env.client, 
        receiver_key,
    )

    # build and execute the transfer transaction
    freeze_sign_execute(
        TransferTransaction()
            .add_token_transfer(token_id, env.operator_id, -amount)
            .add_token_transfer(token_id, receiver, amount),
        env.client,
        env.operator_key,
    )

@pytest.fixture
def pause_token(env, freeze_sign_execute):
    """
    Helper to pause a token with the given key (defaults to pause_key=env.operator_key).
    """
    def _pause(token_id, key=env.operator_key):
        return freeze_sign_execute(
            TokenPauseTransaction().set_token_id(token_id),
            env.client,
            key,
        )
    return _pause

@fixture
def env():
    """Integration test environment with client/operator set up."""
    e = IntegrationTestEnv()
    yield e
    e.close()

@fixture
def account(env):
    """Create a fresh account with 1 ℏ and return (account_id, private_key)."""

    key = PrivateKey.generate()
    receipt = freeze_sign_execute(
        AccountCreateTransaction()
            .set_key(key.public_key())
            .set_initial_balance(Hbar(1)),
        env.client,
        env.operator_key,
    )
    return Account(id=receipt.accountId, key=key)

@fixture
def pausable_token(env):
    """Create a token that has a pause key (signed by operator)."""
    pause_key = env.operator_key
    return create_fungible_token(env, [
        lambda t: t.set_pause_key(pause_key).freeze_with(env.client),
        lambda t: t.sign(pause_key),
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
    receipt = freeze_sign_execute(tx, env.client, env.operator_key)
    return receipt.tokenId

@mark.integration
@mark.parametrize(
    "token_id, exception, msg",
    [
        (None,                              ValueError,    "token_id must be set"),
        (TokenId(0, 0, 99999999),           PrecheckError, ResponseCode.INVALID_TOKEN_ID.name),
        (lazy_fixture("unpausable_token"),  PrecheckError, ResponseCode.TOKEN_HAS_NO_PAUSE_KEY.name),
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

    tx.freeze_with(env.client)
    with pytest.raises(exception, match=msg):
        tx.execute(env.client)

@mark.integration
@pytest.mark.usefixtures("freeze_sign_execute")
class TestTokenPause:
    """Integration tests for pausing tokens."""

    def test_transfer_before_pause(self, env, account, pausable_token):
        """
        A pausable token is transferred in 10 units to a fresh account that has them associated.
        The receiver's balance increases by 10.
        """
        recv_id, recv_key = account.id, account.key

        associate_and_transfer(env, recv_id, recv_key, pausable_token, 10)
        balance = CryptoGetAccountBalanceQuery(recv_id).execute(env.client)
        assert balance.token_balances[pausable_token] == 10

    def test_pause_sets_token_status_to_paused(self, env, pausable_token, pause_token):
        """
        Take a pausable token, that is not paused, it should be UNPAUSED.
        A token pause transaction to an unpaused token now makes it PAUSED.
        """
        # pre-pause sanity check
        before = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
        assert before.token_status.name == "UNPAUSED"

        # pause via fixture
        pause_token(pausable_token)

        # verify
        after = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)
        assert after.token_status.name == "PAUSED"

    def test_transfers_are_blocked_when_paused(self, env, account, pausable_token, pause_token):
        """
        Pause a token.
        Now that the token is PAUSED, it cannot perform operations.
        For example, an attempt to transfer tokens fails with TOKEN_IS_PAUSED.
        """
        acc_id, acc_key = account.id, account.key

        # pause via fixture
        pause_token(pausable_token)

        with pytest.raises(ReceiptStatusException, match=ResponseCode.TOKEN_IS_PAUSED.name):
            associate_and_transfer(env, acc_id, acc_key, pausable_token, 1)

    def test_double_pause_raises_already_paused(self, env, pausable_token, pause_token):
        """
        Pause the token.
        Attempt to pause again, the SDK rejects with TOKEN_ALREADY_PAUSED.
        """
        # first pause
        pause_token(pausable_token)

        # second pause
        with pytest.raises(PrecheckError, match=ResponseCode.TOKEN_ALREADY_PAUSED.name):
            pause_token(pausable_token)

    def test_wrong_key_fails_to_pause(self, env, pausable_token, pause_token):
        """
        Given a valid pause transaction signed by the wrong key
        The SDK rejects with SIG_MISMATCH.
        """
        bad_key = PrivateKey.generate()
        with pytest.raises(PrecheckError, match=ResponseCode.SIG_MISMATCH.name):
            pause_token(pausable_token, key=bad_key)
