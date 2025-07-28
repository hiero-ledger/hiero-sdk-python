import pytest
from pytest import mark

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.exceptions import PrecheckError
from tests.integration.utils_for_test import env, IntegrationTestEnv

# Generate big contents for chunking tests - similar to JavaScript bigContents
BIG_CONTENTS = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 250  # ~13,750 characters

def generate_uint8_array(length: int) -> bytes:
    """Generate a byte array of specified length filled with repeating pattern."""
    return bytes([1] * length)

@mark.integration
def test_integration_file_append_transaction_can_execute(env):
    """Test basic file append functionality."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"[e2e::FileCreateTransaction]")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    assert create_receipt.fileId is not None
    assert create_receipt.fileId.file > 0

    file_id = create_receipt.fileId

    # Append to the file
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(b"[e2e::FileAppendTransaction]")
        .execute(env.client)
    )
    
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append file failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_chunk_contents(env):
    """Test file append with large content that requires chunking."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"[e2e::FileCreateTransaction]")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    assert create_receipt.fileId is not None
    assert create_receipt.fileId.file > 0

    file_id = create_receipt.fileId

    # Append large content that will be chunked
    big_contents_bytes = BIG_CONTENTS.encode('utf-8')
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(big_contents_bytes)
        .execute(env.client)
    )
    
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append large file failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_error_no_file_id(env):
    """Test that FileAppendTransaction errors when no file ID is set."""
    # Try to append without setting a file ID
    try:
        append_receipt = (
            FileAppendTransaction()
            .set_contents(b"[e2e::FileAppendTransaction]")
            .execute(env.client)
        )
        # If we get here, the test should fail
        assert False, "File append transaction should have failed with no file ID"
    except Exception as error:
        # Verify that the error contains the expected status
        error_str = str(error)
        assert "INVALID_FILE_ID" in error_str or "InvalidFileId" in error_str

@mark.integration 
def test_integration_file_append_transaction_no_contents(env):
    """Test that FileAppendTransaction does not error with no contents appended."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"[e2e::FileCreateTransaction]")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    assert create_receipt.fileId is not None

    file_id = create_receipt.fileId

    # Append with no contents - this should not error
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .execute(env.client)
    )
    
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append with no contents failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_one_chunk(env):
    """Test file append with content that fits in one chunk."""
    CHUNK_SIZE = 4096
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    assert create_receipt.fileId is not None
    assert create_receipt.fileId.file > 0

    file_id = create_receipt.fileId

    # Append content that exactly fits one chunk
    test_content = generate_uint8_array(CHUNK_SIZE)
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(test_content)
        .set_chunk_size(CHUNK_SIZE)
        .execute(env.client)
    )
    
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append one chunk failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_multiple_chunks(env):
    """Test file append with content that requires multiple chunks."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    assert create_receipt.fileId is not None

    file_id = create_receipt.fileId

    # Create content larger than default chunk size to force multiple chunks
    large_content = generate_uint8_array(10000)  # 10KB content
    
    file_append_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(large_content)
        .set_chunk_size(1024)  # 1KB chunks = should require ~10 chunks
    )
    
    # Verify it calculates the correct number of chunks
    required_chunks = file_append_tx.get_required_chunks()
    assert required_chunks > 1, f"Expected multiple chunks, got {required_chunks}"
    
    append_receipt = file_append_tx.execute(env.client)
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append multiple chunks failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_custom_chunk_settings(env):
    """Test file append with custom chunk size and interval settings."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    file_id = create_receipt.fileId

    # Test with custom chunk settings
    test_content = generate_uint8_array(5000)  # 5KB content
    
    append_tx = (
        FileAppendTransaction()
        .set_file_id(file_id) 
        .set_contents(test_content)
        .set_chunk_size(1000)  # 1KB chunks
        .set_max_chunks(10)  # Max 10 chunks
    )
    
    # Verify settings are applied
    assert append_tx.chunk_size == 1000
    assert append_tx.max_chunks == 10
    
    # Should require 5 chunks (5000 bytes / 1000 bytes per chunk)
    required_chunks = append_tx.get_required_chunks()
    assert required_chunks == 5, f"Expected 5 chunks, got {required_chunks}"
    
    append_receipt = append_tx.execute(env.client)
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append with custom settings failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_max_chunks_exceeded(env):
    """Test that FileAppendTransaction fails when max chunks is exceeded."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS
    file_id = create_receipt.fileId

    # Create content that would require more than max allowed chunks
    large_content = generate_uint8_array(10000)  # 10KB content
    
    append_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(large_content)
        .set_chunk_size(100)  # Small chunks = 100 chunks needed
        .set_max_chunks(5)    # But only allow 5 chunks
    )

    # Should fail with max chunks exceeded
    with pytest.raises(ValueError, match="more than.*chunks"):
        append_tx.execute(env.client)

@mark.integration
def test_integration_file_append_transaction_string_contents(env):
    """Test file append with string contents (automatic UTF-8 encoding)."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"Initial content")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS
    file_id = create_receipt.fileId

    # Append string content (should be automatically encoded to UTF-8)
    string_content = "This is a string that should be encoded as UTF-8 bytes 🌟"
    append_receipt = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(string_content)
        .execute(env.client)
    )
    
    assert append_receipt.status == ResponseCode.SUCCESS, f"Append string content failed with status: {ResponseCode(append_receipt.status).name}"

@mark.integration
def test_integration_file_append_transaction_method_chaining(env):
    """Test that all FileAppendTransaction setter methods support method chaining."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS
    file_id = create_receipt.fileId

    # Test method chaining by setting all properties in one chain
    append_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(b"Method chaining test")
        .set_chunk_size(2048)
        .set_max_chunks(15)
    )
    
    # Verify all properties were set correctly
    assert append_tx.file_id == file_id
    assert append_tx.contents == b"Method chaining test"
    assert append_tx.chunk_size == 2048
    assert append_tx.max_chunks == 15
    
    append_receipt = append_tx.execute(env.client)
    assert append_receipt.status == ResponseCode.SUCCESS 

@mark.integration
def test_integration_file_append_transaction_and_view_content(env):
    """Test that all FileAppendTransaction setter methods support method chaining."""
    operator_key = env.operator_key.public_key()

    # Create a file first
    create_receipt = (
        FileCreateTransaction()
        .set_keys(operator_key)
        .set_contents(b"")
        .execute(env.client)
    )
    
    assert create_receipt.status == ResponseCode.SUCCESS
    file_id = create_receipt.fileId

    # Test method chaining by setting all properties in one chain
    append_tx = (
        FileAppendTransaction()
        .set_file_id(file_id)
        .set_contents(b"Method chaining test")
        .set_chunk_size(2048)
        .set_max_chunks(15)
    )

    append_response = append_tx.execute(env.client)

    assert append_response.status == ResponseCode.SUCCESS 
    
    file_info = FileContentsQuery().set_file_id(file_id).execute(env.client)
    assert file_info == b"Method chaining test"