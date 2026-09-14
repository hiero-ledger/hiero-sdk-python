"""
Integration tests for MirrorNodeAccountBalanceQuery.

These tests verify the mirror-node REST replacement for
CryptoGetAccountBalanceQuery against a real Hiero network.

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
from hiero_sdk_python.query.mirror_node_account_balance_query import MirrorNodeAccountBalanceQuery


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

    Args:
        client: Hiero SDK client.
        account_id: Account to query.
        predicate: Function receiving Hbar and returning True when
            the expected balance has been reached.
        timeout: Maximum time to wait in seconds.
        interval: Time between queries in seconds.

    Returns:
        The Hbar balance reported by the mirror node.

    Raises:
        TimeoutError: If the expected balance is not observed.
    """
    deadline = time.monotonic() + timeout
    last_balance = None

    while time.monotonic() < deadline:
        try:
            balance = MirrorNodeAccountBalanceQuery().set_account_id(account_id).execute(client)

            last_balance = balance.hbars

            if predicate(last_balance):
                return last_balance

        except Exception:
            # The account may not have been indexed by the mirror node yet.
            # Keep retrying until the timeout expires.
            pass

        time.sleep(interval)

    raise TimeoutError(f"Timed out waiting for mirror node balance for {account_id}. Last balance: {last_balance}")


def test_can_fetch_balance_for_client_operator():
    """
    Can fetch the HBAR balance for the client operator.
    """
    client = Client.from_env()

    try:
        operator_id = client.operator_account_id

        balance = await_mirror_balance(
            client,
            operator_id,
            lambda balance: balance.to_tinybars() > 0,
        )

        assert balance.to_tinybars() > 0

    finally:
        client.close()


def test_can_fetch_balance_by_evm_address():
    """
    Can fetch the HBAR balance for an account addressed by its
    EVM address.
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

        evm_address_account_id = AccountId.from_evm_address("0x" + account_id.to_evm_address())

        balance = await_mirror_balance(
            client,
            evm_address_account_id,
            lambda value: value == initial_balance,
        )

        assert balance == initial_balance

    finally:
        client.close()


def test_can_fetch_balance_by_alias():
    """
    Can fetch the HBAR balance for an account addressed by its
    public key alias.
    """
    client = Client.from_env()

    try:
        key = PrivateKey.generate_ed25519()
        alias_account_id = key.public_key().to_account_id(0, 0)
        initial_balance = Hbar(1)

        # Transferring to an alias auto-creates the account.
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


def test_can_fetch_balance_for_contract():
    """
    Can fetch the HBAR balance of a contract passed as an account ID.
    """
    client = Client.from_env()

    try:
        # This is a placeholder for however the Python SDK's existing
        # contract test helpers create contracts.
        contract_id = create_test_contract(client)

        # The balances endpoint resolves contract IDs, so no separate
        # set_contract_id method is needed.
        contract_as_account_id = AccountId(
            contract_id.shard,
            contract_id.realm,
            contract_id.num,
        )

        # Fund the contract with a plain crypto transfer.
        # This avoids relying on a payable contract constructor.
        (
            TransferTransaction()
            .add_hbar_transfer(
                client.operator_account_id,
                -Hbar(1).to_tinybars(),
            )
            .add_hbar_transfer(
                contract_as_account_id,
                Hbar(1).to_tinybars(),
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

        assert balance == Hbar(1)

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

        with pytest.raises(
            Exception,
            match="INVALID_ACCOUNT_ID",
        ):
            (MirrorNodeAccountBalanceQuery().set_account_id(non_existent_account_id).execute(client))

    finally:
        client.close()


def test_fails_before_network_call_when_account_id_missing():
    """
    Fails before making a network call when no account ID is set.
    """
    client = Client.from_env()

    try:
        with pytest.raises(
            ValueError,
            match="account_id must be set",
        ):
            MirrorNodeAccountBalanceQuery().execute(client)

    finally:
        client.close()


def test_throws_invalid_account_id_for_unserved_shard():
    """
    An otherwise well-formed account ID in a shard that the mirror
    node does not serve should fail with INVALID_ACCOUNT_ID.
    """
    client = Client.from_env()

    try:
        account_id = AccountId.from_string("1.0.3")

        with pytest.raises(
            Exception,
            match="INVALID_ACCOUNT_ID",
        ):
            (MirrorNodeAccountBalanceQuery().set_account_id(account_id).set_max_attempts(1).execute(client))

    finally:
        client.close()


def create_test_contract(client: Client):
    """
    Create a test contract.

    Replace this with the Python SDK's existing contract test helper
    when one is available.
    """
    raise NotImplementedError("Use the existing Python SDK contract test helper here.")
