import time
import pytest
from pytest import mark

from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from tests.integration.utils_for_test import env, IntegrationTestEnv

@mark.integration
def test_integration_file_create_transaction_can_execute(env):
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(b"Test the contents of the file")
        .set_file_memo("Test the memo of the file")
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(receipt.status).name}"
    
    file_id = receipt.file_id
    assert file_id is not None, "File ID is None"

@mark.integration        
def test_integration_file_create_transaction_no_key(env):
    receipt = (
        FileCreateTransaction()
        .execute(env.client)
    )
    assert receipt.status == ResponseCode.SUCCESS, f"Create file failed with status: {ResponseCode(receipt.status).name}"
    
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
    assert receipt.status == ResponseCode.AUTORENEW_DURATION_NOT_IN_RANGE, \
        f"FileCreateTransaction should have failed with AUTORENEW_DURATION_NOT_IN_RANGE but got: {ResponseCode(receipt.status).name}"