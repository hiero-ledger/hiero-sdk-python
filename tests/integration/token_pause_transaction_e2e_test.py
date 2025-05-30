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

pause_key = PrivateKey.generate()

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
# Create a unique pause key to enable varied tests
# Signing by the treasury account handled by the executable method in env
@fixture
def pausable_token(env):
    return create_fungible_token(env, opts=[lambda tx: tx.set_pause_key(pause_key)])

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
        tx.freeze_with(env.client) # ← builds the body which fails

@mark.integration
def test_pause_nonexistent_token_id_raises_precheck_error(env):
    """
    If you set a token_id that doesn’t exist, execute should
    raise a PrecheckError(INVALID_TOKEN_ID).
    """
    fake = TokenId(0, 0, 99999999)
    tx = TokenPauseTransaction().set_token_id(fake)

    receipt = tx.execute(env.client)

    assert receipt.status == ResponseCode.INVALID_TOKEN_ID, (
        f"Expected INVALID_TOKEN_ID but got "
        f"{ResponseCode.get_name(receipt.status)}"
    )

@mark.integration
def test_pause_fails_for_unpausable_token(env, unpausable_token):
    """
    If you pause a token without a pause key, execute() should
    return a receipt with status TOKEN_HAS_NO_PAUSE_KEY.
    """
    tx = TokenPauseTransaction().set_token_id(unpausable_token)

    receipt = tx.execute(env.client)  # ← auto-freeze & sign with operator key

    assert receipt.status == ResponseCode.TOKEN_HAS_NO_PAUSE_KEY, (
        f"Expected TOKEN_HAS_NO_PAUSE_KEY but got "
        f"{ResponseCode.get_name(receipt.status)}"
    )

@mark.integration
def test_pause_requires_pause_key_signature(env, pausable_token):
    """
    A pausable token has a pause key.  If you submit a pause tx without
    that pause-key signature, the service rejects it with INVALID_SIGNATURE.
    """
    # Build & freeze, but never sign with the pause key:
    tx = TokenPauseTransaction().set_token_id(pausable_token)
    tx = tx.freeze_with(env.client)
    receipt = tx.execute(env.client) # This autosigns with operator key, which is different to the pause key

    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Expected INVALID_SIGNATURE but got "
        f"{ResponseCode.get_name(receipt.status)}"
    )

@mark.integration
def test_pause_with_invalid_key(env, pausable_token):
    """
    A pausable token created with a pause key must be signed with it—
    signing with some other key causes an INVALID_SIGNATURE.
    """
    bad_key = PrivateKey.generate()

    tx = TokenPauseTransaction().set_token_id(pausable_token)
    tx = tx.freeze_with(env.client)
    tx = tx.sign(bad_key) # ← signed with wrong key
    receipt = tx.execute(env.client)

    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"Expected INVALID_SIGNATURE but got "
        f"{ResponseCode.get_name(receipt.status)}"
    )

@mark.integration
def test_transfer_before_pause(env, account: Account, pausable_token):
    """
    A pausable token is transferred in 10 units to a fresh account that has them associated.
    The receiver's balance increases by 10.
    """
    env.associate_and_transfer(account.id, account.key, pausable_token, 10)

    balance = CryptoGetAccountBalanceQuery(account.id).execute(env.client).token_balances[pausable_token]
    assert balance == 10

@mark.integration
def test_pause_sets_token_status_to_paused(env, pausable_token):
    """
    Take a pausable token (UNPAUSED), submit a pause transaction signed
    with its pause key, then verify it ends up PAUSED.
    """
    # 1) pre-pause sanity check
    info = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)

    assert info.token_status.name == "UNPAUSED"

    # 2) build, freeze, sign & execute the pause tx
    tx = (
        TokenPauseTransaction()
        .set_token_id(pausable_token)
        .freeze_with(env.client)
        .sign(pause_key)
    )
    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS

    # 3) post-pause verify
    info2 = TokenInfoQuery().set_token_id(pausable_token).execute(env.client)

    assert info2.token_status.name == "PAUSED"

@mark.integration
def test_transfers_blocked_when_paused(env, account: Account, pausable_token):
    """
    Pause a token.
    Now that the token is PAUSED, it cannot perform operations.
    For example, an attempt to transfer tokens fails with TOKEN_IS_PAUSED.
    """
    # first associate (this must succeed)
    assoc_tx = (
        TokenAssociateTransaction()
            .set_account_id(account.id)
            .add_token_id(pausable_token)
    )
    assoc_tx = assoc_tx.freeze_with(env.client).sign(account.key)
    assoc_receipt = assoc_tx.execute(env.client)
    assert assoc_receipt.status == ResponseCode.SUCCESS

    # pause the token
    pause_tx = (
        TokenPauseTransaction()
            .set_token_id(pausable_token)
            .freeze_with(env.client)
            .sign(pause_key)
    )
    pause_receipt = pause_tx.execute(env.client)
    assert pause_receipt.status == ResponseCode.SUCCESS

    # attempt to transfer 1 token
    tx = (
        TransferTransaction()
            .add_token_transfer(pausable_token, env.operator_id, -1)
            .add_token_transfer(pausable_token, account.id,       1)
    )
    transfer_receipt = tx.execute(env.client)
    assert transfer_receipt.status == ResponseCode.TOKEN_IS_PAUSED, (
        f"Expected TOKEN_IS_PAUSED but got "
        f"{ResponseCode.get_name(transfer_receipt.status)}"
    )