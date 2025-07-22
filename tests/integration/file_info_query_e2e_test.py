"""
Integration tests for FileInfoQuery.
"""

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.hbar import Hbar
from tests.integration.utils_for_test import env

FILE_CONTENT = b"Hello, World"
FILE_MEMO = "python sdk e2e tests"


@pytest.mark.integration
def test_integration_file_info_query_can_execute(env):
    """Test that the FileInfoQuery can be executed successfully."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(FILE_CONTENT)
        .set_transaction_memo(FILE_MEMO)
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Query the file info
    info = FileInfoQuery().set_file_id(file_id).execute(env.client)

    assert str(info.file_id) == str(file_id), "File ID mismatch"
    assert info.size == len(FILE_CONTENT), "File size mismatch"
    assert not info.is_deleted, "File should not be deleted"
    assert info.keys is not None, "Keys should not be None"


@pytest.mark.integration
def test_integration_file_info_query_get_cost(env):
    """Test that the FileInfoQuery can calculate query costs."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(FILE_CONTENT)
        .set_transaction_memo(FILE_MEMO)
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create the query and get its cost
    file_info = FileInfoQuery().set_file_id(file_id)

    cost = file_info.get_cost(env.client)

    # Execute with the exact cost
    info = file_info.set_query_payment(cost).execute(env.client)

    assert str(info.file_id) == str(file_id), "File ID mismatch"
    assert info.size == len(FILE_CONTENT), "File size mismatch"
    assert not info.is_deleted, "File should not be deleted"


@pytest.mark.integration
def test_integration_file_info_query_multiple_keys(env):
    """Test that the FileInfoQuery works correctly with multiple keys."""
    # Create additional test keys
    key1 = PrivateKey.generate()
    key2 = PrivateKey.generate()

    # Create a file with multiple keys
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key(), key1.public_key(), key2.public_key()])
        .set_contents(FILE_CONTENT)
        .set_transaction_memo(FILE_MEMO)
        .freeze_with(env.client)
        .sign(key1)
        .sign(key2)
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Query the file info
    info = FileInfoQuery().set_file_id(file_id).execute(env.client)

    # Verify file info
    assert str(info.file_id) == str(file_id), "File ID mismatch"
    assert info.size == len(FILE_CONTENT), "File size mismatch"
    assert not info.is_deleted, "File should not be deleted"
    assert info.keys is not None, "Keys should not be None"
    assert len(info.keys) == 3, "Should have exactly 3 keys"

    # Verify each key is present
    key_bytes = [key.to_bytes_raw() for key in info.keys]
    assert (
        env.operator_key.public_key().to_bytes_raw() in key_bytes
    ), "Operator key not found"
    assert key1.public_key().to_bytes_raw() in key_bytes, "Key1 not found"
    assert key2.public_key().to_bytes_raw() in key_bytes, "Key2 not found"


@pytest.mark.integration
def test_integration_file_info_query_insufficient_payment(env):
    """Test that FileInfoQuery fails with insufficient payment."""
    # Create a test file first
    receipt = FileCreateTransaction().set_contents(FILE_CONTENT).execute(env.client)
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create query and set very low payment
    file_info = FileInfoQuery().set_file_id(file_id)
    file_info.set_query_payment(Hbar.from_tinybars(1))  # Set very low query payment

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        file_info.execute(env.client)


@pytest.mark.integration
def test_integration_file_info_query_fails_with_invalid_file_id(env):
    """Test that the FileInfoQuery fails with an invalid file ID."""
    # Create a file ID that doesn't exist on the network
    file_id = FileId(0, 0, 999999999)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_FILE_ID"
    ):
        FileInfoQuery(file_id).execute(env.client)
