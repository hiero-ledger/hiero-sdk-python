from __future__ import annotations

import time

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.response_code import ResponseCode


# The network accepts durations down to 15s, but at precheck it only honours
# validStart + (duration - 10s buffer), and TransactionId.generate() backdates validStart
# by 5-8s. At 15s a freshly generated ID is already expired, so a regenerated ID would
# expire again. 25s leaves a regenerated ID at least 7s to reach the node.
VALID_DURATION = 25
VALIDITY_BUFFER = 10
MIN_BACKDATE = 5


def _expired_transaction(env):
    """Freeze an AccountCreateTransaction and wait until its transaction ID has expired."""
    tx = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate())
        .set_initial_balance(1)
        .set_transaction_valid_duration(VALID_DURATION)
        .freeze_with(env.client)
    )
    # Expiry depends only on the validity window, so wait out its longest possible case.
    time.sleep(VALID_DURATION - VALIDITY_BUFFER - MIN_BACKDATE + 3)
    return tx


@pytest.mark.integration
def test_expired_transaction_id_is_regenerated(env):
    """Test that an expired SDK-generated ID is replaced and the transaction succeeds."""
    tx = _expired_transaction(env)
    # _current_transaction_id does not pin; reading the public transaction_id here would.
    original_transaction_id = tx._current_transaction_id

    receipt = tx.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS
    assert tx.transaction_id != original_transaction_id
    assert tx.transaction_id.account_id == env.operator_id


@pytest.mark.integration
def test_expired_transaction_id_is_kept_when_regeneration_disabled(env):
    """Test that TRANSACTION_EXPIRED is raised when regeneration is disabled."""
    env.client.set_default_regenerate_transaction_id(False)
    tx = _expired_transaction(env)
    original_transaction_id = tx._current_transaction_id

    with pytest.raises(PrecheckError) as exc_info:
        tx.execute(env.client)

    assert exc_info.value.status == ResponseCode.TRANSACTION_EXPIRED
    assert tx.transaction_id == original_transaction_id
