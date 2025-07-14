"""
Integration tests for FileDeleteTransaction.
"""

import pytest

from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_file_delete_transaction_can_execute(env):
    """Test that the FileDeleteTransaction can execute a file deletion transaction."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Hello, World")
        .set_file_memo("go sdk e2e tests")
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Create file failed with status: {ResponseCode(receipt.status).name}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID is None"

    # Then delete the file
    receipt = FileDeleteTransaction().set_file_id(file_id).execute(env.client)
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Delete file failed with status: {ResponseCode(receipt.status).name}"

    # Query the file info
    info = FileInfoQuery().set_file_id(file_id).execute(env.client)
    assert info.is_deleted is True, "File should be deleted"


@pytest.mark.integration
def test_integration_file_delete_transaction_fails_when_deleted_twice(env):
    """Test that deleting a file twice fails."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Hello, World")
        .set_file_memo("go sdk e2e tests")
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    file_id = receipt.file_id
    assert file_id is not None

    # Delete once
    receipt = FileDeleteTransaction().set_file_id(file_id).execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS

    # Try to delete again
    receipt = FileDeleteTransaction().set_file_id(file_id).execute(env.client)
    assert receipt.status == ResponseCode.FILE_DELETED, (
        f"File deletion should have failed with FILE_DELETED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_delete_transaction_fails_when_file_does_not_exist(env):
    """Test that deleting a non-existing file fails."""
    # Create a file ID that doesn't exist on the network
    file_id = FileId(0, 0, 999999999)

    receipt = FileDeleteTransaction().set_file_id(file_id).execute(env.client)
    assert receipt.status == ResponseCode.INVALID_FILE_ID, (
        f"File deletion should have failed with INVALID_FILE_ID status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_delete_transaction_fails_when_key_is_invalid(env):
    """Test that deleting a file without proper key raises an exception."""
    key = PrivateKey.generate_ed25519()

    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys(key.public_key())
        .set_contents(b"Test file")
        .freeze_with(env.client)
        .sign(key)  # sign with the private key
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS
    file_id = receipt.file_id
    assert file_id is not None

    # Try to delete the file without the required key signature
    receipt = FileDeleteTransaction().set_file_id(file_id).execute(env.client)
    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"File deletion should have failed with INVALID_SIGNATURE status but got: "
        f"{ResponseCode(receipt.status).name}"
    )
