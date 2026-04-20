from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.hapi.services import (
    timestamp_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId


pytestmark = pytest.mark.unit


def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time

    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    return TransactionId(valid_start=tx_timestamp, account_id=account_id_proto)


# This test uses fixture mock_account_ids as parameter
def test_build_nft_transaction_body_single_bytes_metadata(mock_account_ids):
    """Test that a single bytes object is converted to a single-element metadata list."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    single_metadata = b"SingleBytes"

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(single_metadata)
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()

    assert len(transaction_body.tokenMint.metadata) == 1
    assert transaction_body.tokenMint.metadata[0] == single_metadata
    assert transaction_body.tokenMint.amount == 0


# This test uses fixtures (mock_account_ids, amount) as parameters
def test_build_transaction_body_fungible(mock_account_ids, amount):
    """Test building a token mint transaction body for fungible tokens."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()

    assert transaction_body.tokenMint.token.shardNum == 1
    assert transaction_body.tokenMint.token.realmNum == 1
    assert transaction_body.tokenMint.token.tokenNum == 1
    assert transaction_body.tokenMint.amount == amount
    assert len(transaction_body.tokenMint.metadata) == 0  # No metadata for fungible tokens


# This test uses fixtures (mock_account_ids, metadata) as parameters
def test_build_transaction_body_nft(mock_account_ids, metadata):
    """Test building a token mint transaction body for NFTs."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()

    assert transaction_body.tokenMint.token.shardNum == 1
    assert transaction_body.tokenMint.token.realmNum == 1
    assert transaction_body.tokenMint.token.tokenNum == 1
    assert transaction_body.tokenMint.amount == 0
    assert transaction_body.tokenMint.metadata == metadata


def test_build_proto_body_no_token_id(mock_account_ids):
    """Test that _build_proto_body handles None token_id."""
    payer_account, _, node_account_id, _, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_amount(100)
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()
    assert transaction_body.tokenMint.amount == 100
    assert not transaction_body.tokenMint.HasField("token")


def test_build_proto_body_no_amount_no_metadata(mock_account_ids):
    """Test that _build_proto_body returns empty body when neither amount nor metadata is set."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()
    assert transaction_body.tokenMint.amount == 0
    assert len(transaction_body.tokenMint.metadata) == 0


def test_build_proto_body_metadata_bytes_in_build(mock_account_ids):
    """Test that raw bytes metadata assigned directly is converted in _build_proto_body."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.metadata = b"raw_bytes"  # bypass set_metadata to test the isinstance branch
    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id

    transaction_body = mint_tx.build_transaction_body()
    assert transaction_body.tokenMint.amount == 0
    assert transaction_body.tokenMint.metadata == [b"raw_bytes"]


# This test uses fixtures (mock_account_ids, amount, mock_client) as parameters
def test_sign_transaction_fungible(mock_account_ids, amount, mock_client):
    """Test signing the fungible token mint transaction with a supply key."""
    operator_id, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)
    mint_tx.transaction_id = generate_transaction_id(operator_id)

    # Mock a supply key
    supply_key = MagicMock()
    supply_key.sign.return_value = b"signature"
    supply_key.public_key().to_bytes_raw.return_value = b"public_key"

    mint_tx.freeze_with(mock_client)

    mint_tx.sign(supply_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = mint_tx._transaction_body_bytes[node_id]

    assert len(mint_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = mint_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


# This test uses fixtures (mock_account_ids, metadata, mock_client) as parameters
def test_sign_transaction_nft(mock_account_ids, metadata, mock_client):
    """Test signing the NFT mint transaction with a supply key."""
    operator_id, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)

    mint_tx.transaction_id = generate_transaction_id(operator_id)

    mint_tx.freeze_with(mock_client)

    supply_key = MagicMock()
    supply_key.sign.return_value = b"signature"
    supply_key.public_key().to_bytes_raw.return_value = b"public_key"
    mint_tx.sign(supply_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = mint_tx._transaction_body_bytes[node_id]

    assert len(mint_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = mint_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


# This test uses fixtures (mock_account_ids, amount, mock_client) as parameters
def test_to_proto_fungible(mock_account_ids, amount, mock_client):
    """Test converting the fungible token mint transaction to protobuf format after signing."""
    operator_id, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)
    mint_tx.transaction_id = generate_transaction_id(operator_id)

    supply_key = MagicMock()
    supply_key.sign.return_value = b"signature"
    supply_key.public_key().to_bytes_raw.return_value = b"public_key"

    mint_tx.freeze_with(mock_client)

    mint_tx.sign(supply_key)
    proto = mint_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


# This test uses fixtures (mock_account_ids, metadata, mock_client) as parameters
def test_to_proto_nft(mock_account_ids, metadata, mock_client):
    """Test converting the nft token mint transaction to protobuf format after signing."""
    operator_id, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)
    mint_tx.transaction_id = generate_transaction_id(operator_id)

    mint_tx.freeze_with(mock_client)

    supply_key = MagicMock()
    supply_key.sign.return_value = b"signature"
    supply_key.public_key().to_bytes_raw.return_value = b"public_key"
    mint_tx.sign(supply_key)

    proto = mint_tx._to_proto()
    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


def test_build_scheduled_body_fungible(mock_account_ids, amount):
    """Test building a scheduled transaction body for fungible token mint transaction."""
    _, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)

    schedulable_body = mint_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenMint")
    assert schedulable_body.tokenMint.token == token_id._to_proto()
    assert schedulable_body.tokenMint.amount == amount
    assert len(schedulable_body.tokenMint.metadata) == 0


def test_build_scheduled_body_nft(mock_account_ids, metadata):
    """Test building a scheduled transaction body for NFT token mint transaction."""
    _, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)

    schedulable_body = mint_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenMint")
    assert schedulable_body.tokenMint.token == token_id._to_proto()
    assert schedulable_body.tokenMint.amount == 0
    assert schedulable_body.tokenMint.metadata == metadata


def test_from_protobuf_fungible(mock_account_ids):
    """Test round-trip via _from_protobuf for fungible TokenMintTransaction."""
    payer_account, _, node_account_id, token_id_1, _ = mock_account_ids

    tx = TokenMintTransaction()
    tx.set_token_id(token_id_1)
    tx.set_amount(500)
    tx.transaction_id = generate_transaction_id(payer_account)
    tx.node_account_id = node_account_id

    body = tx.build_transaction_body()
    reconstructed = TokenMintTransaction._from_protobuf(body, body.SerializeToString(), None)

    assert reconstructed.token_id == token_id_1
    assert reconstructed.amount == 500


def test_from_protobuf_nft(mock_account_ids):
    """Test round-trip via _from_protobuf for NFT TokenMintTransaction."""
    payer_account, _, node_account_id, token_id_1, _ = mock_account_ids
    nft_metadata = [b"meta1", b"meta2"]

    tx = TokenMintTransaction()
    tx.set_token_id(token_id_1)
    tx.set_metadata(nft_metadata)
    tx.transaction_id = generate_transaction_id(payer_account)
    tx.node_account_id = node_account_id

    body = tx.build_transaction_body()
    reconstructed = TokenMintTransaction._from_protobuf(body, body.SerializeToString(), None)

    assert reconstructed.token_id == token_id_1
    assert list(reconstructed.metadata) == nft_metadata
