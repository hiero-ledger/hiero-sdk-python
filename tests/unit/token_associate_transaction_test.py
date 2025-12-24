import pytest
from unittest.mock import MagicMock
from hiero_sdk_python.tokens.token_associate_transaction import TokenAssociateTransaction
from hiero_sdk_python.hapi.services import timestamp_pb2, token_associate_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.tokens.token_id import TokenId

pytestmark = pytest.mark.unit

def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time
    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    tx_id = TransactionId(
        valid_start=tx_timestamp,
        account_id=account_id_proto
    )
    return tx_id

# This test uses fixture mock_account_ids as parameter
def test_build_transaction_body(mock_account_ids):
    """Test building the token associate transaction body with valid account ID and token IDs."""
    account_id, _, node_account_id, token_id_1, token_id_2 = mock_account_ids
    associate_tx = TokenAssociateTransaction()

    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.add_token_id(token_id_2)
    associate_tx.transaction_id = generate_transaction_id(account_id)
    associate_tx.node_account_id = node_account_id

    transaction_body = associate_tx.build_transaction_body()

    assert transaction_body.tokenAssociate.account.shardNum == account_id.shard
    assert transaction_body.tokenAssociate.account.realmNum == account_id.realm
    assert transaction_body.tokenAssociate.account.accountNum == account_id.num
    assert len(transaction_body.tokenAssociate.tokens) == 2
    assert transaction_body.tokenAssociate.tokens[0].tokenNum == token_id_1.num
    assert transaction_body.tokenAssociate.tokens[1].tokenNum == token_id_2.num


def test_missing_fields():
    """Test that building the transaction without account ID or token IDs raises a ValueError."""
    associate_tx = TokenAssociateTransaction()

    with pytest.raises(ValueError, match="Account ID and token IDs must be set."):
        associate_tx.build_transaction_body()

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_sign_transaction(mock_account_ids, mock_client):
    """Test signing the token associate transaction with a private key."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.transaction_id = generate_transaction_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'
    
    # Freeze the transaction
    associate_tx.freeze_with(mock_client)
    
    # Sign the transaction
    associate_tx.sign(private_key)
    
    node_id = mock_client.network.current_node._account_id
    body_bytes = associate_tx._transaction_body_bytes[node_id]

    assert body_bytes in associate_tx._signature_map, "Body bytes should be a key in the signature map dictionary"
    assert len(associate_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = associate_tx._signature_map[body_bytes].sigPair[0]

    assert sig_pair.pubKeyPrefix == b'public_key'  
    assert sig_pair.ed25519 == b'signature'

# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token associate transaction to protobuf format after signing."""
    account_id, _, _, token_id_1, _ = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.transaction_id = generate_transaction_id(account_id)

    private_key = MagicMock()
    private_key.sign.return_value = b'signature'
    private_key.public_key().to_bytes_raw.return_value = b'public_key'

    associate_tx.freeze_with(mock_client)

    associate_tx.sign(private_key)
    proto = associate_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
    
def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token associate transaction."""
    account_id, _, _, token_id_1, token_id_2 = mock_account_ids
    
    associate_tx = TokenAssociateTransaction()
    associate_tx.set_account_id(account_id)
    associate_tx.add_token_id(token_id_1)
    associate_tx.add_token_id(token_id_2)
    
    schedulable_body = associate_tx.build_scheduled_body()
    
    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenAssociate")
    assert schedulable_body.tokenAssociate.account == account_id._to_proto()
    assert len(schedulable_body.tokenAssociate.tokens) == 2
    assert schedulable_body.tokenAssociate.tokens[0] == token_id_1._to_proto()
    assert schedulable_body.tokenAssociate.tokens[1] == token_id_2._to_proto()

# This test uses fixture mock_account_ids as parameter
def test_set_token_ids_accepts_tokenid_and_string(mock_account_ids):
    """
    set_token_ids should accept a list containing both TokenId instances
    and string representations, normalizing everything to TokenId.
    """
    account_id, _, _, token_id_1, _ = mock_account_ids

    associate_tx = TokenAssociateTransaction().set_account_id(account_id)

    associate_tx.set_token_ids([token_id_1, "0.0.1234"])

    assert len(associate_tx.token_ids) == 2
    assert isinstance(associate_tx.token_ids[0], TokenId)
    assert isinstance(associate_tx.token_ids[1], TokenId)

    # The first element should be exactly the same TokenId instance passed in
    assert associate_tx.token_ids[0] is token_id_1

    # The second element should be parsed from the string "0.0.1234"
    assert associate_tx.token_ids[1].shard == 0
    assert associate_tx.token_ids[1].realm == 0
    assert associate_tx.token_ids[1].num == 1234

def test_set_token_ids_invalid_type_raises():
    """
    set_token_ids should raise ValueError if any element is neither TokenId nor str.
    """
    associate_tx = TokenAssociateTransaction()

    with pytest.raises(TypeError, match="Invalid token_id type:"):
        associate_tx.set_token_ids([123])  # int is not allowed

def test_set_token_ids_non_iterable_raises_typeerror():
    """
    set_token_ids should raise a TypeError if called with a non-iterable,
    e.g. a single integer instead of a list.
    This happens naturally when Python attempts to iterate over the value.
    """
    associate_tx = TokenAssociateTransaction()

    with pytest.raises(TypeError):
        associate_tx.set_token_ids(123)

def test_validate_checksums_calls_validate_on_ids():
    associate_tx = TokenAssociateTransaction()

    account_id_mock = MagicMock()
    token_id_1 = MagicMock()
    token_id_2 = MagicMock()
    client = MagicMock()

    associate_tx.account_id = account_id_mock
    associate_tx.token_ids = [token_id_1, token_id_2]

    associate_tx._validate_checksums(client)

    account_id_mock.validate_checksum.assert_called_once_with(client)
    token_id_1.validate_checksum.assert_called_once_with(client)
    token_id_2.validate_checksum.assert_called_once_with(client)

# This test uses fixture mock_account_ids as parameter
def test_from_proto_builds_transaction(mock_account_ids):
    """
    _from_proto should rebuild a TokenAssociateTransaction instance
    from a TokenAssociateTransactionBody protobuf.
    """
    account_id, _, _, token_id_1, token_id_2 = mock_account_ids

    body = token_associate_pb2.TokenAssociateTransactionBody(
        account=account_id._to_proto(),
        tokens=[token_id_1._to_proto(), token_id_2._to_proto()],
    )

    tx = TokenAssociateTransaction._from_proto(body)

    assert tx.account_id == account_id
    assert len(tx.token_ids) == 2
    assert tx.token_ids[0] == token_id_1
    assert tx.token_ids[1] == token_id_2

