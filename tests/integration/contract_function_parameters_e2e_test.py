"""
Integration tests for the ConstructorTestContract constructor parameters.
"""

import pytest

from examples.contracts import CONSTRUCTOR_TEST_CONTRACT_BYTECODE, CONTRACT_DEPLOY_GAS
from hiero_sdk_python.contract.contract_create_transaction import (
    ContractCreateTransaction,
)
from hiero_sdk_python.contract.contract_function_parameters import (
    ContractFunctionParameters,
)
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_create_transaction import FileCreateTransaction
from hiero_sdk_python.response_code import ResponseCode
from tests.integration.utils_for_test import env

# Generate a new ECDSA key pair and extract the first 40 bytes of the public key
# to use as a test address for the contract constructor
TEST_ADDRESS = PrivateKey.generate_ecdsa().public_key().to_string_ecdsa()[:40]


@pytest.mark.integration
def test_constructor_test_contract_parameters(env):
    """Test that constructor parameters are correctly passed to the contract."""
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(CONSTRUCTOR_TEST_CONTRACT_BYTECODE)
        .set_file_memo("ConstructorTestContract bytecode file")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"File creation failed with status: {ResponseCode(receipt.status).name}"
    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Prepare test values for constructor parameters
    test_string = "Test String Value"
    test_bytes32 = b"Test Bytes32 Value"
    test_int8 = 42
    test_address = TEST_ADDRESS
    test_bool = True
    test_bytes = b"Test Bytes Value"
    test_uint8_array = [1, 2, 3, 255]

    # Create contract with constructor parameters
    constructor_params = (
        ContractFunctionParameters()
        .add_string(test_string)
        .add_bytes32(test_bytes32)
        .add_int8(test_int8)
        .add_address(test_address)
        .add_bool(test_bool)
        .add_bytes(test_bytes)
        .add_uint8_array(test_uint8_array)
    )

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(constructor_params)
        .set_contract_memo("ConstructorTestContract with parameters")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), f"Contract creation failed with status: {ResponseCode(receipt.status).name}"

    contract_id = receipt.contract_id
    assert contract_id is not None, "Contract ID should not be None"


@pytest.mark.integration
def test_constructor_test_contract_parameter_variations(env):
    """Test different variations of constructor parameters."""
    # Create file with contract bytecode
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(CONSTRUCTOR_TEST_CONTRACT_BYTECODE)
        .set_file_memo("ConstructorTestContract bytecode file")
        .execute(env.client)
    )

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Test cases with different parameter values
    test_cases = [
        {
            "name": "Basic values",
            "string": "Hello World",
            "bytes32": b"Basic test".ljust(32, b"\0"),
            "int8": 100,
            "address": TEST_ADDRESS,
            "bool": True,
            "bytes": b"Basic bytes",
            "uint8_array": [1, 2, 3],
        },
        {
            "name": "Edge values",
            "string": "A" * 100,  # Long string
            "bytes32": b"X" * 32,  # Full bytes32
            "int8": 127,  # Max int8
            "address": "0x0000000000000000000000000000000000000000",  # Zero address
            "bool": False,
            "bytes": b"",  # Empty bytes
            "uint8_array": [0, 255],  # Min and max uint8
        },
        {
            "name": "Special characters",
            "string": "Special chars: !@#$%^&*()_+",
            "bytes32": b"Special\x00\x01\x02".ljust(32, b"\0"),
            "int8": -128,  # Min int8
            "address": TEST_ADDRESS,
            "bool": True,
            "bytes": b"\x00\x01\x02\x03",  # Binary data
            "uint8_array": [],  # Empty array
        },
    ]

    for test_case in test_cases:
        constructor_params = (
            ContractFunctionParameters()
            .add_string(test_case["string"])
            .add_bytes32(test_case["bytes32"])
            .add_int8(test_case["int8"])
            .add_address(test_case["address"])
            .add_bool(test_case["bool"])
            .add_bytes(test_case["bytes"])
            .add_uint8_array(test_case["uint8_array"])
        )

        receipt = (
            ContractCreateTransaction()
            .set_admin_key(env.operator_key.public_key())
            .set_gas(CONTRACT_DEPLOY_GAS)
            .set_bytecode_file_id(file_id)
            .set_constructor_parameters(constructor_params)
            .set_contract_memo(f"Test case: {test_case['name']}")
            .execute(env.client)
        )

        assert (
            receipt.status == ResponseCode.SUCCESS
        ), f"Contract creation failed for test case '{test_case['name']}'"


@pytest.mark.integration
def test_constructor_test_contract_parameter_order_sensitivity(env):
    """Test that parameter order matters for constructor parameters."""
    # Create file with contract bytecode
    receipt = (
        FileCreateTransaction()
        .set_keys(env.operator_key.public_key())
        .set_contents(CONSTRUCTOR_TEST_CONTRACT_BYTECODE)
        .execute(env.client)
    )

    file_id = receipt.file_id
    assert file_id is not None, "File ID should not be None"

    # Prepare test values
    test_string = "Order Test"
    test_bytes32 = b"Order Test Bytes32"
    test_int8 = 127
    test_address = TEST_ADDRESS
    test_bool = False
    test_bytes = b"Order Test Bytes"
    test_uint8_array = [5, 10, 15]

    # Create contract with constructor parameters in the correct order
    # This order must match the constructor definition in ConstructorTestContract.sol
    correct_order_params = (
        ContractFunctionParameters()
        .add_string(test_string)
        .add_bytes32(test_bytes32)
        .add_int8(test_int8)
        .add_address(test_address)
        .add_bool(test_bool)
        .add_bytes(test_bytes)
        .add_uint8_array(test_uint8_array)
    )

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(correct_order_params)
        .set_contract_memo("Correct parameter order")
        .execute(env.client)
    )

    assert (
        receipt.status == ResponseCode.SUCCESS
    ), "Contract creation with correct parameter order failed"

    # Try with incorrect order (should fail)
    # For example, swap string and bytes32
    incorrect_order_params = (
        ContractFunctionParameters()
        .add_bytes32(test_bytes32)  # Should be string first
        .add_string(test_string)  # Should be bytes32 second
        .add_int8(test_int8)
        .add_address(test_address)
        .add_bool(test_bool)
        .add_uint8_array(test_uint8_array)  # Should be bytes here
        .add_bytes(test_bytes)  # Should be uint8_array here
    )

    receipt = (
        ContractCreateTransaction()
        .set_admin_key(env.operator_key.public_key())
        .set_gas(CONTRACT_DEPLOY_GAS)
        .set_bytecode_file_id(file_id)
        .set_constructor_parameters(incorrect_order_params)
        .set_contract_memo("Incorrect parameter order")
        .execute(env.client)
    )

    assert receipt.status == ResponseCode.CONTRACT_REVERT_EXECUTED, (
        f"Contract creation with incorrect parameter order should have failed "
        f"with CONTRACT_REVERT_EXECUTED but got {ResponseCode(receipt.status).name}"
    )
