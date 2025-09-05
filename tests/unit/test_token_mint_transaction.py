from unittest.mock import MagicMock

import pytest
from cryptography.hazmat.primitives import serialization

from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    timestamp_pb2,
    token_mint_pb2,
    transaction_pb2,
)
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_mint_transaction import TokenMintTransaction
from hiero_sdk_python.transaction.transaction_id import TransactionId

pytestmark = pytest.mark.unit


def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time

    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(
        seconds=timestamp_seconds, nanos=timestamp_nanos
    )

    tx_id = TransactionId(valid_start=tx_timestamp, account_id=account_id_proto)
    return tx_id


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
    assert (
        len(transaction_body.tokenMint.metadata) == 0
    )  # No metadata for fungible tokens


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


# This test uses fixtures (mock_account_ids, amount) as parameters
@pytest.mark.parametrize("amount", [0, -1, -1000])
def test_build_fungible_transaction_body_invalid_amount(mock_account_ids, amount):
    _, _, _, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)
    with pytest.raises(ValueError, match="Amount to mint must be positive."):
        mint_tx.build_transaction_body()


# This test uses fixture amount as parameter
def test_build_fungible_transaction_body_missing_token_id(amount):
    """Test that missing token_id raises a ValueError for fungible token mint."""
    mint_tx = TokenMintTransaction()
    mint_tx.set_amount(amount)
    with pytest.raises(ValueError, match="Token ID is required for minting."):
        mint_tx.build_transaction_body()


# This test uses fixture metadata as parameter
def test_build_nft_transaction_body_missing_token_id(metadata):
    """Test that missing token_id raises a ValueError for nft mint."""
    mint_tx = TokenMintTransaction()
    mint_tx.set_metadata(metadata)
    with pytest.raises(ValueError, match="Token ID is required for minting."):
        mint_tx.build_transaction_body()


# This test uses fixture mock_account_ids as parameter
def test_build_nft_transaction_body_invalid_metadata_type(mock_account_ids):
    """Test that invalid metadata type raises a ValueError."""
    _, _, _, token_id, _ = mock_account_ids
    metadata = "invalid_metadata"  # Should be a list of bytes

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)
    with pytest.raises(
        ValueError, match="Metadata must be a list of byte arrays for NFTs."
    ):
        mint_tx.build_transaction_body()


# This test uses fixture mock_account_ids as parameter
def test_build_nft_transaction_body_empty_metadata(mock_account_ids):
    """Test that empty metadata list with no fungible mint amount raises a ValueError."""
    _, _, _, token_id, _ = mock_account_ids
    metadata = []  # Should be a list of bytes

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_metadata(metadata)
    with pytest.raises(ValueError, match="Metadata list cannot be empty for NFTs."):
        mint_tx.build_transaction_body()


# This test uses fixtures (mock_account_ids, amount, metadata) as parameters
def test_build_transaction_body_both_amount_and_metadata(
    mock_account_ids, amount, metadata
):
    """Test that setting both amount and metadata raises a ValueError."""
    payer_account, _, node_account_id, token_id, _ = mock_account_ids

    mint_tx = TokenMintTransaction()
    mint_tx.set_token_id(token_id)
    mint_tx.set_amount(amount)
    mint_tx.set_metadata(metadata)

    mint_tx.transaction_id = generate_transaction_id(payer_account)
    mint_tx.node_account_id = node_account_id
    with pytest.raises(
        ValueError,
        match="Specify either amount for fungible tokens or metadata for NFTs, not both.",
    ):
        mint_tx.build_transaction_body()


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
