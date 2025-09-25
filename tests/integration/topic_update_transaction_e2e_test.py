import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from hiero_sdk_python.tokens.custom_fixed_fee import CustomFixedFee
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_topic_update_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        create_transaction = TopicCreateTransaction(
            memo="Original memo",
            admin_key=env.public_operator_key
        )
        
        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        
        topic_id = create_receipt.topic_id
        
        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Original memo"
        assert info.sequence_number == 0
        assert env.client.operator_private_key.public_key()._to_proto() == info.admin_key

        update_transaction = TopicUpdateTransaction(
            topic_id=topic_id,
            memo="Updated memo"
        )
        
        update_transaction.freeze_with(env.client)
        update_receipt = update_transaction.execute(env.client)
        
        assert update_receipt.status == ResponseCode.SUCCESS, f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"
        
        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        
        assert info.memo == "Updated memo"
        assert info.sequence_number == 0
        assert env.client.operator_private_key.public_key()._to_proto() == info.admin_key

        transaction = TopicDeleteTransaction(topic_id=topic_id)
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 


@pytest.mark.integration
def test_integration_topic_update_transaction_clear_custom_fees():
    env = IntegrationTestEnv()

    try:
        custom_fee = CustomFixedFee().set_amount_in_tinybars(1).set_fee_collector_account_id(env.client.operator_account_id)

        create_transaction = (
            TopicCreateTransaction()
            .set_admin_key(env.client.operator_private_key.public_key())
            .set_fee_schedule_key(env.client.operator_private_key.public_key())
            .set_custom_fees([custom_fee])
        )

        create_receipt = create_transaction.execute(env.client)
        assert create_receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"

        topic_id = create_receipt.topic_id

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert info.custom_fees[0] == custom_fee

        update_transaction = (
            TopicUpdateTransaction(topic_id=topic_id)
            .clear_custom_fees()
        )

        update_receipt = update_transaction.execute(env.client)
        assert update_receipt.status == ResponseCode.SUCCESS, f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"

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
        assert create_receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"

        topic_id = create_receipt.topic_id

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert info.fee_exempt_keys[0].to_bytes_raw() == fee_exempt_key.public_key().to_bytes_raw()
        
        update_transaction = (
            TopicUpdateTransaction(topic_id=topic_id)
            .clear_fee_exempt_keys()
        )

        update_receipt = update_transaction.execute(env.client)
        assert update_receipt.status == ResponseCode.SUCCESS, f"Topic update failed with status: {ResponseCode(update_receipt.status).name}"

        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert info is not None
        assert len(info.fee_exempt_keys) == 0
    finally:
        env.close()
