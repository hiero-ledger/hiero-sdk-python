import pytest

from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.crypto.private_key import PrivateKey

from hiero_sdk_python.account.account_update_transaction import AccountUpdateTransaction
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.tokens.token_airdrop_transaction import TokenAirdropTransaction
from hiero_sdk_python.tokens.token_transfer import TokenTransfer
from hiero_sdk_python.tokens.token_airdrop_pending_id import PendingAirdropId
from hiero_sdk_python.tokens.token_airdrop_claim import TokenClaimAirdropTransaction
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery

from tests.integration.utils_for_test import (
    IntegrationTestEnv,
    create_fungible_token,
)

pytestmark = pytest.mark.integration


# ---------- Helpers ---------- #

def set_receiver_signature_required(
    env: IntegrationTestEnv,
    account_id: AccountId,
    account_key: PrivateKey,
    required: bool,
):
    """Flip the receiverSignatureRequired flag for an account."""
    receipt_update_signature = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_receiver_signature_required(required)
        .freeze_with(env.client)
        .sign(account_key)
        .execute(env.client)
    )
    assert receipt_update_signature.status == ResponseCode.SUCCESS, f"Account update failed: {receipt_update_signature.status}"


def associate_token_to_account(
    env: IntegrationTestEnv,
    account_id: AccountId,
    account_key: PrivateKey,
    token_id: TokenId,
):
    """Associate a token to an account."""
    associate_receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(env.client)
        .sign(account_key)
        .execute(env.client)
    )
    assert associate_receipt.status == ResponseCode.SUCCESS, f"Association failed: {associate_receipt.status}"


def submit_airdrop_and_get_record(
    env: IntegrationTestEnv,
    receiver_id: AccountId,
    fungible_token_id: TokenId,
    amount: int = 1,
):
    """
    Submit a TokenAirdropTransaction for a single fungible transfer and return a TransactionRecord.
    """
    airdrop_receipt = (
        TokenAirdropTransaction(
            token_transfers=[
                TokenTransfer(fungible_token_id, env.operator_id, -amount),
                TokenTransfer(fungible_token_id, receiver_id, amount),
            ]
        )
        .freeze_with(env.client)
        .sign(env.operator_key)
        .execute(env.client)
    )
    assert airdrop_receipt.status == ResponseCode.SUCCESS, f"Airdrop failed: {airdrop_receipt.status}"
    record = TransactionRecordQuery(airdrop_receipt.transaction_id).execute(env.client)
    assert record is not None, "Expected a TransactionRecord instance"
    return record


def record_has_immediate_credit(record, token_id, account_id, amount=1) -> bool:
    """Check if the record shows an immediate token credit to the receiver."""
    token_map = record.token_transfers.get(token_id, {})
    return token_map.get(account_id, 0) == amount


def record_has_new_pending_airdrops(record) -> bool:
    """Check if the record shows newly created pending airdrops."""
    return bool(record.new_pending_airdrops)


# =====================================================================================
# Scenario A:
# receiverSignatureRequired = False (or None) AND the token is already associated
# => immediate airdrop (NO claim).
# =====================================================================================

def test_immediate_airdrop_when_already_associated_and_no_receiver_sig_required(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    # Explicitly ensure receiver account has receiverSigRequired=False for clarity
    set_receiver_signature_required(env, receiver.id, receiver.key, required=False)

    # Associate the token
    associate_token_to_account(env, receiver.id, receiver.key, token_id)

    # Submit airdrop
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)

    # Assert: no pending; immediate credit shown in token_transfers
    assert not record_has_new_pending_airdrops(record), "Expected no pending airdrops"
    assert record_has_immediate_credit(record, token_id, receiver.id, amount=1), \
        "Expected +1 token credit to receiver in the record"


# =====================================================================================
# Scenario B:
# receiverSignatureRequired = False (or None), token is NOT associated, and (effectively as we don't have this functionality yet) no auto-association slots
# => pending airdrop MUST be created (claim required).
# =====================================================================================

def test_pending_airdrop_created_when_unassociated_and_no_receiver_sig_required(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    set_receiver_signature_required(env, receiver.id, receiver.key, required=False)

    record = submit_airdrop_and_get_record(env, receiver.id, token_id)

    # Assert: pending present; no immediate credit
    assert record_has_new_pending_airdrops(record), "Expected a pending airdrop"
    assert not record_has_immediate_credit(record, token_id, receiver.id, amount=1), \
        "Receiver should not be credited until claim"

# =====================================================================================
# Scenario C:
# receiverSignatureRequired = True — MUST claim even if associated.
# =====================================================================================

def test_pending_airdrop_created_when_receiver_sig_required_even_if_associated(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    set_receiver_signature_required(env, receiver.id, receiver.key, required=True)
    associate_token_to_account(env, receiver.id, receiver.key, token_id)

    record = submit_airdrop_and_get_record(env, receiver.id, token_id)

    # Assert: pending present; no immediate credit
    assert record_has_new_pending_airdrops(record), "Expected pending when receiverSigRequired=True"
    assert not record_has_immediate_credit(record, token_id, receiver.id, amount=1), \
        "Receiver should not be credited until claim (sig required)"


# =====================================================================================
# Scenario D:
# receiverSignatureRequired = True and unassociated — MUST claim.
# =====================================================================================

def test_pending_airdrop_created_when_receiver_sig_required_and_unassociated(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    set_receiver_signature_required(env, receiver.id, receiver.key, required=True)

    record = submit_airdrop_and_get_record(env, receiver.id, token_id)

    # Assert
    assert record_has_new_pending_airdrops(record), "Expected pending when receiverSigRequired=True and unassociated"
    assert not record_has_immediate_credit(record, token_id, receiver.id, amount=1), \
        "Receiver should not be credited until claim (sig required)"

def assert_transfer_pair(record, token_id, receiver_id, operator_id, amount=1):
    tm = record.token_transfers[token_id]
    assert tm[receiver_id] == amount
    assert tm[operator_id] == -amount

def claim_with_receiver_signature(env: IntegrationTestEnv, pending_ids, receiver_key):
    """
    Build, sign (receiver), and execute a TokenClaimAirdropTransaction for the given IDs.
    Returns the receipt.
    """
    claim_tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_ids)
    receiver_account = pending_ids[0].receiver

    claim_tx.freeze_with(env.client)
    claim_tx.sign(receiver_key)
    receipt = claim_tx.execute(env.client)
    return receipt

def extract_pending_ids_from_record(record):
    """
    Convert record.new_pending_airdrops entries into PendingAirdropId objects. d d
    """
    pending_ids = []
    for item in record.new_pending_airdrops:
        pid_proto = getattr(item, "pending_airdrop_id", None)
        if pid_proto is None and hasattr(item, "_to_proto"):
            pid_proto = item._to_proto().pending_airdrop_id
        if pid_proto is None:
            raise AssertionError("Could not extract pending_airdrop_id from record item")
        pending_ids.append(PendingAirdropId._from_proto(pid_proto))  # pylint: disable=protected-access
    return pending_ids

def test_claim_fungible_pending_succeeds_and_credits_receiver(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    # Create a pending airdrop
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    assert record_has_new_pending_airdrops(record)

    # Extract IDs and claim
    pending_ids = extract_pending_ids_from_record(record)
    receipt = claim_with_receiver_signature(env, pending_ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS

    # Optional: fetch the claim record and assert transfer is present
    claim_record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
    assert claim_record is not None
    assert record_has_immediate_credit(claim_record, token_id, receiver.id, amount=1)

def test_claim_multiple_pendings_in_single_transaction(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    # Create two separate pendings (two airdrops)
    rec1 = submit_airdrop_and_get_record(env, receiver.id, token_id)
    rec2 = submit_airdrop_and_get_record(env, receiver.id, token_id)
    ids = extract_pending_ids_from_record(rec1) + extract_pending_ids_from_record(rec2)
    assert len(ids) >= 2

    receipt = claim_with_receiver_signature(env, ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS

def test_claim_fails_without_receiver_signature(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    pending_ids = extract_pending_ids_from_record(record)

    claim_tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_ids)
    claim_tx.freeze_with(env.client)

    # Intentionally NOT signing with receiver
    with pytest.raises(Exception):
        claim_tx.execute(env.client)

def test_claim_fails_with_wrong_signer(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    pending_ids = extract_pending_ids_from_record(record)

    claim_tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_ids)
    claim_tx.freeze_with(env.client)

    # Wrong signer only (operator)
    claim_tx.sign(env.operator_key)
    with pytest.raises(Exception):
        claim_tx.execute(env.client)

def test_claim_duplicate_ids_rejected_locally(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    pid = extract_pending_ids_from_record(record)[0]

    claim_tx = TokenClaimAirdropTransaction()
    with pytest.raises(ValueError):
        claim_tx.add_pending_airdrop_ids([pid, pid])  # same ID twice

def test_cannot_claim_same_pending_twice(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    ids = extract_pending_ids_from_record(record)

    first = claim_with_receiver_signature(env, ids, receiver.key)
    assert ResponseCode(first.status) == ResponseCode.SUCCESS

    # Second attempt on same IDs must fail at node
    with pytest.raises(Exception):
        claim_with_receiver_signature(env, ids, receiver.key)

def test_claim_with_one_pending_id_succeeds(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)
    record = submit_airdrop_and_get_record(env, receiver.id, token_id)
    ids = extract_pending_ids_from_record(record)

    # Should be exactly 1
    assert len(ids) == 1

    receipt = claim_with_receiver_signature(env, ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS

def test_claim_with_max_10_pending_ids_succeeds(env: IntegrationTestEnv):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    pending_ids = []
    for _ in range(TokenClaimAirdropTransaction.MAX_IDS):
        record = submit_airdrop_and_get_record(env, receiver.id, token_id)
        pending_ids.extend(extract_pending_ids_from_record(record))

    assert len(pending_ids) == TokenClaimAirdropTransaction.MAX_IDS

    receipt = claim_with_receiver_signature(env, pending_ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS
