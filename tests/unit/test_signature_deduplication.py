from __future__ import annotations

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


def test_duplicate_signature_not_added():
    tx = TokenMintTransaction()

    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))

    key = PrivateKey.generate_ed25519()

    tx.freeze()

    tx.sign(key)
    tx.sign(key)

    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair

    assert len(sig_pairs) == 1, "Expected 1 signature for duplicate key"


def test_multiple_keys_still_work():
    tx = TokenMintTransaction()

    tx.set_transaction_id(TransactionId.generate(AccountId(0, 0, 1234)))
    tx.set_node_account_id(AccountId(0, 0, 3))

    key1 = PrivateKey.generate_ed25519()
    key2 = PrivateKey.generate_ed25519()

    tx.freeze()

    tx.sign(key1)
    tx.sign(key2)

    body_bytes = next(iter(tx._signature_map.keys()))
    sig_pairs = tx._signature_map[body_bytes].sigPair

    assert len(sig_pairs) == 2, "Expected 2 signatures for different keys"

    pubkey_prefixes = {sp.pubKeyPrefix for sp in sig_pairs}
    expected_prefixes = {
        key1.public_key().to_bytes(),
        key2.public_key().to_bytes(),
    }

    assert pubkey_prefixes == expected_prefixes, "Signatures should match key1 and key2 exactly"
