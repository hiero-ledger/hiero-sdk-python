"""
Integration tests for PRNG transaction.
"""

import pytest

from hiero_sdk_python.prng_transaction import PrngTransaction
from hiero_sdk_python.query.transaction_record_query import TransactionRecordQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env


@pytest.mark.integration
def test_integration_prng_transaction_can_execute(env):
    """Test that the PRNG transaction can be executed successfully."""
    receipt = PrngTransaction().set_range(100).execute(env.client)
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Prng transaction failed with status: {ResponseCode(receipt.status).name}"

    record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

    assert record.prng_number is not None, "PRNG number should not be None"
    assert (
        record.prng_number >= 0 and record.prng_number <= 100
    ), "PRNG number should be between 0 and 100"
    assert record.prng_bytes == b"", "PRNG bytes should be empty bytes"


@pytest.mark.integration
def test_integration_prng_transaction_can_execute_without_range(env):
    """Test that the PRNG transaction can be executed successfully without a range."""
    receipt = PrngTransaction().execute(env.client)
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Prng transaction failed with status: {ResponseCode(receipt.status).name}"

    record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

    assert record.prng_number == 0, "PRNG number should be 0"
    assert len(record.prng_bytes) == 48, "PRNG bytes should be 48 bytes"
    assert record.prng_bytes is not None, "PRNG bytes should not be None"


@pytest.mark.integration
def test_integration_prng_transaction_can_execute_with_zero_range(env):
    """Test that the PRNG transaction can be executed successfully with a zero range."""
    receipt = PrngTransaction().set_range(0).execute(env.client)
    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Prng transaction failed with status: {ResponseCode(receipt.status).name}"

    record = TransactionRecordQuery(receipt.transaction_id).execute(env.client)

    assert record.prng_number == 0, "PRNG number should be 0"
    assert len(record.prng_bytes) == 48, "PRNG bytes should be 48 bytes"
    assert record.prng_bytes is not None, "PRNG bytes should not be None"
