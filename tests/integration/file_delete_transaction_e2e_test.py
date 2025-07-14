import pytest

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_delete_transaction import FileDeleteTransaction
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env

@pytest.mark.integration
def test_integration_file_delete_transaction_can_execute(env):
    # Create a file
    create_receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Hello, World")
        .set_file_memo("go sdk e2e tests")
        .execute(env.client)
    )
    assert create_receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(create_receipt.status).name}"
    
    file_id = create_receipt.fileId
    assert file_id is not None, "File ID is None"

    # Then delete the file
    delete_receipt = (
        FileDeleteTransaction()
        .set_file_id(file_id)
        .execute(env.client)
    )
    assert delete_receipt.status == ResponseCode.SUCCESS, f"Delete file failed with status: {ResponseCode(delete_receipt.status).name}"
    
    # Query the file info
    info = (
        FileInfoQuery()
        .set_file_id(file_id)
        .execute(env.client)
    )
    assert info.is_deleted == True, "File should be deleted"