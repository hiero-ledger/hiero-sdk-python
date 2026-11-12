from __future__ import annotations

import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.crypto.public_key import PublicKey
from hiero_sdk_python.Duration import Duration
from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.hbar_unit import HbarUnit
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.timestamp import Timestamp
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from hiero_sdk_python.transaction.transaction import Transaction
from tests.integration.utils import IntegrationTestEnv


@pytest.mark.integration
def test_integration_topic_update_transaction_can_execute():
    env = IntegrationTestEnv()

    try:
        create_transaction = TopicCreateTransaction(memo="Original memo", admin_key=env.public_operator_key)

        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        )

        topic_id = create_receipt.topic_id

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Original memo"
        assert info.sequence_number == 0
        assert isinstance(info.admin_key, PublicKey)
        assert env.client.operator_private_key.public_key().to_bytes_raw() == info.admin_key.to_bytes_raw()

        update_transaction = TopicUpdateTransaction(topic_id=topic_id, memo="Updated memo")

        update_transaction.freeze_with(env.client)
        update_receipt = update_transaction.execute(env.client)

        assert update_receipt.status == ResponseCode.SUCCESS, (
            f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"
        )

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Updated memo"
        assert info.sequence_number == 0
        assert isinstance(info.admin_key, PublicKey)
        assert env.client.operator_private_key.public_key().to_bytes_raw() == info.admin_key.to_bytes_raw()

        transaction = TopicDeleteTransaction(topic_id=topic_id)
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, (
            f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
        )
    finally:
        env.close()


@pytest.mark.integration
def test_integration_topic_update_transaction_clear_custom_fees():
    env = IntegrationTestEnv()

    try:
        custom_fee = (
            CustomFixedFee()
            .set_hbar_amount(Hbar.from_tinybars(1))
            .set_fee_collector_account_id(env.client.operator_account_id)
        )

        create_transaction = (
            TopicCreateTransaction()
            .set_admin_key(env.client.operator_private_key.public_key())
            .set_fee_schedule_key(env.client.operator_private_key.public_key())
            .set_custom_fees([custom_fee])
        )

        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        )

        topic_id = create_receipt.topic_id

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert info.custom_fees[0] == custom_fee

        update_transaction = TopicUpdateTransaction(topic_id=topic_id).clear_custom_fees()

        update_receipt = update_transaction.execute(env.client)
        assert update_receipt.status == ResponseCode.SUCCESS, (
            f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"
        )

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert len(info.custom_fees) == 0

    finally:
        env.close()


@pytest.mark.integration
def test_integration_topic_update_transaction_clear_fee_exempt_keys():
    env = IntegrationTestEnv()

    try:
        fee_exempt_key = PrivateKey.generate_ecdsa()

        create_transaction = (
            TopicCreateTransaction()
            .set_admin_key(env.client.operator_private_key.public_key())
            .set_fee_exempt_keys([fee_exempt_key.public_key()])
        )

        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, (
            f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        )

        topic_id = create_receipt.topic_id

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert info.fee_exempt_keys[0].to_bytes_raw() == fee_exempt_key.public_key().to_bytes_raw()

        update_transaction = TopicUpdateTransaction(topic_id=topic_id).clear_fee_exempt_keys()

        update_receipt = update_transaction.execute(env.client)
        assert update_receipt.status == ResponseCode.SUCCESS, (
            f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"
        )

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert len(info.fee_exempt_keys) == 0
    finally:
        env.close()


@pytest.mark.integration
def test_serialize_topic_update_transaction_can_execute(env):
    """Verify restored update fields and the resulting network state."""
    topic_id = None

    try:
        receipt = TopicCreateTransaction(
            memo="Original topic", admin_key=env.public_operator_key, fee_schedule_key=env.public_operator_key
        ).execute(env.client)
        topic_id = receipt.topic_id

        assert receipt.status == ResponseCode.SUCCESS
        assert topic_id is not None

        before = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert before.expiration_time is not None

        expiration = Timestamp(before.expiration_time.seconds + 60, 0)
        period = Duration(7_776_000)
        submit_key = PrivateKey.generate_ed25519().public_key()
        exempt_key = PrivateKey.generate_ecdsa().public_key()
        fee = CustomFixedFee(amount=2, fee_collector_account_id=env.operator_id)

        transaction = TopicUpdateTransaction(
            topic_id=topic_id,
            memo="Updated round-trip topic",
            admin_key=env.public_operator_key,
            submit_key=submit_key,
            auto_renew_period=period,
            auto_renew_account=env.operator_id,
            expiration_time=expiration,
            fee_schedule_key=env.public_operator_key,
            fee_exempt_keys=[exempt_key],
            custom_fees=[fee],
        )
        transaction.transaction_fee = Hbar.of(30, HbarUnit.HBAR)
        transaction.freeze_with(env.client)

        original_bytes = transaction.to_bytes()
        restored = Transaction.from_bytes(original_bytes)

        assert isinstance(restored, TopicUpdateTransaction)
        assert restored.topic_id == topic_id
        assert restored.topic_memo == "Updated round-trip topic"
        assert restored.admin_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert restored.submit_key.to_proto_key() == submit_key.to_proto_key()
        assert restored.auto_renew_period == period
        assert restored.auto_renew_account == env.operator_id
        assert restored.expiration_time == expiration
        assert restored.fee_schedule_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert [key.to_proto_key() for key in restored.fee_exempt_keys] == [exempt_key.to_proto_key()]
        assert restored.custom_fees == [fee]
        assert restored.to_bytes() == original_bytes

        receipt = restored.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Updated round-trip topic"
        assert info.admin_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert info.submit_key.to_proto_key() == submit_key.to_proto_key()
        assert info.auto_renew_period == period
        assert info.auto_renew_account == env.operator_id
        assert info.expiration_time.seconds == expiration.seconds
        assert info.fee_schedule_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert [key.to_proto_key() for key in info.fee_exempt_keys] == [exempt_key.to_proto_key()]
        assert info.custom_fees == [fee]
    finally:
        if topic_id is not None:
            receipt = TopicDeleteTransaction(topic_id=topic_id).execute(env.client)
            assert receipt.status == ResponseCode.SUCCESS


@pytest.mark.integration
@pytest.mark.parametrize("clear_lists", [False, True], ids=["unset", "empty"])
def test_serialize_topic_update_preserves_unset_and_empty_lists(env, clear_lists):
    """Verify absent and explicitly empty update fields retain their meaning."""
    topic_id = None

    try:
        exempt_key = PrivateKey.generate_ed25519().public_key()
        fee = CustomFixedFee(amount=1, fee_collector_account_id=env.operator_id)

        receipt = TopicCreateTransaction(
            memo="Memo to clear",
            admin_key=env.public_operator_key,
            submit_key=env.public_operator_key,
            fee_schedule_key=env.public_operator_key,
            custom_fees=[fee],
            fee_exempt_keys=[exempt_key],
        ).execute(env.client)
        topic_id = receipt.topic_id

        assert receipt.status == ResponseCode.SUCCESS
        assert topic_id is not None

        transaction = TopicUpdateTransaction(topic_id=topic_id, memo="")
        if clear_lists:
            transaction.clear_custom_fees()
            transaction.clear_fee_exempt_keys()
        transaction.freeze_with(env.client)

        original_bytes = transaction.to_bytes()
        restored = Transaction.from_bytes(original_bytes)

        assert isinstance(restored, TopicUpdateTransaction)
        assert restored.topic_id == topic_id
        assert restored.topic_memo == ""
        assert restored.custom_fees == ([] if clear_lists else None)
        assert restored.fee_exempt_keys == ([] if clear_lists else None)

        for field in (
            "admin_key",
            "submit_key",
            "fee_schedule_key",
            "auto_renew_period",
            "auto_renew_account",
            "expiration_time",
        ):
            assert getattr(restored, field) is None, field

        assert restored.to_bytes() == original_bytes

        receipt = restored.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == ""
        assert info.custom_fees == ([] if clear_lists else [fee])
        assert [key.to_proto_key() for key in info.fee_exempt_keys] == (
            [] if clear_lists else [exempt_key.to_proto_key()]
        )
        assert info.admin_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert info.submit_key.to_proto_key() == env.public_operator_key.to_proto_key()
        assert info.fee_schedule_key.to_proto_key() == env.public_operator_key.to_proto_key()
    finally:
        if topic_id is not None:
            receipt = TopicDeleteTransaction(topic_id=topic_id).execute(env.client)
            assert receipt.status == ResponseCode.SUCCESS
