import pytest

from hiero_sdk_python.consensus.topic_create_transaction import TopicCreateTransaction
from hiero_sdk_python.consensus.topic_delete_transaction import TopicDeleteTransaction
from hiero_sdk_python.exceptions import PrecheckError
from hiero_sdk_python.query.topic_info_query import TopicInfoQuery
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_topic_delete_transaction_can_execute():
    env = IntegrationTestEnv()
    
    try:
        create_transaction = TopicCreateTransaction(
            memo="Topic to delete",
            admin_key=env.public_operator_key
        )
        create_transaction.freeze_with(env.client)
        create_receipt = create_transaction.execute(env.client)
        
        assert create_receipt.status == ResponseCode.SUCCESS, f"Topic creation failed with status: {ResponseCode(create_receipt.status).name}"
        
        topic_id = create_receipt.topic_id
        assert topic_id is not None
        
        topic_info = TopicInfoQuery(topic_id=topic_id).execute(env.client)
        
        assert topic_info is not None
        
        delete_transaction = TopicDeleteTransaction(topic_id=topic_id)
        delete_transaction.freeze_with(env.client)
        delete_receipt = delete_transaction.execute(env.client)
        
        assert delete_receipt.status == ResponseCode.SUCCESS, f"Topic deletion failed with status: {ResponseCode(delete_receipt.status).name}"
        
        with pytest.raises(PrecheckError, match="failed precheck with status: INVALID_TOPIC_ID"):
            TopicInfoQuery(topic_id=topic_id).execute(env.client)
    finally:
        env.close() 