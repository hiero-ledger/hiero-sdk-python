from __future__ import annotations

import time

from pytest import mark

from hiero_sdk_python.crypto.key_list import KeyList
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp


@mark.integration
def test_integration_file_create_transaction_can_execute(env):
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Test the contents of the file")
        .set_file_memo("Test the memo of the file")
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Create file failed with status: {ResponseCode(receipt.status).name}"
    )

    file_id = receipt.file_id
    assert file_id is not None, "File ID is None"


@mark.integration
def test_integration_file_create_transaction_no_key(env):
    receipt = FileCreateTransaction().execute(env.client)
    assert receipt.status == ResponseCode.SUCCESS, (
        f"Create file failed with status: {ResponseCode(receipt.status).name}"
    )

    file_id = receipt.file_id
    assert file_id is not None, "File ID is None"


@mark.integration
def test_integration_file_create_transaction_too_large_expiration_fails(env):
    timestamp = Timestamp(int(time.time()) + 9999999999, 0)

    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Large timestamp test")
        .set_expiration_time(timestamp)
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.AUTORENEW_DURATION_NOT_IN_RANGE, (
        f"FileCreateTransaction should have failed with AUTORENEW_DURATION_NOT_IN_RANGE but got: {ResponseCode(receipt.status).name}"
    )


@mark.integration
def test_integration_file_create_transaction_with_supported_key_types(env):
    """Test FileCreateTransaction with all supported key types."""
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

    receipt = (
        FileCreateTransaction()
        .set_keys(
            [
                file_private_key,
                file_public_key,
                key_list,
                threshold_key,
            ]
        )
        .set_contents("Hello, Hedera!")
        .freeze_with(env.client)
        .sign(file_private_key)
        .sign(file_public_key_private)
        .sign(key_list_private_key)
        .sign(threshold_private_key_1)
        .sign(threshold_private_key_2)
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS
    assert receipt.file_id is not None

    info = FileInfoQuery(receipt.file_id).execute(env.client)
    assert len(info.keys) == 4

    # Verify the stored keys authorize file deletion.
    receipt = (
        FileDeleteTransaction()
        .set_file_id(receipt.file_id)
        .freeze_with(env.client)
        .sign(file_private_key)
        .sign(file_public_key_private)
        .sign(key_list_private_key)
        .sign(threshold_private_key_1)  # sign with one since threshold is set to one
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.SUCCESS
