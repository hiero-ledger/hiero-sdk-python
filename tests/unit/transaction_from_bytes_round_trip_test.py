from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.account.account_delete_transaction import AccountDeleteTransaction
from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import (
    TopicMessageSubmitTransaction,
)
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.contract.contract_delete_transaction import ContractDeleteTransaction
from hiero_sdk_python.contract.contract_execute_transaction import ContractExecuteTransaction
from hiero_sdk_python.contract.contract_update_transaction import ContractUpdateTransaction
from hiero_sdk_python.contract.ethereum_transaction import EthereumTransaction
from hiero_sdk_python.crypto import private_key
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.nodes.node_create_transaction import NodeCreateTransaction
from hiero_sdk_python.nodes.node_delete_transaction import NodeDeleteTransaction
from hiero_sdk_python.nodes.node_update_transaction import NodeUpdateTransaction
from hiero_sdk_python.nodes.registered_node_create_transaction import (
    RegisteredNodeCreateTransaction,
)
from hiero_sdk_python.nodes.registered_node_delete_transaction import (
    RegisteredNodeDeleteTransaction,
)
from hiero_sdk_python.nodes.registered_node_update_transaction import (
    RegisteredNodeUpdateTransaction,
)
from hiero_sdk_python.prng_transaction import PrngTransaction
from hiero_sdk_python.schedule.schedule_create_transaction import ScheduleCreateTransaction
from hiero_sdk_python.schedule.schedule_delete_transaction import ScheduleDeleteTransaction
from hiero_sdk_python.schedule.schedule_sign_transaction import ScheduleSignTransaction
from hiero_sdk_python.system.freeze_transaction import FreezeTransaction
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_create_transaction import TokenCreateTransaction
from hiero_sdk_python.tokens.token_delete_transaction import TokenDeleteTransaction
from hiero_sdk_python.tokens.token_dissociate_transaction import TokenDissociateTransaction
from hiero_sdk_python.tokens.token_fee_schedule_update_transaction import (
    TokenFeeScheduleUpdateTransaction,
)
from hiero_sdk_python.tokens.token_freeze_transaction import TokenFreezeTransaction
from hiero_sdk_python.tokens.token_grant_kyc_transaction import TokenGrantKycTransaction
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.tokens.token_pause_transaction import TokenPauseTransaction
from hiero_sdk_python.tokens.token_reject_transaction import TokenRejectTransaction
from hiero_sdk_python.tokens.token_revoke_kyc_transaction import TokenRevokeKycTransaction
from hiero_sdk_python.tokens.token_unfreeze_transaction import TokenUnfreezeTransaction
from hiero_sdk_python.tokens.token_unpause_transaction import TokenUnpauseTransaction
from hiero_sdk_python.tokens.token_update_nfts_transaction import TokenUpdateNftsTransaction
from hiero_sdk_python.tokens.token_update_transaction import TokenUpdateTransaction
from hiero_sdk_python.tokens.token_wipe_transaction import TokenWipeTransaction
from hiero_sdk_python.transaction.batch_transaction import BatchTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class RoundTripCase:
    """Registry entry for one transaction round-trip test case."""

    transaction_class: type[Transaction]
    builder: Callable
    fields: tuple[str, ...]


MISSING_FROM_PROTOBUF = "Follow-up work required to add a working _from_protobuf override for this transaction type."

FILE_CREATE_FROM_PROTOBUF_DISCREPANCY = (
    "Follow-up work required to add _from_protobuf to FileCreateTransaction; "
    "the ticket identifies FileCreateTransaction as a reference implementation, "
    "but the current class does not define a _from_protobuf classmethod."
)


def _transfer(mock_account_ids, transaction_id, private_key):
    sender, receiver, _, _, _ = mock_account_ids

    return (
        TransferTransaction()
        .add_hbar_transfer(
            sender,
            -1000,
        )
        .add_hbar_transfer(
            receiver,
            1000,
        )
    )


def _account_create():
    return AccountCreateTransaction().set_key(private_key.public_key())


def _account_delete(mock_account_ids):
    sender, receiver, _, _, _ = mock_account_ids

    return AccountDeleteTransaction().set_delete_account_id(sender).set_transfer_account_id(receiver)


def _account_update(mock_account_ids):
    account_id, _, _, _, _ = mock_account_ids

    return AccountUpdateTransaction().set_account_id(account_id).set_transaction_memo("round-trip")


def _file_create():
    return (
        FileCreateTransaction()
        .set_keys([private_key.public_key()])
        .set_contents(b"round-trip file contents")
        .set_file_memo("round-trip file")
    )


def _file_append():
    return FileAppendTransaction().set_file_id("0.0.2").set_contents(b"round-trip append")


def _file_update():
    return FileUpdateTransaction().set_file_id("0.0.2").set_contents(b"round-trip update")


def _file_delete():
    return FileDeleteTransaction().set_file_id("0.0.2")


def _freeze():
    return FreezeTransaction().set_start_time(1).set_file_id("0.0.2").set_file_hash(b"round-trip-file-hash")


def _topic_create():
    return TopicCreateTransaction().set_topic_memo("round-trip")


def _topic_update():
    return TopicUpdateTransaction().set_topic_id("0.0.1234").set_topic_memo("round-trip")


def _topic_delete():
    return TopicDeleteTransaction().set_topic_id("0.0.1234")


def _topic_submit():
    return TopicMessageSubmitTransaction().set_topic_id("0.0.1234").set_message(b"round-trip message")


def _token_create():
    return TokenCreateTransaction().set_token_name("Round Trip Token").set_symbol("RT")


def _token_update(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenUpdateTransaction().set_token_id(token_id).set_token_name("Updated Token")


def _token_delete(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenDeleteTransaction().set_token_id(token_id)


def _token_freeze(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenFreezeTransaction().set_token_id(token_id).set_account_id(account_id)


def _token_unfreeze(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenUnfreezeTransaction().set_token_id(token_id).set_account_id(account_id)


def _token_pause(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenPauseTransaction().set_token_id(token_id)


def _token_unpause(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenUnpauseTransaction().set_token_id(token_id)


def _token_grant_kyc(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenGrantKycTransaction().set_token_id(token_id).set_account_id(account_id)


def _token_revoke_kyc(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenRevokeKycTransaction().set_token_id(token_id).set_account_id(account_id)


def _token_associate(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenAssociateTransaction().set_account_id(account_id).set_token_ids([token_id])


def _token_dissociate(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenDissociateTransaction().set_account_id(account_id).set_token_ids([token_id])


def _token_mint(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenMintTransaction().set_token_id(token_id).set_amount(100)


def _token_wipe(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenWipeTransaction().set_token_id(token_id).set_account_id(account_id).set_amount(1)


def _token_reject(mock_account_ids):
    account_id, _, _, token_id, _ = mock_account_ids

    return TokenRejectTransaction().set_owner_id(account_id).set_token_ids([token_id])


def _token_claim_airdrop(mock_account_ids):
    sender, receiver, _, token_id, _ = mock_account_ids

    return TokenClaimAirdropTransaction().set_pending_airdrop_ids(
        [
            {
                "sender_id": sender,
                "receiver_id": receiver,
                "token_id": token_id,
            }
        ]
    )


def _token_fee_schedule_update(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenFeeScheduleUpdateTransaction().set_token_id(token_id).set_custom_fees([])


def _token_update_nfts(mock_account_ids):
    _, _, _, token_id, _ = mock_account_ids

    return TokenUpdateNftsTransaction().set_token_id(token_id)


def _prng():
    return PrngTransaction().set_range(100)


def _batch(mock_account_ids, transaction_id, private_key):
    sender, receiver, node_id, _, _ = mock_account_ids

    inner_transaction = TransferTransaction().add_hbar_transfer(sender, -1000).add_hbar_transfer(receiver, 1000)

    inner_transaction.set_transaction_id(transaction_id)
    inner_transaction.set_node_account_ids([node_id])
    inner_transaction.set_batch_key(private_key.public_key())
    inner_transaction.freeze()

    return BatchTransaction().add_inner_transaction(inner_transaction)


def _node_create(mock_account_ids, transaction_id, private_key):
    return NodeCreateTransaction()


def _node_update(mock_account_ids, transaction_id, private_key):
    return NodeUpdateTransaction()


def _node_delete(mock_account_ids, transaction_id, private_key):
    return NodeDeleteTransaction()


def _registered_node_create(mock_account_ids, transaction_id, private_key):
    return RegisteredNodeCreateTransaction()


def _registered_node_update(mock_account_ids, transaction_id, private_key):
    return RegisteredNodeUpdateTransaction()


def _registered_node_delete(mock_account_ids, transaction_id, private_key):
    return RegisteredNodeDeleteTransaction().set_registered_node_id(1)


def _schedule_create():
    return ScheduleCreateTransaction()


def _schedule_delete():
    return ScheduleDeleteTransaction()


def _schedule_sign():
    return ScheduleSignTransaction()


def _contract_create():
    return ContractCreateTransaction().set_bytecode(b"\x01")


def _contract_execute():
    return ContractExecuteTransaction()


def _contract_update():
    return ContractUpdateTransaction()


def _contract_delete():
    return ContractDeleteTransaction()


def _ethereum():
    return EthereumTransaction()


def _case(transaction_class, builder, fields, reason=None):
    """Create one parametrized registry entry."""
    marks = pytest.mark.xfail(strict=True, reason=reason) if reason else ()

    return pytest.param(
        RoundTripCase(
            transaction_class=transaction_class,
            builder=builder,
            fields=fields,
        ),
        marks=marks,
        id=transaction_class.__name__,
    )


CASES = [
    _case(
        TransferTransaction,
        _transfer,
        ("hbar_transfers",),
    ),
    _case(
        BatchTransaction,
        _batch,
        ("inner_transactions",),
    ),
    _case(
        NodeCreateTransaction,
        _node_create,
        (),
    ),
    _case(
        NodeUpdateTransaction,
        _node_update,
        (),
    ),
    _case(
        RegisteredNodeCreateTransaction,
        _registered_node_create,
        (),
    ),
    _case(
        RegisteredNodeUpdateTransaction,
        _registered_node_update,
        (),
    ),
    _case(
        RegisteredNodeDeleteTransaction,
        _registered_node_delete,
        (),
    ),
    _case(
        AccountCreateTransaction,
        _account_create,
        ("key",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        AccountDeleteTransaction,
        _account_delete,
        ("delete_account_id", "transfer_account_id"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        AccountUpdateTransaction,
        _account_update,
        ("account_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        FileCreateTransaction,
        _file_create,
        ("keys", "contents", "file_memo"),
        FILE_CREATE_FROM_PROTOBUF_DISCREPANCY,
    ),
    _case(
        FileAppendTransaction,
        _file_append,
        ("file_id", "contents"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        FileUpdateTransaction,
        _file_update,
        ("file_id", "contents"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        FileDeleteTransaction,
        _file_delete,
        ("file_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        FreezeTransaction,
        _freeze,
        ("start_time", "file_id", "file_hash", "freeze_type"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TopicCreateTransaction,
        _topic_create,
        ("topic_memo",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TopicUpdateTransaction,
        _topic_update,
        ("topic_id", "topic_memo"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TopicDeleteTransaction,
        _topic_delete,
        ("topic_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TopicMessageSubmitTransaction,
        _topic_submit,
        ("topic_id", "message"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenCreateTransaction,
        _token_create,
        ("token_name", "symbol"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenUpdateTransaction,
        _token_update,
        ("token_id", "token_name"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenDeleteTransaction,
        _token_delete,
        ("token_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenFreezeTransaction,
        _token_freeze,
        ("token_id", "account_id"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenUnfreezeTransaction,
        _token_unfreeze,
        ("token_id", "account_id"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenPauseTransaction,
        _token_pause,
        ("token_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenUnpauseTransaction,
        _token_unpause,
        ("token_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenGrantKycTransaction,
        _token_grant_kyc,
        ("token_id", "account_id"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenRevokeKycTransaction,
        _token_revoke_kyc,
        ("token_id", "account_id"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenAssociateTransaction,
        _token_associate,
        ("account_id", "token_ids"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenDissociateTransaction,
        _token_dissociate,
        ("account_id", "token_ids"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenMintTransaction,
        _token_mint,
        ("token_id", "amount"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenWipeTransaction,
        _token_wipe,
        ("token_id", "account_id", "amount"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenRejectTransaction,
        _token_reject,
        ("owner_id", "token_ids"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenClaimAirdropTransaction,
        _token_claim_airdrop,
        ("pending_airdrop_ids",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenFeeScheduleUpdateTransaction,
        _token_fee_schedule_update,
        ("token_id", "custom_fees"),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        TokenUpdateNftsTransaction,
        _token_update_nfts,
        ("token_id",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        PrngTransaction,
        _prng,
        ("range",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ScheduleCreateTransaction,
        _schedule_create,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ScheduleDeleteTransaction,
        _schedule_delete,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ScheduleSignTransaction,
        _schedule_sign,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ContractCreateTransaction,
        _contract_create,
        ("bytecode",),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ContractExecuteTransaction,
        _contract_execute,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ContractUpdateTransaction,
        _contract_update,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        ContractDeleteTransaction,
        _contract_delete,
        (),
        MISSING_FROM_PROTOBUF,
    ),
    _case(
        EthereumTransaction,
        _ethereum,
        (),
        MISSING_FROM_PROTOBUF,
    ),
]


@pytest.mark.parametrize("case", CASES)
def test_transaction_from_bytes_round_trip(
    case,
    mock_account_ids,
    transaction_id,
    private_key,
):
    """Verify dispatch, restoration, and byte-for-byte round-trip fidelity."""
    transaction = case.builder(
        mock_account_ids,
        transaction_id,
        private_key,
    )

    _, _, node_id, _, _ = mock_account_ids

    transaction.set_transaction_id(transaction_id)
    transaction.set_node_account_ids([node_id])
    transaction.freeze()

    original = transaction.to_bytes()

    restored = Transaction.from_bytes(original)

    assert isinstance(restored, case.transaction_class)

    for field_name in case.fields:
        original_field = getattr(transaction, field_name)
        restored_field = getattr(restored, field_name)

        if field_name == "hbar_transfers":
            assert [(transfer.account_id, transfer.amount, transfer.is_approved) for transfer in restored_field] == [
                (transfer.account_id, transfer.amount, transfer.is_approved) for transfer in original_field
            ]

        elif field_name == "inner_transactions":
            assert len(restored_field) == len(original_field)

            for restored_inner, original_inner in zip(
                restored_field,
                original_field,
                strict=True,
            ):
                assert isinstance(restored_inner, type(original_inner))
                assert restored_inner.to_bytes() == original_inner.to_bytes()

        else:
            assert restored_field == original_field

    assert restored.to_bytes() == original
