import pytest
from unittest.mock import patch

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.hapi.services import basic_types_pb2, response_pb2
from hiero_sdk_python.hapi.services.transaction_response_pb2 import TransactionResponse as TransactionResponseProto
from hiero_sdk_python.hapi.services.transaction_receipt_pb2 import TransactionReceipt as TransactionReceiptProto
from hiero_sdk_python.hapi.services import transaction_get_receipt_pb2, response_header_pb2
from hiero_sdk_python.hapi.services import file_create_pb2
from hiero_sdk_python.hapi.services.schedulable_transaction_body_pb2 import (
    SchedulableTransactionBody,
)

from tests.unit.mock_server import mock_hedera_servers

pytestmark = pytest.mark.unit

def test_constructor_with_parameters():
    """Test creating a file create transaction with constructor parameters."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    contents = b"Test file content"
    file_memo = "Test memo"

    file_tx = FileCreateTransaction(
        keys=key_list,
        contents=contents,
        file_memo=file_memo
    )

    assert file_tx.keys == key_list
    assert file_tx.contents == contents
    assert file_tx.file_memo == file_memo
    assert file_tx.expiration_time is not None  # Should have default expiration
    assert file_tx._default_transaction_fee == Hbar(5).to_tinybars()

def test_constructor_default_expiration_time():
    """Test that constructor sets expiration time to exactly time.time() + DEFAULT_EXPIRY_SECONDS."""
    fixed_time = 1640995200  # Fixed timestamp: Jan 1, 2022
    
    with patch('time.time', return_value=fixed_time):
        file_tx = FileCreateTransaction()
        
        expected_expiration = Timestamp(fixed_time + FileCreateTransaction.DEFAULT_EXPIRY_SECONDS, 0)
        assert file_tx.expiration_time == expected_expiration

def test_constructor_with_custom_expiration_time():
    """Test that constructor uses provided expiration time instead of default."""
    custom_expiration = Timestamp(1704067200, 0)  # Jan 1, 2024
    
    with patch('time.time', return_value=1640995200):
        file_tx = FileCreateTransaction(expiration_time=custom_expiration)
        
        assert file_tx.expiration_time == custom_expiration

def test_build_transaction_body(mock_account_ids):
    """Test building a file create transaction body with valid values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    
    file_tx = FileCreateTransaction(
        keys=key_list,
        contents=b"Test content",
        file_memo="Test memo"
    )

    # Set operator and node account IDs needed for building transaction body
    file_tx.operator_account_id = operator_id
    file_tx.node_account_id = node_account_id
    
    transaction_body = file_tx.build_transaction_body()

    expected_keys = basic_types_pb2.KeyList(keys=[key._to_proto() for key in key_list])
    assert transaction_body.fileCreate.keys == expected_keys
    assert transaction_body.fileCreate.contents == b"Test content"
    assert transaction_body.fileCreate.memo == "Test memo"

def test_build_scheduled_body(mock_account_ids):
    """Test building a schedulable file create transaction body with valid values."""
    operator_id, _, node_account_id, _, _ = mock_account_ids

    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]

    file_tx = FileCreateTransaction(
        keys=key_list,
        contents=b"Test schedulable content",
        file_memo="Test schedulable memo"
    )

    # Set operator and node account IDs needed for building transaction body
    file_tx.operator_account_id = operator_id
    file_tx.node_account_id = node_account_id

    schedulable_body = file_tx.build_scheduled_body()

    # Verify correct return type
    assert isinstance(schedulable_body, SchedulableTransactionBody)

    # Verify fields in the schedulable body
    expected_keys = basic_types_pb2.KeyList(keys=[key._to_proto() for key in key_list])
    assert schedulable_body.fileCreate.keys == expected_keys
    assert schedulable_body.fileCreate.contents == b"Test schedulable content"
    assert schedulable_body.fileCreate.memo == "Test schedulable memo"

def test_set_methods():
    """Test the set methods of FileCreateTransaction."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]
    contents = b"Test content"
    file_memo = "Test memo"
    expiration_time = Timestamp(1704067200, 0)  # Jan 1, 2024

    file_tx = FileCreateTransaction()

    test_cases = [
        ('set_keys', key_list, 'keys'),
        ('set_contents', contents, 'contents'),
        ('set_file_memo', file_memo, 'file_memo'),
        ('set_expiration_time', expiration_time, 'expiration_time')
    ]

    for method_name, value, attr_name in test_cases:
        tx_after_set = getattr(file_tx, method_name)(value)
        assert tx_after_set is file_tx
        assert getattr(file_tx, attr_name) == value

def test_set_keys_variations():
    """Test setting keys with different input types."""
    file_tx = FileCreateTransaction()
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

def test_set_methods_require_not_frozen(mock_client):
    """Test that set methods raise exception when transaction is frozen."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    
    file_tx = FileCreateTransaction(
        keys=[public_key],
        contents=b"test content"
    )
    file_tx.freeze_with(mock_client)

    test_cases = [
        ('set_keys', [public_key]),
        ('set_contents', b"new content"),
        ('set_file_memo', "new memo"),
        ('set_expiration_time', Timestamp(1704067200, 0))
    ]

    for method_name, value in test_cases:
        with pytest.raises(Exception, match="Transaction is immutable; it has been frozen"):
            getattr(file_tx, method_name)(value)

def test_file_create_transaction_can_execute():
    """Test that a file create transaction can be executed successfully."""
    # Create test transaction responses
    ok_response = TransactionResponseProto()
    ok_response.nodeTransactionPrecheckCode = ResponseCode.OK

    # Create a mock receipt for successful file creation
    mock_receipt_proto = TransactionReceiptProto(
        status=ResponseCode.SUCCESS,
        fileID=basic_types_pb2.FileID(
            shardNum=0,
            realmNum=0,
            fileNum=5678
        )
    )

    # Create a response for the receipt query
    receipt_query_response = response_pb2.Response(
        transactionGetReceipt=transaction_get_receipt_pb2.TransactionGetReceiptResponse(
            header=response_header_pb2.ResponseHeader(
                nodeTransactionPrecheckCode=ResponseCode.OK
            ),
            receipt=mock_receipt_proto
        )
    )

    response_sequences = [
        [ok_response, receipt_query_response],
    ]

    with mock_hedera_servers(response_sequences) as client:
        test_key = PrivateKey.generate().public_key()
        
        transaction = (
            FileCreateTransaction()
            .set_keys(test_key)
            .set_contents(b"Integration test content")
            .set_file_memo("Integration test file")
        )

        receipt = transaction.execute(client)

        assert receipt.status == ResponseCode.SUCCESS, "Transaction should have succeeded"
        assert receipt.file_id.file == 5678

def test_file_create_transaction_from_proto():
    """Test that a file create transaction can be created from a protobuf object."""
    private_key = PrivateKey.generate()
    public_key = private_key.public_key()
    key_list = [public_key]

    # Create protobuf object with file create details
    proto = file_create_pb2.FileCreateTransactionBody(
        keys=basic_types_pb2.KeyList(keys=[key._to_proto() for key in key_list]),
        contents=b"Proto test content",
        memo="Proto test memo"
    )
    
    # Deserialize the protobuf object
    from_proto = FileCreateTransaction()._from_proto(proto)
    
    # Verify deserialized transaction matches original data
    assert from_proto.contents == b"Proto test content"
    assert from_proto.file_memo == "Proto test memo"
    assert len(from_proto.keys) == 1
    assert isinstance(from_proto.keys[0], PublicKey)
    
    # Deserialize empty protobuf
    from_proto = FileCreateTransaction()._from_proto(file_create_pb2.FileCreateTransactionBody())
    
    # Verify empty protobuf deserializes to empty/default values
    assert from_proto.contents == b""
    assert from_proto.file_memo == ""
    assert from_proto.keys == [] 