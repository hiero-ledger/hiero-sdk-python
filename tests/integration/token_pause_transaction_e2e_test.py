import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction
from tests.integration.utils_for_test import IntegrationTestEnv, create_fungible_token
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_type import TokenType
from hiero_sdk_python.tokens.supply_type import SupplyType
from hiero_sdk_python.tokens.token_info_query import TokenInfoQuery

@pytest.mark.integration
def test_pause_without_setting_token_id_raises_client_error():
    """
    Building a TokenPauseTransaction without ever
    calling set_token_id(), should error.
    """
    env = IntegrationTestEnv()
    try:
        tx = TokenPauseTransaction()  # no set_token_id()
        with pytest.raises(ValueError, match="token_id must be set"):
            tx.freeze_with(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_pause_nonexistent_token_raises_precheck():
    """
    Trying to pause a token that doesn’t exist should fail fast
    with INVALID_TOKEN_ID.
    """
    env = IntegrationTestEnv()
    try:
        bogus = TokenPauseTransaction().set_token_id(TokenId(0, 0, 99999999))
        bogus.freeze_with(env.client)

        with pytest.raises(
            PrecheckError,
            match="failed precheck with status: INVALID_TOKEN_ID"
        ) as excinfo:
            bogus.execute(env.client)

        assert "INVALID_TOKEN_ID" in str(excinfo.value)
    finally:
        env.close()

@pytest.mark.integration
def test_pause_without_pause_key_fails():
    """
    A token WITHOUT a pause key, attempting to pause it
    should hit TOKEN_HAS_NO_PAUSE_KEY error.
    """
    env = IntegrationTestEnv()
    try:
        # 1) Create a token with no pause_key
        token = (
            TokenCreateTransaction()
            .set_token_name("NoPause")
            .set_token_symbol("NOP")
            .set_decimals(0)
            .set_initial_supply(1)
            .set_treasury_account_id(env.operator_id)
            .set_token_type(TokenType.FUNGIBLE_COMMON)
            .set_supply_type(SupplyType.FINITE)
            .set_max_supply(1)
            .freeze_with(env.client)
        ).execute(env.client).tokenId

        # 2) Attempt to pause it
        tx = TokenPauseTransaction().set_token_id(token)
        tx.freeze_with(env.client)

        with pytest.raises(
            PrecheckError,
            match="failed precheck with status: TOKEN_HAS_NO_PAUSE_KEY"
        ):
            tx.execute(env.client)
    finally:
        env.close()


@pytest.mark.integration
def test_pause_prevents_transfers_and_reflects_in_info():
    """
    Create a token with a pause key, make a transfer,
    pause the token, verify transfers now fail,
    and confirm TokenInfoQuery reports PAUSED status.
    """
    env = IntegrationTestEnv()
    try:
        # 1) create a test account to receive tokens
        recv_key = PrivateKey.generate()
        recv_tx = (
            AccountCreateTransaction()
            .set_key(recv_key.public_key())
            .set_initial_balance(Hbar(1))
            .freeze_with(env.client)
        ).execute(env.client)
        recv = recv_tx.accountId

        # 2) create a token WITH a pause key
        token = env.create_fungible_token(pause_key=env.operator_key)

        # 3) associate and transfer some
        (
            TokenAssociateTransaction()
            .set_account_id(recv)
            .add_token_id(token)
            .freeze_with(env.client)
            .sign(recv_key)
        ).execute(env.client)
        (
            TransferTransaction()
            .add_token_transfer(token, env.operator_id, -10)
            .add_token_transfer(token, recv, 10)
            .freeze_with(env.client)
        ).execute(env.client)

        # balance check before pause
        bal = CryptoGetAccountBalanceQuery(recv).execute(env.client)
        assert bal.token_balances[token] == 10

        # 4) pause the token
        (
            TokenPauseTransaction()
            .set_token_id(token)
            .freeze_with(env.client)
            .sign(env.operator_key)
        ).execute(env.client)

        # info query should show PAUSED
        status = TokenInfoQuery().set_token_id(token).execute(env.client).token_status
        assert status.name == "PAUSED"

        # 5) any further transfer should now throw ReceiptStatusException TOKEN_IS_PAUSED
        with pytest.raises(ReceiptStatusException) as exc:
            (
                TransferTransaction()
                .add_token_transfer(token, env.operator_id, -1)
                .add_token_transfer(token, recv, 1)
                .freeze_with(env.client)
                .sign(env.operator_key)
                .execute(env.client)
            )
        assert "TOKEN_IS_PAUSED" in str(exc.value)

    finally:
        env.close()

@pytest.mark.integration
def test_double_pause_raises_token_already_paused():
    """
    Once a token is already paused, attempting to pause it again
    should hit the TOKEN_ALREADY_PAUSED precheck error.
    """
    env = IntegrationTestEnv()
    try:
        # Create a token with a pause key
        token = env.create_fungible_token(pause_key=env.operator_key)

        # First pause should succeed
        (
            TokenPauseTransaction()
            .set_token_id(token)
            .freeze_with(env.client)
            .sign(env.operator_key)
            .execute(env.client)
        )

        # Confirm status is PAUSED
        status = (
            TokenInfoQuery()
            .set_token_id(token)
            .execute(env.client)
            .token_status
        )
        assert status.name == "PAUSED"

        # Second pause should fail with TOKEN_ALREADY_PAUSED
        tx = TokenPauseTransaction().set_token_id(token)
        tx.freeze_with(env.client)
        tx.sign(env.operator_key)
        with pytest.raises(
            PrecheckError,
            match="failed precheck with status: TOKEN_ALREADY_PAUSED"
        ):
            tx.execute(env.client)

    finally:
        env.close()


@pytest.mark.integration
def test_pause_with_wrong_key_raises_sig_mismatch():
    """
    Signing a pause transaction with a key that is NOT the token's pause key
    should fail the precheck with SIG_MISMATCH.
    """
    env = IntegrationTestEnv()
    try:
        # Create a token whose pause key is the operator
        token = env.create_fungible_token(pause_key=env.operator_key)

        # Build & freeze the pause transaction
        tx = TokenPauseTransaction().set_token_id(token)
        tx.freeze_with(env.client)

        # Sign with a completely unrelated key
        wrong_key = PrivateKey.generate()
        tx.sign(wrong_key)

        # Expect signature mismatch at precheck
        with pytest.raises(
            PrecheckError,
            match="failed precheck with status: SIG_MISMATCH"
        ):
            tx.execute(env.client)

    finally:
        env.close()
