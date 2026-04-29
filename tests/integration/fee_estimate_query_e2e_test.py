from __future__ import annotations

import pytest

from hiero_sdk_python.account.account_create_transaction import AccountCreateTransaction
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.fees.fee_estimate_mode import FeeEstimateMode
from hiero_sdk_python.file.file_append_transaction import FileAppendTransaction
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.query.fee_estimate_query import FeeEstimateQuery


@pytest.mark.integration
def test_can_execute_fee_estimation_query(env):
    print("test stated")
    tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519()).set_initial_balance(1)
    query = FeeEstimateQuery().set_transaction(tx)
    result = query.execute(env.client)

    print(result)
    assert result is not None


@pytest.mark.integration
def test_can_execute_fee_estimation_query2(env):
    print("test stated 2")
    tx = AccountCreateTransaction().set_key_without_alias(PrivateKey.generate_ed25519()).set_initial_balance(1)
    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    print(result)
    print(type(result.total))
    assert result is not None


@pytest.mark.integration
def test__fee_estimation_query_chuck_tx_can_execute(env):
    print("test stated")

    tx = FileAppendTransaction().set_file_id(FileId(0, 0, 2)).set_chunk_size(10).set_contents("s" * 33)  # 4 chunks

    tx.freeze_with(env.client)
    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    print(result)
    assert result is not None


@pytest.mark.integration
def test_can_execute_fee_estimation_query_chuck_tx(env):
    print("test stated")

    tx = (
        TopicMessageSubmitTransaction().set_topic_id(TopicId(0, 0, 2)).set_chunk_size(10).set_message("s" * 20)
    )  # 2 chunks

    # 2. IMPORTANT: Let freeze_with generate the valid transaction ID sequence
    # This ensures tx._transaction_ids is populated correctly.

    tx.freeze_with(env.client)
    query = FeeEstimateQuery().set_mode(FeeEstimateMode.STATE).set_transaction(tx)
    result = query.execute(env.client)

    print(result)
    assert result is not None
