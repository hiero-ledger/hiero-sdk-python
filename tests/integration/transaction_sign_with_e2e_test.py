from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.account_info_query import AccountInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


def simulated_hsm(private_key: PrivateKey):
    """Return a signer callback that keeps the private key out of the SDK, like an HSM would."""

    def signer(body_bytes: bytes) -> bytes:
        return private_key.sign(body_bytes)

    return signer


def create_account(env, key: PrivateKey):
    """Create an account owned by key, funded with 2 HBAR."""
    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(key.public_key())
        .set_initial_balance(Hbar(2))
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed: {ResponseCode(receipt.status).name}"
    return receipt.account_id


@pytest.mark.integration
@pytest.mark.parametrize("key_factory", [PrivateKey.generate_ed25519, PrivateKey.generate_ecdsa])
def test_sign_with_external_signer_executes(env, key_factory):
    """Test that a transaction signed through a signer callback executes, for Ed25519 and ECDSA."""
    key = key_factory()
    account_id = create_account(env, key)

    tx = (
        TransferTransaction()
        .add_hbar_transfer(account_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(1).to_tinybars())
        .freeze_with(env.client)
        .sign_with(key.public_key(), simulated_hsm(key))
    )
    receipt = tx.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed: {ResponseCode(receipt.status).name}"


@pytest.mark.integration
def test_client_with_signer_based_operator_executes_transaction_and_paid_query(env):
    """Test that a client set up with set_operator_with can pay for transactions and queries."""
    client = Client(env.client.network)
    client.set_operator_with(env.operator_id, env.operator_key.public_key(), simulated_hsm(env.operator_key))
    assert client.operator_private_key is None

    receipt = (
        AccountCreateTransaction()
        .set_key_without_alias(PrivateKey.generate_ed25519().public_key())
        .set_initial_balance(Hbar(1))
        .execute(client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Account creation failed: {ResponseCode(receipt.status).name}"

    info = AccountInfoQuery().set_account_id(receipt.account_id).execute(client)
    assert info.account_id == receipt.account_id


@pytest.mark.integration
def test_transaction_with_non_operator_payer_skips_operator_signature(env):
    """Test that the operator does not sign a transaction it does not pay for."""
    payer_key = PrivateKey.generate_ed25519()
    payer_id = create_account(env, payer_key)

    tx = (
        TransferTransaction()
        .add_hbar_transfer(payer_id, -Hbar(1).to_tinybars())
        .add_hbar_transfer(env.operator_id, Hbar(1).to_tinybars())
        .set_transaction_id(TransactionId.generate(payer_id))
        .freeze_with(env.client)
        .sign(payer_key)
    )
    receipt = tx.execute(env.client)

    assert receipt.status == ResponseCode.SUCCESS, f"Transfer failed: {ResponseCode(receipt.status).name}"
    assert tx.is_signed_by(payer_key.public_key())
    assert not tx.is_signed_by(env.operator_key.public_key())


@pytest.mark.integration
def test_chunked_file_append_signed_with_external_signer_executes(env):
    """Test that sign_with signs every chunk for every node of a FileAppendTransaction."""
    file_key = PrivateKey.generate_ecdsa()
    create_receipt = (
        FileCreateTransaction()
        .set_keys(file_key.public_key())
        .set_contents(b"")
        .freeze_with(env.client)
        .sign(file_key)
        .execute(env.client)
    )
    assert create_receipt.status == ResponseCode.SUCCESS, (
        f"File creation failed: {ResponseCode(create_receipt.status).name}"
    )

    contents = b"signer-based chunk " * 60  # 1,140 bytes, 3 chunks of 512
    tx = (
        FileAppendTransaction()
        .set_file_id(create_receipt.file_id)
        .set_chunk_size(512)
        .set_contents(contents)
        .set_node_account_ids(env.client.get_node_account_ids())
        .freeze_with(env.client)
        .sign_with(file_key.public_key(), simulated_hsm(file_key))
    )
    assert len(tx._transaction_ids) == 3
    assert tx.is_signed_by(file_key.public_key())

    receipt = tx.execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS, f"File append failed: {ResponseCode(receipt.status).name}"

    file_contents = FileContentsQuery().set_file_id(create_receipt.file_id).execute(env.client)
    assert file_contents == contents
