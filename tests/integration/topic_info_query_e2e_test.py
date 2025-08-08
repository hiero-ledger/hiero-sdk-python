import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_topic_info_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        create_transaction = TopicCreateTransaction(
            memo="Topic for info query",
            admin_key=env.public_operator_key
        )
        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        
        assert create_receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        
        topic_id = create_receipt.topic_id
        
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        
        assert topic_info is not None
        
        assert topic_info.memo == "Topic for info query"
        assert topic_info.sequence_number == 0
        assert env.client.operator_private_key.public_key()._to_proto() == topic_info.admin_key

        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_receipt = delete_transaction.execute(env.client)
        
        assert delete_receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(delete_receipt.status).name}"
    finally:
        env.close() 