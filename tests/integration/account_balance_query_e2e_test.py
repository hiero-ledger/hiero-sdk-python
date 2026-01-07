import pytest

from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.contract.contract_id import ContractId
from tests.integration.utils import IntegrationTestEnv

@pytest.mark.integration
def test_integration_account_balance_query_can_execute():
    env = IntegrationTestEnv()
    
    try:
        CryptoGetAccountBalanceQuery(account_id=env.operator_id).execute(env.client)
    finally:
        env.close()

@pytest.mark.integration
def test_integration_contract_balance_query_can_execute():
    env = IntegrationTestEnv()

    contract_id_str = os.getenv("HEDERA_TEST_CONTRACT_ID")
    if not contract_id_str:
        pytest.skip("Set HEDERA_TEST_CONTRACT_ID (e.g. '0.0.1234') to run this test.")

    contract_id = ContractId.from_string(contract_id_str)

    try:
        CryptoGetAccountBalanceQuery().set_contract_id(contract_id).execute(env.client)
    finally:
        env.close()
