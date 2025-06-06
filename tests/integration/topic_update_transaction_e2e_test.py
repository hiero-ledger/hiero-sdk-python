import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_update_transaction import TopicUpdateTransaction
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
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
        
        topic_id = create_receipt.topicId
        
        info = TopicInfoQuery(topic_id=topic_id).execute(env.client)

        assert info.memo == "Original memo"
        assert info.sequence_number == 0
        assert env.client.operator.private_key.public_key().to_string() == info.admin_key.ed25519.hex()
        
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
        assert env.client.operator.private_key.public_key().to_string() == info.admin_key.ed25519.hex()
        
        transaction = TopicDeleteTransaction(topic_id=topic_id)
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        assert receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 