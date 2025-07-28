"""
Integration tests for the FileUpdateTransaction class.
"""

import pytest

from hiero_sdk_python import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_file_update_transaction_can_execute(env):
    """Test that the FileUpdateTransaction can be executed."""
    # Create initial file
    file_private_key = PrivateKey.generate_ed25519()
    receipt = (
        FileCreateTransaction()
        .set_keys(file_private_key.public_key())
        .set_contents("Initial contents")
        .set_file_memo("python sdk e2e tests")
        .freeze_with(env.client)
        .sign(file_private_key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode.get_name(receipt.status)}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    new_private_key = PrivateKey.generate_ed25519()

    # Update file contents
    new_contents = "Update contents!"
    new_memo = "Update memo"

    receipt = (
        FileUpdateTransaction()
        .set_file_id(file_id)
        .set_keys(new_private_key.public_key())
        .set_contents(new_contents)
        .set_file_memo(new_memo)
        .freeze_with(env.client)
        .sign(new_private_key)
        .sign(file_private_key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File update failed with status: {ResponseCode.get_name(receipt.status)}"

    # Query file info and check if everything is updated
    info = FileInfoQuery().set_file_id(file_id).execute(env.client)

    assert info.file_id == file_id, "File ID should match"
    assert info.file_memo == new_memo, "File memo should match"
    assert info.is_deleted is False, "File should not be deleted"
    assert info.size == len(new_contents.encode("utf-8")), "File size should match"
    assert len(info.keys) == 1, "File should have one key"
    assert info.keys[0].to_bytes_raw() == new_private_key.public_key().to_bytes_raw()


@pytest.mark.integration
def test_integration_file_update_transaction_fails_with_invalid_file_id(env):
    """Test that the FileUpdateTransaction fails when updating an invalid file ID."""
    # Create a file ID that doesn't exist on the network
    file_id = FileId(0, 0, 999999999)

    receipt = FileUpdateTransaction().set_file_id(file_id).execute(env.client)
    assert receipt.status == ResponseCode.INVALID_FILE_ID, (
        f"File update should have failed with INVALID_FILE_ID status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_update_transaction_cannot_update_immutable_file(env):
    """Test that the FileUpdateTransaction fails when updating an immutable file."""
    receipt = FileCreateTransaction().set_contents("Immutable file").execute(env.client)
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode.get_name(receipt.status)}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Update file contents
    new_contents = "Update contents!"

    receipt = (
        FileUpdateTransaction()
        .set_file_id(file_id)
        .set_contents(new_contents)
        .freeze_with(env.client)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.UNAUTHORIZED, (
        f"File update should have failed with UNAUTHORIZED status but got: "
        f"{ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_update_transaction_fails_when_key_is_invalid(env):
    """Test that the FileUpdateTransaction fails when the key is invalid."""
    # Create initial file
    file_private_key = PrivateKey.generate_ed25519()
    receipt = (
        FileCreateTransaction()
        .set_keys(file_private_key.public_key())
        .set_contents("Initial contents")
        .freeze_with(env.client)
        .sign(file_private_key)
        .execute(env.client)
    )
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode.get_name(receipt.status)}"

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Update file contents
    receipt = (
        FileUpdateTransaction()
        .set_file_id(file_id)
        .set_contents("Update contents!")
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"File update should have failed with INVALID_SIGNATURE status but got: "
        f"{ResponseCode(receipt.status).name}"
    )
