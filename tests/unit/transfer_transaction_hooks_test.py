"""Unit tests for HIP-1195 hook calls on TransferTransaction."""

from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hooks.evm_hook_call import EvmHookCall
from hiero_sdk_python.hooks.fungible_hook_call import FungibleHookCall
from hiero_sdk_python.hooks.fungible_hook_type import FungibleHookType
from hiero_sdk_python.hooks.nft_hook_call import NftHookCall
from hiero_sdk_python.hooks.nft_hook_type import NftHookType
from hiero_sdk_python.tokens.hbar_transfer import HbarTransfer
from hiero_sdk_python.tokens.token_nft_transfer import TokenNftTransfer
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


pytestmark = pytest.mark.unit

SENDER = AccountId(0, 0, 100)
RECEIVER = AccountId(0, 0, 200)


def fungible(hook_id=1, hook_type=FungibleHookType.PRE_TX_ALLOWANCE_HOOK):
    return FungibleHookCall(hook_id=hook_id, evm_hook_call=EvmHookCall(b"\x01", 25_000), hook_type=hook_type)


def nft(hook_type, hook_id=2):
    return NftHookCall(hook_id=hook_id, evm_hook_call=EvmHookCall(b"\x02", 30_000), hook_type=hook_type)


def build(tx, mock_account_ids):
    operator_id, _, node_account_id, _, _ = mock_account_ids
    tx.operator_account_id = operator_id
    tx.set_node_account_ids([node_account_id])
    return tx.build_transaction_body().cryptoTransfer


# --- HBAR -----------------------------------------------------------------------------


@pytest.mark.parametrize("hook_type", list(FungibleHookType))
def test_add_hbar_transfer_with_hook(mock_account_ids, hook_type):
    hook = fungible(hook_type=hook_type)
    tx = TransferTransaction().add_hbar_transfer_with_hook(SENDER, Hbar(-1), hook).add_hbar_transfer(RECEIVER, Hbar(1))

    body = build(tx, mock_account_ids)

    sender_amount, receiver_amount = body.transfers.accountAmounts
    assert sender_amount.WhichOneof("hook_call") == hook_type.value
    assert sender_amount.amount == -100_000_000
    assert receiver_amount.WhichOneof("hook_call") is None


def test_add_hbar_transfer_with_hook_requires_fungible_hook_call():
    with pytest.raises(TypeError):
        TransferTransaction().add_hbar_transfer_with_hook(SENDER, -1, None)
    with pytest.raises(TypeError):
        TransferTransaction().add_hbar_transfer_with_hook(SENDER, -1, nft(NftHookType.PRE_HOOK_SENDER))


def test_hbar_hook_merges_into_existing_transfer_for_same_account():
    hook = fungible()
    tx = TransferTransaction().add_hbar_transfer(SENDER, -5).add_hbar_transfer_with_hook(SENDER, -5, hook)

    assert len(tx.hbar_transfers) == 1
    assert tx.hbar_transfers[0].amount == -10
    assert tx.hbar_transfers[0].hook_call == hook


def test_hbar_same_hook_twice_merges():
    tx = (
        TransferTransaction()
        .add_hbar_transfer_with_hook(SENDER, -5, fungible())
        .add_hbar_transfer_with_hook(SENDER, -5, fungible())
    )

    assert tx.hbar_transfers[0].amount == -10


def test_hbar_conflicting_hooks_for_same_account_raise():
    tx = TransferTransaction().add_hbar_transfer_with_hook(SENDER, -5, fungible(hook_id=1))

    with pytest.raises(ValueError, match="different hook call"):
        tx.add_hbar_transfer_with_hook(SENDER, -5, fungible(hook_id=2))


def test_hbar_plain_transfer_after_hook_keeps_hook():
    hook = fungible()
    tx = TransferTransaction().add_hbar_transfer_with_hook(SENDER, -5, hook).add_hbar_transfer(SENDER, -5)

    assert tx.hbar_transfers[0].hook_call == hook


def test_approved_hbar_transfer_with_hook_rejected_on_build():
    transfer = HbarTransfer(SENDER, -5, is_approved=True, hook_call=fungible())

    with pytest.raises(ValueError, match="approved"):
        transfer._to_proto()


# --- Fungible tokens -------------------------------------------------------------------


def test_add_token_transfer_with_hook(mock_account_ids, token_id):
    hook = fungible(hook_type=FungibleHookType.PRE_POST_TX_ALLOWANCE_HOOK)
    tx = (
        TransferTransaction()
        .add_token_transfer_with_hook(token_id, SENDER, -10, hook)
        .add_token_transfer(token_id, RECEIVER, 10)
    )

    body = build(tx, mock_account_ids)

    sender_amount, receiver_amount = body.tokenTransfers[0].transfers
    assert sender_amount.WhichOneof("hook_call") == "pre_post_tx_allowance_hook"
    assert sender_amount.pre_post_tx_allowance_hook.hook_id == 1
    assert receiver_amount.WhichOneof("hook_call") is None


def test_add_token_transfer_with_hook_validation(token_id):
    with pytest.raises(TypeError):
        TransferTransaction().add_token_transfer_with_hook(token_id, SENDER, -10, None)

    tx = TransferTransaction().add_token_transfer_with_hook(token_id, SENDER, -10, fungible(hook_id=1))
    with pytest.raises(ValueError, match="different hook call"):
        tx.add_token_transfer_with_hook(token_id, SENDER, -10, fungible(hook_id=2))


def test_approved_token_transfer_with_hook_rejected_on_build(token_id):
    transfer = TokenTransfer(token_id, SENDER, -5, is_approved=True, hook_call=fungible())

    with pytest.raises(ValueError, match="approved"):
        transfer._to_proto()


# --- NFTs ------------------------------------------------------------------------------


@pytest.mark.parametrize("sender_type", [NftHookType.PRE_HOOK_SENDER, NftHookType.PRE_POST_HOOK_SENDER])
@pytest.mark.parametrize("receiver_type", [NftHookType.PRE_HOOK_RECEIVER, NftHookType.PRE_POST_HOOK_RECEIVER])
def test_add_nft_transfer_with_both_hooks(mock_account_ids, nft_id, sender_type, receiver_type):
    tx = TransferTransaction().add_nft_transfer_with_hook(
        nft_id, SENDER, RECEIVER, nft(sender_type, hook_id=3), nft(receiver_type, hook_id=4)
    )

    body = build(tx, mock_account_ids)

    nft_transfer = body.tokenTransfers[0].nftTransfers[0]
    assert nft_transfer.serialNumber == nft_id.serial_number
    assert nft_transfer.WhichOneof("sender_allowance_hook_call") == sender_type.value
    assert nft_transfer.WhichOneof("receiver_allowance_hook_call") == receiver_type.value


def test_add_nft_transfer_with_receiver_hook_only(mock_account_ids, nft_id):
    tx = TransferTransaction().add_nft_transfer_with_hook(
        nft_id, SENDER, RECEIVER, receiver_hook_call=nft(NftHookType.PRE_HOOK_RECEIVER)
    )

    nft_transfer = build(tx, mock_account_ids).tokenTransfers[0].nftTransfers[0]

    assert nft_transfer.WhichOneof("sender_allowance_hook_call") is None
    assert nft_transfer.WhichOneof("receiver_allowance_hook_call") == "pre_tx_receiver_allowance_hook"


def test_add_nft_transfer_with_hook_requires_a_hook(nft_id):
    with pytest.raises(ValueError, match="At least one"):
        TransferTransaction().add_nft_transfer_with_hook(nft_id, SENDER, RECEIVER)


def test_add_nft_transfer_with_hook_rejects_wrong_side(nft_id):
    with pytest.raises(ValueError, match="sender_hook_call"):
        TransferTransaction().add_nft_transfer_with_hook(
            nft_id, SENDER, RECEIVER, sender_hook_call=nft(NftHookType.PRE_HOOK_RECEIVER)
        )
    with pytest.raises(ValueError, match="receiver_hook_call"):
        TransferTransaction().add_nft_transfer_with_hook(
            nft_id, SENDER, RECEIVER, receiver_hook_call=nft(NftHookType.PRE_POST_HOOK_SENDER)
        )


def test_add_nft_transfer_with_hook_rejects_wrong_types(nft_id):
    with pytest.raises(TypeError):
        TransferTransaction().add_nft_transfer_with_hook(nft_id, SENDER, RECEIVER, sender_hook_call=fungible())
    with pytest.raises(TypeError):
        TransferTransaction().add_nft_transfer_with_hook(
            "0.0.1/1", SENDER, RECEIVER, sender_hook_call=nft(NftHookType.PRE_HOOK_SENDER)
        )


def test_nft_proto_rejects_approved_sender_hook(token_id):
    transfer = TokenNftTransfer(token_id, SENDER, RECEIVER, 1, True, nft(NftHookType.PRE_HOOK_SENDER))

    with pytest.raises(ValueError, match="approved"):
        transfer._to_proto()


def test_nft_proto_allows_approved_receiver_hook(token_id):
    transfer = TokenNftTransfer(token_id, SENDER, RECEIVER, 1, True, None, nft(NftHookType.PRE_HOOK_RECEIVER))

    proto = transfer._to_proto()

    assert proto.is_approval
    assert proto.WhichOneof("receiver_allowance_hook_call") == "pre_tx_receiver_allowance_hook"


def test_nft_proto_rejects_wrong_side_set_directly(token_id):
    with pytest.raises(ValueError, match="sender NftHookType"):
        TokenNftTransfer(token_id, SENDER, RECEIVER, 1, sender_hook_call=nft(NftHookType.PRE_HOOK_RECEIVER))._to_proto()
    with pytest.raises(ValueError, match="receiver NftHookType"):
        TokenNftTransfer(token_id, SENDER, RECEIVER, 1, receiver_hook_call=nft(NftHookType.PRE_HOOK_SENDER))._to_proto()


# --- Round trips -----------------------------------------------------------------------


def test_from_bytes_restores_all_hook_calls(mock_client, token_id, nft_id):
    hbar_hook = fungible(hook_id=1)
    token_hook = fungible(hook_id=2, hook_type=FungibleHookType.PRE_POST_TX_ALLOWANCE_HOOK)
    sender_hook = nft(NftHookType.PRE_POST_HOOK_SENDER, hook_id=3)
    receiver_hook = nft(NftHookType.PRE_HOOK_RECEIVER, hook_id=4)
    original = (
        TransferTransaction()
        .add_hbar_transfer_with_hook(SENDER, -10, hbar_hook)
        .add_hbar_transfer(RECEIVER, 10)
        .add_token_transfer_with_hook(token_id, SENDER, -5, token_hook)
        .add_token_transfer(token_id, RECEIVER, 5)
        .add_nft_transfer_with_hook(nft_id, SENDER, RECEIVER, sender_hook, receiver_hook)
        .freeze_with(mock_client)
    )
    original_bytes = original.to_bytes()

    restored = Transaction.from_bytes(original_bytes)

    assert isinstance(restored, TransferTransaction)
    assert [t.hook_call for t in restored.hbar_transfers] == [hbar_hook, None]
    assert [t.hook_call for t in restored.token_transfers[token_id]] == [token_hook, None]
    restored_nft = restored.nft_transfers[nft_id.token_id][0]
    assert restored_nft.sender_hook_call == sender_hook
    assert restored_nft.receiver_hook_call == receiver_hook
    assert restored.to_bytes() == original_bytes


def test_transfer_models_from_proto_restore_hooks(token_id):
    hook = fungible()
    assert HbarTransfer._from_proto(HbarTransfer(SENDER, -1, hook_call=hook)._to_proto()).hook_call == hook

    nft_transfer = TokenNftTransfer(token_id, SENDER, RECEIVER, 7, sender_hook_call=nft(NftHookType.PRE_HOOK_SENDER))
    restored = TokenNftTransfer._from_nft_transfer_proto(token_id, nft_transfer._to_proto())
    assert restored.sender_hook_call == nft_transfer.sender_hook_call
    assert restored.receiver_hook_call is None


def test_str_includes_hook_only_when_set(token_id):
    assert "hook_call" not in str(HbarTransfer(SENDER, -1))
    assert "hook_call" in str(HbarTransfer(SENDER, -1, hook_call=fungible()))
    assert "hook_call" not in str(TokenTransfer(token_id, SENDER, -1))
    assert "hook_call" in str(TokenTransfer(token_id, SENDER, -1, hook_call=fungible()))
    assert "hook_call" not in str(TokenNftTransfer(token_id, SENDER, RECEIVER, 1))
    assert "receiver_hook_call" in str(
        TokenNftTransfer(token_id, SENDER, RECEIVER, 1, receiver_hook_call=nft(NftHookType.PRE_HOOK_RECEIVER))
    )


def test_frozen_transfer_rejects_hook_methods(mock_client, token_id, nft_id):
    tx = TransferTransaction().add_hbar_transfer(SENDER, -1).add_hbar_transfer(RECEIVER, 1).freeze_with(mock_client)

    with pytest.raises(Exception, match="frozen"):
        tx.add_hbar_transfer_with_hook(SENDER, -1, fungible())
    with pytest.raises(Exception, match="frozen"):
        tx.add_token_transfer_with_hook(token_id, SENDER, -1, fungible())
    with pytest.raises(Exception, match="frozen"):
        tx.add_nft_transfer_with_hook(nft_id, SENDER, RECEIVER, nft(NftHookType.PRE_HOOK_SENDER))
