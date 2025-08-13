import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv

topic_memo = "Python SDK created topic"

@pytest.mark.integration
def test_integration_topic_create_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        transaction = TopicCreateTransaction()
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        
        transaction = TopicCreateTransaction(
            memo=topic_memo,
            admin_key=env.client.operator_private_key.public_key()
        )
        
        transaction.freeze_with(env.client)
        receipt = transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(receipt.status).name}"
        
        topic_id = receipt.topic_id
        assert topic_id is not None
        
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        assert topic_info is not None
        
        assert topic_info.memo == topic_memo
        assert topic_info.sequence_number == 0
        assert env.client.operator_private_key.public_key()._to_proto() == topic_info.admin_key

        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        
        delete_transaction.freeze_with(env.client)
        receipt = delete_transaction.execute(env.client)
        
        assert receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(receipt.status).name}"
    finally:
        env.close() 