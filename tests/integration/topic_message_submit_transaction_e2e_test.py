import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.consensus.topic_message_submit_transaction import TopicMessageSubmitTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_topic_message_submit_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        create_transaction = TopicCreateTransaction(
            memo="Python SDK topic",
            admin_key=env.public_operator_key
        )
        
        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        topic_id = create_receipt.topicId
        
        message_transaction = TopicMessageSubmitTransaction(
            topic_id=topic_id,
            message="Hello, Python SDK!"
        )
        
        message_transaction.freeze_with(env.client)
        message_receipt = message_transaction.execute(env.client)
        
        assert message_receipt.status == ResponseCode.SUCCESS, f"Message submission failed with status: {ResponseCode(message_receipt.status).name}"
        
        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_receipt = delete_transaction.execute(env.client)
        
        assert delete_receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(delete_receipt.status).name}"
    finally:
        env.close() 