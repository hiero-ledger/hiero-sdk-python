"""
Integration tests for the FileUpdateTransaction class.
"""

from __future__ import annotations

import pytest

from hiero_sdk_python import PrivateKey
from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.file.file_update_transaction import FileUpdateTransaction
from hiero_sdk_python.response_code import ResponseCode


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
    assert receipt.status == ResponseCode.SUCCESS, (
        f"File creation failed with status: {ResponseCode(receipt.status).name}"
    )

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
    assert receipt.status == ResponseCode.SUCCESS, (
        f"File update failed with status: {ResponseCode(receipt.status).name}"
    )

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
        f"File update should have failed with INVALID_FILE_ID status but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_update_transaction_cannot_update_immutable_file(env):
    """Test that the FileUpdateTransaction fails when updating an immutable file."""
    receipt = FileCreateTransaction().set_contents("Immutable file").execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS, (
        f"File creation failed with status: {ResponseCode(receipt.status).name}"
    )

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
        f"File update should have failed with UNAUTHORIZED status but got: {ResponseCode(receipt.status).name}"
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
    assert receipt.status == ResponseCode.SUCCESS, (
        f"File creation failed with status: {ResponseCode(receipt.status).name}"
    )

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Update file contents
    receipt = FileUpdateTransaction().set_file_id(file_id).set_contents("Update contents!").execute(env.client)
    assert receipt.status == ResponseCode.INVALID_SIGNATURE, (
        f"File update should have failed with INVALID_SIGNATURE status but got: {ResponseCode(receipt.status).name}"
    )


@pytest.mark.integration
def test_integration_file_create_transaction_with_supported_key_types(env):
    """Test FileUpdateTransaction with all supported key types."""
    initial_private_key = PrivateKey.generate()

    create_receipt = (
        FileCreateTransaction()
        .set_keys([initial_private_key])
        .set_contents("Hello, Hedera!")
        .freeze_with(env.client)
        .sign(initial_private_key)
        .execute(env.client)
    )

    assert create_receipt.status == ResponseCode.SUCCESS
    assert create_receipt.file_id is not None

    file_id = create_receipt.file_id
    info = FileInfoQuery(file_id).execute(env.client)
    assert len(info.keys) == 1

    file_private_key = PrivateKey.generate()

    file_public_key_private = PrivateKey.generate()
    file_public_key = file_public_key_private.public_key()

    key_list_private_key = PrivateKey.generate()
    key_list = KeyList([key_list_private_key])

    threshold_private_key_1 = PrivateKey.generate()
    threshold_private_key_2 = PrivateKey.generate()
    threshold_key = KeyList(
        [threshold_private_key_1, threshold_private_key_2],
        threshold=1,
    )

    update_receipt = (
        FileUpdateTransaction()
        .set_file_id(file_id)
        .set_keys(
            [
                file_private_key,
                file_public_key,
                key_list,
                threshold_key,
            ]
        )
        .freeze_with(env.client)
        .sign(initial_private_key)
        .sign(file_private_key)
        .sign(file_public_key_private)
        .sign(key_list_private_key)
        .sign(threshold_private_key_1)
        .sign(threshold_private_key_2)
        .execute(env.client)
    )

    assert update_receipt.status == ResponseCode.SUCCESS
    info = FileInfoQuery(file_id).execute(env.client)
    assert len(info.keys) == 4

    # Verify the stored keys authorize file deletion.
    delete_receipt = (
        FileDeleteTransaction()
        .set_file_id(file_id)
        .freeze_with(env.client)
        .sign(file_private_key)
        .sign(file_public_key_private)
        .sign(key_list_private_key)
        .sign(threshold_private_key_1)  # sign with one since threshold is set to one
        .execute(env.client)
    )

    assert delete_receipt.status == ResponseCode.SUCCESS
