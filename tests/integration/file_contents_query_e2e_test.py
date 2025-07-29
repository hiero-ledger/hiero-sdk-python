"""
Integration tests for FileContentsQuery.
"""

import pytest

from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.file.file_contents_query import FileContentsQuery
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from tests.integration.utils_for_test import env

FILE_CONTENT = b"Hello, World"


@pytest.mark.integration
def test_integration_file_contents_query_can_execute(env):
    """Test that the FileContentsQuery can be executed successfully."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(FILE_CONTENT)
        .set_transaction_memo("python sdk e2e tests")
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Query the file contents
    contents = FileContentsQuery().set_file_id(file_id).execute(env.client)
    assert contents == FILE_CONTENT, "File contents mismatch"


@pytest.mark.integration
def test_integration_file_contents_query_get_cost(env):
    """Test that the FileContentsQuery can calculate query costs."""
    # Create a file
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_contents(FILE_CONTENT)
        .set_transaction_memo("python sdk e2e tests")
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create the query and get its cost
    file_contents = FileContentsQuery().set_file_id(file_id)

    cost = file_contents.get_cost(env.client)

    # Execute with the exact cost
    contents = file_contents.set_query_payment(cost).execute(env.client)

    assert contents == FILE_CONTENT, "File contents mismatch"


@pytest.mark.integration
def test_integration_file_contents_query_empty_contents(env):
    """Test that FileContentsQuery can execute with empty contents."""
    # Create a file with no contents
    receipt = (
        FileCreateTransaction()
        .set_keys([env.operator_key.public_key()])
        .set_transaction_memo("python sdk e2e tests")
        .execute(env.client)
    )
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Query the empty file contents
    contents = FileContentsQuery().set_file_id(file_id).execute(env.client)

    assert contents == b"", "File contents should be empty"


@pytest.mark.integration
def test_integration_file_contents_query_insufficient_payment(env):
    """Test that FileContentsQuery fails with insufficient payment."""
    # Create a test file first
    receipt = FileCreateTransaction().set_contents(FILE_CONTENT).execute(env.client)
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Create query and set very low payment
    file_contents = FileContentsQuery().set_file_id(file_id)
    file_contents.set_query_payment(Hbar.from_tinybars(1))  # Set very low query payment

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INSUFFICIENT_TX_FEE"
    ):
        file_contents.execute(env.client)


@pytest.mark.integration
def test_integration_file_contents_query_fails_with_invalid_file_id(env):
    """Test that the FileContentsQuery fails with an invalid file ID."""
    # Create a file ID that doesn't exist on the network
    file_id = FileId(0, 0, 999999999)

    with pytest.raises(
        PrecheckError, match="failed precheck with status: INVALID_FILE_ID"
    ):
        FileContentsQuery(file_id).execute(env.client)
