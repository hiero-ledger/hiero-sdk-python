import pytest

from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from tests.integration.utils_for_test import IntegrationTestEnv


@pytest.mark.integration
def test_integration_account_balance_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        CryptoGetAccountBalanceQuery(account_id=env.operator_id).execute(env.client)
    finally:
        env.close()