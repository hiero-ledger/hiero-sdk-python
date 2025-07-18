import pytest

from hiero_sdk_python.contract.contract_create_transaction import ContractCreateTransaction
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env

# This is the bytecode for a simple contract
TEST_CONTRACT_BYTECODE = (
    "608060405234801561001057600080fd5b50336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055506101cb806100606000396000f3fe608060405260043610610046576000357c01000000000000000000000000000000000000000000000000000000009004806341c0e1b51461004b578063cfae321714610062575b600080fd5b34801561005757600080fd5b506100606100f2565b005b34801561006e57600080fd5b50610077610162565b6040518080602001828103825283818151815260200191508051906020019080838360005b838110156100b757808201518184015260208101905061009c565b50505050905090810190601f1680156100e45780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b6000809054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff161415610160573373ffffffffffffffffffffffffffffffffffffffff16ff5b565b60606040805190810160405280600d81526020017f48656c6c6f2c20776f726c64210000000000000000000000000000000000000081525090509056fea165627a7a72305820ae96fb3af7cde9c0abfe365272441894ab717f816f07f41f07b1cbede54e256e0029"
)

CONTRACT_DEPLOY_GAS = 200000

@pytest.mark.integration
def test_integration_contract_create_transaction_can_execute(env):
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(TEST_CONTRACT_BYTECODE)
        .set_file_memo("some test file create transaction memo")
        .execute(env.client)
    )
    
    assert receipt.status == ResponseCode.SUCCESS, f"File creation failed with status: {ResponseCode(receipt.status).name}"
    
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"
    
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key)
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_contract_memo("some test contract create transaction memo")
        .execute(env.client)
    )
    
    assert receipt.status == ResponseCode.SUCCESS, f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
    
    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"

@pytest.mark.integration
def test_integration_contract_create_transaction_set_bytecode(env):
    bytecode = bytes.fromhex(TEST_CONTRACT_BYTECODE)
    
    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key)
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode(bytecode)
        .execute(env.client)
    )
    
    assert receipt.status == ResponseCode.SUCCESS, f"Contract creation failed with status: {ResponseCode(receipt.status).name}"
    
    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"
