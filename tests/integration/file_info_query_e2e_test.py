import pytest

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_info_query import FileInfoQuery
from tests.integration.utils_for_test import env

@pytest.mark.integration
def test_integration_file_info_query_can_execute(env):
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(b"Hello, World")
        .set_transaction_memo("python sdk e2e tests")
        .execute(env.client)
    )
    file_id = receipt.fileId
    assert file_id is not None, "File ID should not be None"
    
    # Query the file info
    info = (
        FileInfoQuery()
        .set_file_id(file_id)
        .execute(env.client)
    )
    assert str(info.file_id) == str(file_id), "File ID mismatch"
    assert info.size == 12, "File size mismatch"
    assert not info.is_deleted, "File should not be deleted"
    assert info.keys is not None, "Keys should not be None"

@pytest.mark.integration
def test_integration_file_info_query_get_cost(env):
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(b"Hello, World")
        .set_transaction_memo("python sdk e2e tests")
        .execute(env.client)
    )
    file_id = receipt.fileId
    assert file_id is not None, "File ID should not be None"
    
    # Create the query and get its cost
    file_info = FileInfoQuery().set_file_id(file_id)
    
    cost = file_info.get_cost(env.client)
    
    # Execute with the exact cost
    info = file_info.set_query_payment(cost).execute(env.client)
    
    assert str(info.file_id) == str(file_id), "File ID mismatch"
    assert info.size == 12, "File size mismatch"
    assert not info.is_deleted, "File should not be deleted"