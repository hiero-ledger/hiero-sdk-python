"""
Test cases for the FileUpdateTransaction class.
"""

from unittest.mock import MagicMock

import pytest

# pylint: disable=no-name-in-module
from google.protobuf.wrappers_pb2 import StringValue

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.hapi.services import (
    basic_types_pb2,
    transaction_get_receipt_pb2,
)

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.timestamp import Timestamp

pytestmark = pytest.mark.unit


def test_constructor_with_parameters(file_id):
    """Test creating a file update transaction with constructor parameters."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    contents = b"Updated file content"
    file_memo = "Updated memo"
    expiration_time = Timestamp(1704067200, 0)

    file_tx = FileUpdateTransaction(
        file_id=file_id,
        keys=key_list,
        contents=contents,
        expiration_time=expiration_time,
        file_memo=file_memo,
    )

    assert file_tx.file_id == file_id
    assert file_tx.keys == key_list
    assert file_tx.contents == contents
    assert file_tx.expiration_time == expiration_time
    assert file_tx.file_memo == file_memo
    assert file_tx._default_transaction_fee == Hbar(2).to_tinybars()


def test_constructor_without_parameters():
    """Test creating a file update transaction without parameters."""
    file_tx = FileUpdateTransaction()

    assert file_tx.file_id is None
    assert file_tx.keys is None
    assert file_tx.contents is None
    assert file_tx.expiration_time is None
    assert file_tx.file_memo is None
    assert file_tx._default_transaction_fee == Hbar(2).to_tinybars()


def test_set_methods():
    """Test the set methods of FileUpdateTransaction."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    contents = b"Test content"
    file_memo = "Test memo"
    expiration_time = Timestamp(1704067200, 0)  # Jan 1, 2024

    file_tx = FileUpdateTransaction()

    test_cases = [
        ("set_keys", key_list, "keys"),
        ("set_contents", contents, "contents"),
        ("set_file_memo", file_memo, "file_memo"),
        ("set_expiration_time", expiration_time, "expiration_time"),
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(file_tx, method_name)(value)
        assert tx_after_set is file_tx
        assert getattr(file_tx, attr_name) == value


def test_set_keys_variations():
    """Test setting keys with different input types."""
    file_tx = FileUpdateTransaction()
    private_key1 = PrivateKey.generate()
    private_key2 = PrivateKey.generate()
    public_key1 = private_key1.public_key()
    public_key2 = private_key2.public_key()

    # Test with single PublicKey
    file_tx.set_keys(public_key1)
    assert isinstance(file_tx.keys, list)
    assert len(file_tx.keys) == 1
    assert file_tx.keys[0] == public_key1

    # Test with list of PublicKeys
    file_tx.set_keys([public_key1, public_key2])
    assert isinstance(file_tx.keys, list)
    assert len(file_tx.keys) == 2

    # Test with KeyList
    key_list = [public_key1]
    file_tx.set_keys(key_list)
    assert file_tx.keys is key_list


def test_set_methods_require_not_frozen(mock_client, file_id):
    """Test that set methods raise exception when transaction is frozen."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()

    file_tx = FileUpdateTransaction(file_id=file_id)
    file_tx.freeze_with(mock_client)

    test_cases = [
        ("set_file_id", FileId(0, 0, 999)),
        ("set_keys", [public_key]),
        ("set_contents", b"new content"),
        ("set_file_memo", "new memo"),
        ("set_expiration_time", Timestamp(1704067200, 0)),
    ]

    for method_name, value in test_cases:
        with pytest.raises(
            Exception, match="Transaction is immutable; it has been frozen"
        ):
            getattr(file_tx, method_name)(value)


def test_build_transaction_body(mock_account_ids, file_id):
    """Test building a file update transaction body with valid values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    contents = b"Updated content"
    file_memo = "Updated memo"
    expiration_time = Timestamp(1704067200, 0)

    file_tx = FileUpdateTransaction(
        file_id=file_id,
        keys=key_list,
        contents=contents,
        expiration_time=expiration_time,
        file_memo=file_memo,
    )

    # Set operator and node account IDs needed for building transaction body
    file_tx.operator_account_id = operator_id
    file_tx.node_account_id = node_account_id

    transaction_body = file_tx.build_transaction_body()

    assert transaction_body.fileUpdate.fileID == file_id._to_proto()
    expected_keys = basic_types_pb2.KeyList(keys=[key._to_proto() for key in key_list])
    assert transaction_body.fileUpdate.keys == expected_keys
    assert transaction_body.fileUpdate.contents == contents
    assert transaction_body.fileUpdate.expirationTime == expiration_time._to_protobuf()
    assert transaction_body.fileUpdate.memo == StringValue(value=file_memo)


def test_build_transaction_body_with_optional_fields(mock_account_ids, file_id):
    """Test building transaction body with some optional fields set to None."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    file_tx = FileUpdateTransaction(file_id=file_id)
    file_tx.operator_account_id = operator_id
    file_tx.node_account_id = node_account_id

    transaction_body = file_tx.build_transaction_body()

    assert transaction_body.fileUpdate.fileID == file_id._to_proto()
    # When keys is None, the keys field should not be set in the protobuf
    assert not transaction_body.fileUpdate.HasField("keys")
    # When contents is None, the contents field should be empty bytes
    assert transaction_body.fileUpdate.contents == b""
    # When expiration_time is None, the expirationTime field should not be set in the protobuf
    assert not transaction_body.fileUpdate.HasField("expirationTime")
    # When file_memo is None, the memo field should not be set in the protobuf
    assert not transaction_body.fileUpdate.HasField("memo")


def test_missing_file_id():
    """Test that building a transaction without setting file_id raises a ValueError."""
    file_tx = FileUpdateTransaction()

    with pytest.raises(ValueError, match="Missing required FileID"):
        file_tx.build_transaction_body()


def test_sign_transaction(mock_client, file_id):
    """Test signing the file update transaction with a private key."""
    file_tx = FileUpdateTransaction(file_id=file_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    file_tx.freeze_with(mock_client)

    file_tx.sign(private_key)

    node_id = mock_client.network.current_node._account_id
    body_bytes = file_tx._transaction_body_bytes[node_id]

    assert len(file_tx._signature_map[body_bytes].sigPair) == 1
    sig_pair = file_tx._signature_map[body_bytes].sigPair[0]
    assert sig_pair.pubKeyPrefix == b"public_key"
    assert sig_pair.ed25519 == b"signature"


def test_to_proto(mock_client, file_id):
    """Test converting the file update transaction to protobuf format after signing."""
    file_tx = FileUpdateTransaction(file_id=file_id)

    private_key = MagicMock()
    private_key.sign.return_value = b"signature"
    private_key.public_key().to_bytes_raw.return_value = b"public_key"

    file_tx.freeze_with(mock_client)

    file_tx.sign(private_key)
    proto = file_tx._to_proto()

    assert proto.signedTransactionBytes
    assert len(proto.signedTransactionBytes) > 0
def test_file_update_transaction_can_execute(file_id):
    """Test that a file update transaction can be executed successfully."""
    from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
    from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
    from hiero_sdk_python.hapi.services import response_pb2, response_header_pb2
    from hiero_sdk_python.response_code import ResponseCode

    # Create mock responses
    ok_response = TransactionResponseProto(nodeTransactionPrecheckCode=ResponseCode.OK)
    receipt_proto = TransactionReceiptProto(status=ResponseCode.SUCCESS)
    receipt_query_response = response_pb2.Response(
            transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=receipt_proto,
        )
    )

    response_sequences = [[ok_response, receipt_query_response]]

    from tests.unit.mock_server import mock_hedera_servers
    from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
    from hiero_sdk_python.crypto.private_key import PrivateKey

    with mock_hedera_servers(response_sequences) as client:
        private_key = PrivateKey.generate()
        public_key = private_key.public_key()

        transaction = (
            FileUpdateTransaction()
            .set_file_id(file_id)
            .set_keys([public_key])
            .set_contents(b"Updated file content")
            .set_file_memo("Updated memo")
        )

        receipt = transaction.execute(client)

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), "Transaction should have succeeded"


def test_get_method():
    """Test retrieving the gRPC method for the transaction."""
    file_tx = FileUpdateTransaction()

    mock_channel = MagicMock()
    mock_file_stub = MagicMock()
    mock_channel.file = mock_file_stub

    method = file_tx._get_method(mock_channel)

    assert method.query is None
    assert method.transaction == mock_file_stub.updateFile


def test_encode_contents_string():
    """Test encoding string contents to bytes."""
    file_tx = FileUpdateTransaction()

    # Test string encoding
    string_content = "Hello, World!"
    encoded = file_tx._encode_contents(string_content)
    assert encoded == b"Hello, World!"

    # Test bytes pass-through
    bytes_content = b"Hello, bytes!"
    encoded = file_tx._encode_contents(bytes_content)
    assert encoded == bytes_content

    # Test None handling
    encoded = file_tx._encode_contents(None)
    assert encoded is None
