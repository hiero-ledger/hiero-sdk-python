from __future__ import annotations

import time

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.query.fee_estimate_query import FeeEstimateQuery
from hiero_sdk_python.transaction.transfer_transaction import TransferTransaction


_fee_estimation_ready = False
_fee_estimation_error: Exception | None = None


def wait_for_fee_estimation_service_ready(env):
    """
    Wait until the FeeEstimationService is ready with a timeout.
    """
    global _fee_estimation_ready, _fee_estimation_error

    if _fee_estimation_ready:
        return
    if _fee_estimation_error:
        raise _fee_estimation_error

    attempts = 0
    last_error = None

    print("Waiting for FeeEstimationService to get ready...")

    deadline = time.monotonic() + 600.0
    while time.monotonic() < deadline:
        attempts += 1
        try:
            probe = (
                TransferTransaction()
                .add_hbar_transfer(env.operator_id, Hbar(-1))
                .add_hbar_transfer(env.operator_id, Hbar(1))
            )

            FeeEstimateQuery().set_mode(FeeEstimateMode.INTRINSIC).set_transaction(probe).execute(env.client)

            _fee_estimation_ready = True

            print(f"FeeEstimationService ready after {attempts} attempts.")
            return

        except Exception as e:
            last_error = e
            time.sleep(5.0)

    _fee_estimation_error = Exception(
        f"FeeEstimationService not became ready after {attempts} attempts. Last error: {last_error}"
    )

    raise _fee_estimation_error


@pytest.mark.integration
def test_can_execute_fee_estimation_query(env):
    """
    Integration test that verifies a fee estimation query executes successfully and returns a non-null result.
    """
    wait_for_fee_estimation_service_ready(env)
    tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519()).set_initial_balance(1)

    query = FeeEstimateQuery().set_transaction(tx)
    result = query.execute(env.client)

    assert result is not None


@pytest.mark.integration
def test_can_execute_fee_estimation_query2(env):
    """Integration test that verifies a state-mode fee estimation query
    executes successfully and returns a non-null result.
    """
    wait_for_fee_estimation_service_ready(env)
    tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519()).set_initial_balance(1)

    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    assert result is not None


@pytest.mark.integration
def test__fee_estimation_query_chunk_tx_can_execute(env):
    """Integration test that verifies a state-mode fee estimation query executes
    successfully for a chunked file append transaction and returns a non-null result.
    """
    wait_for_fee_estimation_service_ready(env)
    tx = FileAppendTransaction().set_file_id(FileId(0, 0, 2)).set_chunk_size(10).set_contents("s" * 33)  # 4 chunks

    tx.freeze_with(env.client)
    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    assert result is not None


@pytest.mark.integration
def test_can_execute_fee_estimation_query_chunk_tx(env):
    """Integration test that verifies a state-mode fee estimation query executes successfully
    for a chunked topic message submit transaction and returns a non-null result.
    """
    wait_for_fee_estimation_service_ready(env)
    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId(0, 0, 2)).set_chunk_size(10).set_message("s" * 20)
    )  # 2 chunks

    tx.freeze_with(env.client)
    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    assert result is not None
