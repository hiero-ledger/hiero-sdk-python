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
from tests.integration.utils_for_test import env, create_fungible_token, create_nft_token

pytestmark = pytest.mark.integration

# ======================
# --- Inline Helpers ---
# ======================

def set_receiver_signature_required(env, account_id: AccountId, account_key: PrivateKey, required: bool):
    receipt = (
        AccountUpdateTransaction()
        .set_account_id(account_id)
        .set_receiver_signature_required(required)
        .freeze_with(env.client)
        .sign(account_key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Account update failed: {receipt.status}"

def associate_token(env, account_id: AccountId, account_key: PrivateKey, token_id: TokenId):
    receipt = (
        TokenAssociateTransaction()
        .set_account_id(account_id)
        .add_token_id(token_id)
        .freeze_with(env.client)
        .sign(account_key)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Association failed: {receipt.status}"

def submit_airdrop(env, receiver_id: AccountId, token_id: TokenId, amount=1):
    tx = TokenAirdropTransaction(
        token_transfers=[
            TokenTransfer(token_id, env.operator_id, -amount),
            TokenTransfer(token_id, receiver_id, amount),
        ]
    ).freeze_with(env.client).sign(env.operator_key).execute(env.client)
    assert tx.status == ResponseCode.SUCCESS, f"Airdrop failed: {tx.status}"

    record = TransactionRecordQuery(tx.transaction_id).execute(env.client)
    assert record is not None
    return record

def has_immediate_credit(record, token_id: TokenId, account_id: AccountId, amount=1):
    token_map = record.token_transfers.get(token_id, {})
    return token_map.get(account_id, 0) == amount

def has_new_pending(record):
    return bool(record.new_pending_airdrops)

def extract_pending_ids(record):
    ids = []
    for item in record.new_pending_airdrops:
        # If it's already a PendingAirdropId object, just append
        if isinstance(item, PendingAirdropId):
            ids.append(item)
        else:
            # Attempt to extract the protobuf field
            pid_proto = getattr(item, "pending_airdrop_id", None)
            if pid_proto is None and hasattr(item, "_to_proto"):
                pid_proto = item._to_proto().pending_airdrop_id

            if pid_proto is None:
                raise AssertionError(f"Cannot extract pending_airdrop_id from {type(item)}")

            ids.append(PendingAirdropId._from_proto(pid_proto))
    return ids

def claim_pending(env, pending_ids, receiver_key):
    tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(pending_ids)
    tx.freeze_with(env.client).sign(receiver_key)
    return tx.execute(env.client)

# ======================
# --- Integration Tests ---
# ======================

def test_immediate_airdrop_if_associated_and_no_sig_required(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    set_receiver_signature_required(env, receiver.id, receiver.key, False)
    associate_token(env, receiver.id, receiver.key, token_id)

    record = submit_airdrop(env, receiver.id, token_id)
    assert not has_new_pending(record)
    assert has_immediate_credit(record, token_id, receiver.id)

def test_pending_airdrop_if_unassociated_and_no_sig_required(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    set_receiver_signature_required(env, receiver.id, receiver.key, False)
    record = submit_airdrop(env, receiver.id, token_id)
    assert has_new_pending(record)
    assert not has_immediate_credit(record, token_id, receiver.id)

def test_pending_airdrop_if_sig_required_even_if_associated(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    set_receiver_signature_required(env, receiver.id, receiver.key, True)
    associate_token(env, receiver.id, receiver.key, token_id)
    record = submit_airdrop(env, receiver.id, token_id)
    assert has_new_pending(record)
    assert not has_immediate_credit(record, token_id, receiver.id)

def test_claim_fungible_pending(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    record = submit_airdrop(env, receiver.id, token_id)
    ids = extract_pending_ids(record)
    receipt = claim_pending(env, ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS

    claim_record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)
    assert has_immediate_credit(claim_record, token_id, receiver.id)

def test_claim_multiple_pendings(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    rec1 = submit_airdrop(env, receiver.id, token_id)
    rec2 = submit_airdrop(env, receiver.id, token_id)

    ids = extract_pending_ids(rec1) + extract_pending_ids(rec2)
    seen = set()
    unique_ids = []
    for pid in ids:
        key = (pid.token_id, pid.nft_id)
        if key not in seen:
            seen.add(key)
            unique_ids.append(pid)

    receipt = claim_pending(env, unique_ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS


def test_claim_fails_without_signature(env):
   receiver = env.create_account(initial_hbar=2.0)
   token_id = create_fungible_token(env)

   record = submit_airdrop(env, receiver.id, token_id)
   ids = extract_pending_ids(record)

   tx = TokenClaimAirdropTransaction().add_pending_airdrop_ids(ids).freeze_with(env.client)
   # Execute without signing
   receipt = tx.execute(env.client)

   # The status should indicate failure
   assert receipt.status != ResponseCode.SUCCESS


def test_cannot_claim_duplicate_ids(env):
    receiver = env.create_account(initial_hbar=2.0)
    token_id = create_fungible_token(env)

    record = submit_airdrop(env, receiver.id, token_id)
    pid = extract_pending_ids(record)[0]

    tx = TokenClaimAirdropTransaction()
    with pytest.raises(ValueError):
        tx.add_pending_airdrop_ids([pid, pid])

def test_cannot_claim_same_pending_twice(env):
   receiver = env.create_account(initial_hbar=2.0)
   token_id = create_fungible_token(env)

   record = submit_airdrop(env, receiver.id, token_id)
   ids = extract_pending_ids(record)

   # First claim should succeed
   first = claim_pending(env, ids, receiver.key)
   assert ResponseCode(first.status) == ResponseCode.SUCCESS

   # Second claim should fail (already claimed)
   second = claim_pending(env, ids, receiver.key)
   assert ResponseCode(second.status) != ResponseCode.SUCCESS

def test_claim_max_ids(env):
    receiver = env.create_account(initial_hbar=2.0)
    
    tokens = [create_fungible_token(env) for _ in range(TokenClaimAirdropTransaction.MAX_IDS)]
    
    pending_ids = []
    for token_id in tokens:
        record = submit_airdrop(env, receiver.id, token_id)
        pending_ids.extend(extract_pending_ids(record))
    
    assert len(pending_ids) == TokenClaimAirdropTransaction.MAX_IDS
    
    receipt = claim_pending(env, pending_ids, receiver.key)
    assert ResponseCode(receipt.status) == ResponseCode.SUCCESS
