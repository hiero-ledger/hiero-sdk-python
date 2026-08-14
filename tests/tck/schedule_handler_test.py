"""Tests for the TCK createSchedule handler helpers."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from tck.handlers.schedule import _build_scheduled_transaction
from tck.param.schedule import ScheduledTransactionParams


pytestmark = pytest.mark.unit


def test_build_scheduled_create_account_transaction():
    """Build the createAccount transaction used by the TCK schedule example."""
    transaction = _build_scheduled_transaction(
        ScheduledTransactionParams(
            method="createAccount",
            params={
                "initialBalance": "100",
                "memo": "new account",
                "commonTransactionParams": {
                    "maxTransactionFee": "123",
                    "memo": "scheduled transaction",
                },
            },
        ),
        "session-id",
    )

    assert isinstance(transaction, AccountCreateTransaction)
    assert transaction.account_memo == "new account"
    assert transaction.transaction_fee == 123
    assert transaction.memo == "scheduled transaction"

    scheduled_body = transaction.build_scheduled_body()

    assert scheduled_body.HasField("cryptoCreateAccount")
    assert scheduled_body.cryptoCreateAccount.initialBalance == 100
    assert scheduled_body.transactionFee == 123
    assert scheduled_body.memo == "scheduled transaction"
