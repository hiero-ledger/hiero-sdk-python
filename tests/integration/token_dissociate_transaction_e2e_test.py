from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from tests.integration.utils import create_fungible_token


def _create_associated_account(env):
    """Creates an account and associates it with a fungible token."""
    private_key = PrivateKey.generate()

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(private_key)
        .set_initial_balance(Hbar(2))
        .set_account_memo("Recipient Account")
        .freeze_with(env.client)
        .execute(env.client)
    )

    account_id = receipt.account_id
    token_id = create_fungible_token(env)

    associate_tx = TokenAssociateTransaction().set_account_id(account_id).set_token_ids([token_id])
    associate_tx.freeze_with(env.client)
    associate_tx.sign(private_key)

    receipt = associate_tx.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token association failed with status: {ResponseCode(receipt.status).name}"
    )

    return account_id, private_key, token_id


@pytest.mark.integration
def test_integration_token_dissociate_transaction_can_execute(env):
    """Test token dissociate transaction can be executed successfully."""
    account_id, account_private_key, token_id = _create_associated_account(env)

    dissociate_transaction = TokenDissociateTransaction(account_id=account_id, token_ids=[token_id])
    dissociate_transaction.freeze_with(env.client)
    dissociate_transaction.sign(account_private_key)

    receipt = dissociate_transaction.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token dissociation failed with status: {ResponseCode(receipt.status).name}"
    )


def test_token_dissociate_transaction_can_execute_with_no_tokensId(env):
    """Test token dissociate transaction can be executed without setting the tokenIds."""
    account_id, account_private_key, _ = _create_associated_account(env)

    dissociate_transaction = TokenDissociateTransaction(account_id=account_id)
    dissociate_transaction.freeze_with(env.client)
    dissociate_transaction.sign(account_private_key)

    receipt = dissociate_transaction.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token dissociation failed with status: {ResponseCode(receipt.status).name}"
    )


def test_token_dissociate_transaction_raise_error_if_account_id_not_set(env):
    """Test token dissociate transaction raises PrecheckError if accountId not set."""
    a_, account_private_key, token_id = _create_associated_account(env)

    dissociate_transaction = TokenDissociateTransaction(token_ids=[token_id])
    dissociate_transaction.freeze_with(env.client)
    dissociate_transaction.sign(account_private_key)

    with pytest.raises(PrecheckError):
        dissociate_transaction.execute(env.client)
