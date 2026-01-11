import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.query.account_balance_query import CryptoGetAccountBalanceQuery
from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.contract.contract_delete_transaction import ContractDeleteTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils import IntegrationTestEnv

from examples.contract.contracts import SIMPLE_CONTRACT_BYTECODE


pytestmark = pytest.mark.integration


def _create_test_contract(env: IntegrationTestEnv) -> ContractId:
    bytecode = bytes.fromhex(SIMPLE_CONTRACT_BYTECODE)

    receipt = (
        ContractCreateTransaction()
        .set_bytecode(bytecode)
        .set_gas(2_000_000)
        .set_contract_memo("integration test: contract balance query")
        .execute(env.client)
    )

    if ResponseCode(receipt.status) != ResponseCode.SUCCESS:
        raise RuntimeError(
            f"ContractCreateTransaction failed with status: {ResponseCode(receipt.status).name}"
        )

    if receipt.contract_id is None:
        raise RuntimeError("ContractCreateTransaction succeeded but receipt.contract_id is None")

    return receipt.contract_id


def _delete_contract_best_effort(env: IntegrationTestEnv, contract_id: ContractId) -> None:
    """
    Best-effort cleanup: delete contract and transfer any remaining hbars to the operator account.
    Cleanup failures should not fail the test run (avoid flakes).
    """
    try:
        receipt = (
            ContractDeleteTransaction()
            .set_contract_id(contract_id)
            .set_transfer_account_id(env.operator_id)
            .execute(env.client)
        )

        if ResponseCode(receipt.status) != ResponseCode.SUCCESS:
            print(
                f"[cleanup] ContractDeleteTransaction failed for {contract_id} "
                f"with status: {ResponseCode(receipt.status).name}"
            )
    except Exception as e:
        print(f"[cleanup] Exception while deleting contract {contract_id}: {e}")


def test_integration_account_balance_query_can_execute():
    env = IntegrationTestEnv()
    try:
        balance = CryptoGetAccountBalanceQuery(account_id=env.operator_id).execute(env.client)
        assert balance is not None
        assert hasattr(balance, "hbars")
        assert balance.hbars is not None
        assert balance.hbars.to_tinybars() >= 0
    finally:
        env.close()


def test_integration_contract_balance_query_can_execute():
    env = IntegrationTestEnv()
    contract_id: ContractId | None = None
    try:
        contract_id = _create_test_contract(env)

        balance = CryptoGetAccountBalanceQuery().set_contract_id(contract_id).execute(env.client)

        assert balance is not None
        assert hasattr(balance, "hbars")
        assert balance.hbars is not None
        assert balance.hbars.to_tinybars() >= 0
    finally:
        if contract_id is not None:
            _delete_contract_best_effort(env, contract_id)
        env.close()


def test_integration_balance_query_raises_when_neither_source_set():
    env = IntegrationTestEnv()
    try:
        with pytest.raises(
            ValueError,
            match=r"Either account_id or contract_id must be set before making the request\.",
        ):
            CryptoGetAccountBalanceQuery().execute(env.client)
    finally:
        env.close()


def test_integration_balance_query_with_invalid_account_id_raises():
    env = IntegrationTestEnv()
    try:
        with pytest.raises(TypeError, match=r"account_id must be an AccountId\."):
            CryptoGetAccountBalanceQuery().set_account_id("0.0.12345").execute(env.client)
    finally:
        env.close()


def test_integration_balance_query_with_invalid_contract_id_raises():
    env = IntegrationTestEnv()
    try:
        with pytest.raises(TypeError, match=r"contract_id must be a ContractId\."):
            CryptoGetAccountBalanceQuery().set_contract_id("0.0.12345").execute(env.client)
    finally:
        env.close()
