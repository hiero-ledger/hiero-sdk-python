from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.hapi.services import response_header_pb2, response_pb2, timestamp_pb2, transaction_get_receipt_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)
from hiero_sdk_python.hapi.services.token_wipe_account_pb2 import TokenWipeAccountTransactionBody
from hiero_sdk_python.hapi.services.transaction_pb2 import TransactionBody
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.token_wipe_transaction import TokenWipeTransaction
from hiero_sdk_python.transaction.transaction import Transaction
from hiero_sdk_python.transaction.transaction_id import TransactionId
from tests.unit.mock_server import mock_hedera_servers


pytestmark = pytest.mark.unit


def generate_transaction_id(account_id_proto):
    """Generate a unique transaction ID based on the account ID and the current timestamp."""
    import time

    current_time = time.time()
    timestamp_seconds = int(current_time)
    timestamp_nanos = int((current_time - timestamp_seconds) * 1e9)

    tx_timestamp = timestamp_pb2.Timestamp(seconds=timestamp_seconds, nanos=timestamp_nanos)

    return TransactionId(valid_start=tx_timestamp, account_id=account_id_proto)


def test_build_transaction_body(mock_account_ids):
    """Test building a token wipe transaction body with valid values."""
    account_id, wipe_account_id, node_account_id, token_id, _ = mock_account_ids
    amount = 1000

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_amount(amount)

    wipe_tx.transaction_id = generate_transaction_id(account_id)
    wipe_tx.set_node_account_ids([node_account_id])

    transaction_body = wipe_tx.build_transaction_body()

    assert transaction_body.tokenWipe.token.shardNum == token_id.shard
    assert transaction_body.tokenWipe.token.realmNum == token_id.realm
    assert transaction_body.tokenWipe.token.tokenNum == token_id.num

    assert transaction_body.tokenWipe.account.shardNum == wipe_account_id.shard
    assert transaction_body.tokenWipe.account.realmNum == wipe_account_id.realm
    assert transaction_body.tokenWipe.account.accountNum == wipe_account_id.num

    assert transaction_body.tokenWipe.amount == amount


# This test uses fixture mock_account_ids as parameter
def test_build_transaction_body_with_serial_numbers(mock_account_ids):
    """Test building a token wipe transaction body with serial numbers for NFTs."""
    account_id, wipe_account_id, node_account_id, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_serial(serial_numbers)

    wipe_tx.transaction_id = generate_transaction_id(account_id)
    wipe_tx.set_node_account_ids([node_account_id])

    transaction_body = wipe_tx.build_transaction_body()

    assert transaction_body.tokenWipe.token.shardNum == token_id.shard
    assert transaction_body.tokenWipe.token.realmNum == token_id.realm
    assert transaction_body.tokenWipe.token.tokenNum == token_id.num

    assert transaction_body.tokenWipe.account.shardNum == wipe_account_id.shard
    assert transaction_body.tokenWipe.account.realmNum == wipe_account_id.realm
    assert transaction_body.tokenWipe.account.accountNum == wipe_account_id.num

    assert transaction_body.tokenWipe.serialNumbers == serial_numbers


# This test uses fixture (mock_account_ids, mock_client) as parameter
def test_to_proto(mock_account_ids, mock_client):
    """Test converting the token wipe transaction to protobuf format after signing."""
    account_id, wipe_account_id, _, token_id, _ = mock_account_ids

    amount = 1000

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_amount(amount)

    wipe_tx.transaction_id = generate_transaction_id(account_id)

    wipe_key = MagicMock()
    wipe_key.sign.return_value = b"signature"
    wipe_key.public_key().to_bytes_raw.return_value = b"public_key"

    wipe_tx.freeze_with(mock_client)

    wipe_tx.sign(wipe_key)
    proto = wipe_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0


# This test uses fixture mock_account_ids as parameter
def test_constructor_with_parameters(mock_account_ids):
    """Test creating a token wipe transaction with constructor parameters."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids
    amount = 1000

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_amount(amount)

    assert wipe_tx.token_id == token_id
    assert wipe_tx.account_id == wipe_account_id
    assert wipe_tx.amount == amount


# This test uses fixture mock_account_ids as parameter
def test_constructor_with_serial_numbers(mock_account_ids):
    """Test creating a token wipe transaction with serial numbers in the constructor."""
    _, account_id, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(account_id).set_serial(serial_numbers)

    assert wipe_tx.token_id == token_id
    assert wipe_tx.account_id == account_id
    assert wipe_tx.serial == serial_numbers


# This test uses fixture mock_account_ids as parameter
def test_wipe_transaction_can_execute(mock_account_ids):
    """Test that a wipe transaction can be executed successfully."""
    _, account_id, _, token_id, _ = mock_account_ids
    amount = 1000

    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for a successful token wipe
    mock_receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(nodeTransactionPrecheckCode=ResponseCode.OK),
            receipt=mock_receipt_proto,
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        transaction = TokenWipeTransaction().set_token_id(token_id).set_account_id(account_id).set_amount(amount)

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"


def test_wipe_transaction_from_proto(mock_account_ids):
    """Test that a wipe transaction can be created from a protobuf object."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids

    # Create protobuf object with token wipe details
    proto = TokenWipeAccountTransactionBody(
        token=token_id._to_proto(), account=wipe_account_id._to_proto(), amount=1000, serialNumbers=[1, 2, 3]
    )

    # Deserialize the protobuf object
    from_proto = TokenWipeTransaction()._from_proto(proto)

    # Verify deserialized transaction matches original data
    assert from_proto.token_id == token_id
    assert from_proto.account_id == wipe_account_id
    assert from_proto.amount == 1000
    assert from_proto.serial == [1, 2, 3]

    # Deserialize empty protobuf
    from_proto = TokenWipeTransaction()._from_proto(TokenWipeAccountTransactionBody())

    # Verify empty protobuf deserializes to empty/default values
    assert from_proto.token_id == TokenId(0, 0, 0)
    assert from_proto.account_id == AccountId(0, 0, 0)
    assert from_proto.amount == 0
    assert from_proto.serial == []


def test_build_scheduled_body(mock_account_ids):
    """Test building a scheduled transaction body for token wipe transaction."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids
    amount = 1000

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_amount(amount)

    schedulable_body = wipe_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenWipe")
    assert schedulable_body.tokenWipe.token == token_id._to_proto()
    assert schedulable_body.tokenWipe.account == wipe_account_id._to_proto()
    assert schedulable_body.tokenWipe.amount == amount


def test_build_scheduled_body_with_serial_numbers(mock_account_ids):
    """Test building a scheduled transaction body for token wipe transaction with serial numbers."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]

    wipe_tx = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_serial(serial_numbers)

    schedulable_body = wipe_tx.build_scheduled_body()

    # Verify the schedulable body has the correct structure and fields
    assert isinstance(schedulable_body, SchedulableTransactionBody)
    assert schedulable_body.HasField("tokenWipe")
    assert schedulable_body.tokenWipe.token == token_id._to_proto()
    assert schedulable_body.tokenWipe.account == wipe_account_id._to_proto()
    assert schedulable_body.tokenWipe.serialNumbers == serial_numbers


def test_token_wipe_transaction_from_protobuf_fungible(mock_account_ids, amount):
    """TokenWipeTransaction should deserialize fungible wipe fields from protobuf correctly."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids

    transaction = TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_amount(amount)
    body = transaction._build_proto_body()

    transaction_body = TransactionBody()
    transaction_body.tokenWipe.CopyFrom(body)

    parsed = TokenWipeTransaction._from_protobuf(transaction_body)

    assert parsed.token_id == token_id
    assert parsed.account_id == wipe_account_id
    assert parsed.amount == amount
    assert parsed.serial == []


def test_token_wipe_transaction_from_protobuf_nft(mock_account_ids):
    """TokenWipeTransaction should deserialize NFT wipe fields from protobuf correctly."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2, 3]

    transaction = (
        TokenWipeTransaction().set_token_id(token_id).set_account_id(wipe_account_id).set_serial(serial_numbers)
    )
    body = transaction._build_proto_body()

    transaction_body = TransactionBody()
    transaction_body.tokenWipe.CopyFrom(body)

    parsed = TokenWipeTransaction._from_protobuf(transaction_body)

    assert parsed.token_id == token_id
    assert parsed.account_id == wipe_account_id
    assert parsed.serial == serial_numbers
    assert parsed.amount is None


def test_token_wipe_transaction_from_protobuf_mixed_payload(mock_account_ids):
    """TokenWipeTransaction should deserialize both amount and serials when both are present."""
    _, wipe_account_id, _, token_id, _ = mock_account_ids
    serial_numbers = [1, 2]

    transaction = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(wipe_account_id)
        .set_amount(10)
        .set_serial(serial_numbers)
    )
    body = transaction._build_proto_body()

    transaction_body = TransactionBody()
    transaction_body.tokenWipe.CopyFrom(body)

    parsed = TokenWipeTransaction._from_protobuf(transaction_body)

    assert parsed.token_id == token_id
    assert parsed.account_id == wipe_account_id
    assert parsed.amount == 10
    assert parsed.serial == serial_numbers


def test_from_bytes_round_trip_fungible(mock_account_ids, amount):
    """Test serialization round-trip via Transaction.from_bytes() for fungible tokens."""
    account_id, wipe_account_id, node_account_id, token_id, _ = mock_account_ids

    tx1 = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(wipe_account_id)
        .set_amount(amount)
        .set_transaction_id(generate_transaction_id(account_id))
        .set_node_account_ids([node_account_id])
    )
    tx1.freeze()
    data = tx1.to_bytes()
    tx2 = Transaction.from_bytes(data)

    assert isinstance(tx2, TokenWipeTransaction)
    assert tx2.token_id == token_id
    assert tx2.account_id == wipe_account_id
    assert tx2.amount == amount
    assert tx2.serial == []
    assert tx2.to_bytes() == data


def test_from_bytes_round_trip_nft(mock_account_ids):
    """Test serialization round-trip via Transaction.from_bytes() for NFT tokens."""
    account_id, wipe_account_id, node_account_id, token_id, _ = mock_account_ids
    serial_numbers = [4, 5, 6]

    tx1 = (
        TokenWipeTransaction()
        .set_token_id(token_id)
        .set_account_id(wipe_account_id)
        .set_serial(serial_numbers)
        .set_transaction_id(generate_transaction_id(account_id))
        .set_node_account_ids([node_account_id])
    )
    tx1.freeze()
    data = tx1.to_bytes()
    tx2 = Transaction.from_bytes(data)

    assert isinstance(tx2, TokenWipeTransaction)
    assert tx2.token_id == token_id
    assert tx2.account_id == wipe_account_id
    assert tx2.serial == serial_numbers
    assert tx2.amount is None
    assert tx2.to_bytes() == data


def test_from_protobuf_without_token_or_account():
    """Test _from_protobuf correctly handles absent token and account fields."""
    from hiero_sdk_python.hapi.services import token_wipe_account_pb2

    tx_body = TransactionBody()
    tx_body.tokenWipe.CopyFrom(token_wipe_account_pb2.TokenWipeAccountTransactionBody(amount=300))

    restored = TokenWipeTransaction._from_protobuf(tx_body)
    assert restored.token_id is None
    assert restored.account_id is None
    assert restored.amount == 300
    assert restored.serial == []


def test_from_protobuf_empty_body():
    """Test _from_protobuf correctly restores amount as None for an empty body."""
    from hiero_sdk_python.hapi.services import token_wipe_account_pb2

    tx_body = TransactionBody()
    tx_body.tokenWipe.CopyFrom(token_wipe_account_pb2.TokenWipeAccountTransactionBody())

    restored = TokenWipeTransaction._from_protobuf(tx_body)
    assert restored.token_id is None
    assert restored.account_id is None
    assert restored.amount is None
    assert restored.serial == []


def test_from_bytes_round_trip_unconfigured(mock_account_ids):
    """Test round-trip preserves amount is None for an unconfigured wipe transaction."""
    account_id, _, node_account_id, _, _ = mock_account_ids

    tx1 = (
        TokenWipeTransaction()
        .set_transaction_id(generate_transaction_id(account_id))
        .set_node_account_ids([node_account_id])
    )
    tx1.freeze()
    data = tx1.to_bytes()
    tx2 = Transaction.from_bytes(data)

    assert isinstance(tx2, TokenWipeTransaction)
    assert tx2.token_id is None
    assert tx2.account_id is None
    assert tx2.amount is None
    assert tx2.serial == []
    assert tx2.to_bytes() == data
