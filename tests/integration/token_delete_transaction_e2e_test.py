from __future__ import annotations

import pytest

from hiero_sdk_python.query.token_info_query import TokenInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from tests.integration.utils import create_fungible_token


@pytest.mark.integration
def test_integration_token_delete_transaction_can_execute(env):
    token_id = create_fungible_token(env)

    assert token_id is not None, "TokenID not found in receipt. Token may not have been created."

    transaction = TokenDeleteTransaction(token_id=token_id)
    transaction.freeze_with(env.client)
    receipt = transaction.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token deletion failed with status: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_delete_token_from_bytes(env):
    """Test delete token transaction can be executed from bytes."""
    token_id = create_fungible_token(env)
    assert token_id is not None, "TokenID not found in receipt. Token may not have been created."

    original_tx = TokenDeleteTransaction(token_id=token_id)
    copy_tx = TokenDeleteTransaction.from_bytes(original_tx.to_bytes())
    receipt = copy_tx.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, (
        f"Token deletion failed with status: {ResponseCode(receipt.status).name}"
    )

    token_info = TokenInfoQuery(token_id=token_id).execute(env.client)
    assert token_info.is_deleted is True, "Token must have been deleted"
