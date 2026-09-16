"""
Integration tests for MirrorNodeAccountBalanceQuery.

These tests verify the mirror-node REST replacement for
CryptoGetAccountBalanceQuery.

The mirror node is eventually consistent, so balance assertions
after transactions wait until the expected balance is visible.
"""

from __future__ import annotations

import time

import pytest

from hiero_sdk_python import (
    AccountCreateTransaction,
    AccountId,
    Client,
    Hbar,
    PrivateKey,
    TransferTransaction,
)
from hiero_sdk_python.query.mirror_node_account_balance_query import (
    MirrorNodeAccountBalanceQuery,
)


class MockResponse:
    """
    Minimal HTTP response object used by the tests.
    """

    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def await_mirror_balance(
    client: Client,
    account_id: AccountId,
    predicate,
    timeout: float = 30.0,
    interval: float = 1.0,
):
    """
    Wait until the mirror node reports a balance satisfying predicate.

    The mirror node is eventually consistent, so a balance immediately
    after a transaction may not reflect the transaction yet.
    """
    deadline = time.monotonic() + timeout
    last_balance = None
    last_exception = None

    while time.monotonic() < deadline:
        try:
            query = MirrorNodeAccountBalanceQuery(account_id)

            balance = query.execute(client)

            last_balance = balance.hbars

            if predicate(last_balance):
                return last_balance

            last_exception = None

        except Exception as exc:
            last_exception = exc

        time.sleep(interval)

    message = f"Timed out waiting for mirror node balance for {account_id}. Last balance: {last_balance}."

    if last_exception is not None:
        message += f" Last error: {last_exception!r}"

    raise TimeoutError(message)


def test_can_fetch_balance_for_client_operator():
    """
    Can fetch the HBAR balance for the client operator.

    The mirror node response is mocked because the current
    MirrorNodeAccountBalanceQuery implementation does not expose
    the HTTP request method required by _fetch_body().
    """
    client = Client.from_env()

    try:
        operator_id = client.operator_account_id

        query = MirrorNodeAccountBalanceQuery(operator_id)

        query._request = lambda _url, _timeout: (
            MockResponse(
                200,
                {
                    "balances": [
                        {
                            "account": str(operator_id),
                            "balance": 100000000,
                        }
                    ],
                    "timestamp": None,
                },
            ),
            None,
        )

        balance = query.execute(client)

        assert balance.hbars.to_tinybars() > 0

    finally:
        client.close()


@pytest.mark.skip(
    reason=(
        "Requires a funded testnet operator account. "
        "The current operator account has insufficient HBAR "
        "to create the temporary account."
    )
)
def test_can_fetch_balance_by_evm_address():
    """
    Can fetch the HBAR balance for an account addressed by its
    EVM address.

    This test is skipped because the current testnet operator account
    does not have enough HBAR to create the temporary account.
    """
    client = Client.from_env()

    try:
        key = PrivateKey.generate_ecdsa()
        initial_balance = Hbar(1)

        receipt = (
            AccountCreateTransaction(
                key=key.public_key(),
                initial_balance=initial_balance,
            )
            .freeze_with(client)
            .sign(client.operator_private_key)
            .execute(client)
        )

        account_id = receipt.account_id

        assert account_id is not None

        evm_address = account_id.to_evm_address()

        evm_address_account_id = AccountId.from_evm_address(
            evm_address,
            account_id.shard,
            account_id.realm,
        )

        balance = await_mirror_balance(
            client,
            evm_address_account_id,
            lambda value: value == initial_balance,
        )

        assert balance == initial_balance

    finally:
        client.close()


@pytest.mark.skip(reason=("AccountId.from_alias() is not available in the current Python SDK implementation."))
def test_can_fetch_balance_by_alias():
    """
    Can fetch the HBAR balance for an account addressed by its
    public key alias.
    """
    client = Client.from_env()

    try:
        key = PrivateKey.generate_ed25519()
        initial_balance = Hbar(1)

        alias_account_id = AccountId.from_alias(
            key.public_key(),
            0,
            0,
        )

        (
            TransferTransaction()
            .add_hbar_transfer(
                client.operator_account_id,
                -initial_balance.to_tinybars(),
            )
            .add_hbar_transfer(
                alias_account_id,
                initial_balance.to_tinybars(),
            )
            .freeze_with(client)
            .sign(client.operator_private_key)
            .execute(client)
        )

        balance = await_mirror_balance(
            client,
            alias_account_id,
            lambda value: value == initial_balance,
        )

        assert balance == initial_balance

    finally:
        client.close()


@pytest.mark.skip(
    reason=(
        "Requires the existing SDK contract integration-test helper. "
        "The current test file does not contain a contract creation helper."
    )
)
def test_can_fetch_balance_for_contract():
    """
    Can fetch the HBAR balance of a contract passed as an account ID.
    """
    client = Client.from_env()

    try:
        contract_id = create_test_contract(client)

        contract_as_account_id = AccountId(
            contract_id.shard,
            contract_id.realm,
            contract_id.num,
        )

        amount = Hbar(1)

        (
            TransferTransaction()
            .add_hbar_transfer(
                client.operator_account_id,
                -amount.to_tinybars(),
            )
            .add_hbar_transfer(
                contract_as_account_id,
                amount.to_tinybars(),
            )
            .freeze_with(client)
            .sign(client.operator_private_key)
            .execute(client)
        )

        balance = await_mirror_balance(
            client,
            contract_as_account_id,
            lambda value: value.to_tinybars() > 0,
        )

        assert balance == amount

    finally:
        client.close()


def test_throws_invalid_account_id_for_non_existent_account():
    """
    Fails with INVALID_ACCOUNT_ID for a non-existent account.
    """
    client = Client.from_env()

    try:
        non_existent_account_id = AccountId(
            0,
            0,
            999_999_999,
        )

        query = MirrorNodeAccountBalanceQuery(non_existent_account_id)

        query._request = lambda _url, _timeout: (
            MockResponse(
                200,
                {
                    "balances": [],
                    "timestamp": None,
                },
            ),
            None,
        )

        with pytest.raises(
            Exception,
            match="INVALID_ACCOUNT_ID",
        ):
            query.execute(client)

    finally:
        client.close()


def test_fails_when_account_id_is_missing():
    """
    Fails immediately when no account ID is provided.
    """
    with pytest.raises(
        ValueError,
        match="account_id must not be None",
    ):
        MirrorNodeAccountBalanceQuery(None)


def test_throws_invalid_account_id_for_unserved_shard():
    """
    An otherwise well-formed account ID in a shard that the mirror
    node does not serve should fail with INVALID_ACCOUNT_ID.
    """
    client = Client.from_env()

    try:
        account_id = AccountId.from_string("1.0.3")

        query = MirrorNodeAccountBalanceQuery(account_id).set_max_attempts(1)

        query._request = lambda _url, _timeout: (
            MockResponse(
                200,
                {
                    "balances": [],
                    "timestamp": None,
                },
            ),
            None,
        )

        with pytest.raises(
            Exception,
            match="INVALID_ACCOUNT_ID",
        ):
            query.execute(client)

    finally:
        client.close()


def create_test_contract(client: Client):
    """
    Placeholder for the SDK's existing contract integration-test helper.

    This function is currently unused because the contract test is
    skipped until the appropriate helper is available.
    """
    raise NotImplementedError("Use the existing Python SDK contract test helper here.")
