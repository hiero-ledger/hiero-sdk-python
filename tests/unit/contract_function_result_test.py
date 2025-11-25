"""
Unit tests for the ContractFunctionResult class.
"""

import pytest
from google.protobuf.wrappers_pb2 import BytesValue, Int64Value

from hiero_sdk_python.contract.contract_function_result import ContractFunctionResult
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_log_info import ContractLogInfo
from hiero_sdk_python.contract.contract_nonce_info import ContractNonceInfo
from hiero_sdk_python.hapi.services import contract_types_pb2

pytestmark = pytest.mark.unit


@pytest.fixture
def log_info():
    """Fixture for a ContractLogInfo."""
    return ContractLogInfo(
        contract_id=ContractId(0, 0, 456),
        bloom=bytes.fromhex("abcd"),
        topics=[bytes.fromhex("1234"), bytes.fromhex("5678")],
        data=bytes.fromhex("90ab"),
    )


@pytest.fixture
def contract_call_result_bytes():
    """Fixture for contract call result bytes."""
    # Static types (32 bytes each)
    uint256_bytes = bytes.fromhex(
        "000000000000000000000000000000000000000000000000000000000000002a"
    )  # 42

    bool_bytes = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000001"
    )  # true

    address_bytes = bytes.fromhex(
        "000000000000000000000000abcdef0123456789abcdef0123456789abcdef01"
    )  # address

    bytes32_value = bytes.fromhex(
        "1122334455667788990011223344556677889900112233445566778899001122"
    )  # bytes32

    # Dynamic type offsets (32 bytes each)
    bytes_offset = bytes.fromhex(
        "00000000000000000000000000000000000000000000000000000000000000c0"
    )  # offset to bytes

    string_offset = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000100"
    )  # offset to string

    # Dynamic data section
    bytes_length = bytes.fromhex(
        "000000000000000000000000000000000000000000000000000000000000000a"
    )  # length: 10

    bytes_value = bytes.fromhex(
        "1234567890123456789000000000000000000000000000000000000000000000"
    )  # bytes data

    string_length = bytes.fromhex(
        "000000000000000000000000000000000000000000000000000000000000000d"
    )  # length: 13

    string_value = bytes.fromhex(
        "48656c6c6f2c20776f726c642100000000000000000000000000000000000000"
    )  # "Hello, world!"

    return (
        uint256_bytes  # 32 bytes: uint256 = 42
        + bool_bytes  # 32 bytes: bool = true
        + address_bytes  # 32 bytes: address
        + bytes32_value  # 32 bytes: bytes32
        + bytes_offset  # 32 bytes: offset to bytes data
        + string_offset  # 32 bytes: offset to string data
        + bytes_length  # 32 bytes: bytes length
        + bytes_value  # 32 bytes: bytes data + padding
        + string_length  # 32 bytes: string length
        + string_value  # 32 bytes: string data + padding
    )


@pytest.fixture
def contract_function_result(contract_id, log_info, contract_call_result_bytes):
    """Fixture for a ContractFunctionResult."""
    return ContractFunctionResult(
        contract_id=contract_id,
        contract_call_result=contract_call_result_bytes,
        error_message="No errors",
        bloom=bytes.fromhex("ffff"),
        gas_used=100000,
        log_info=[log_info],
        evm_address=ContractId(
            evm_address=bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
        ),
        gas_available=1000000,
        amount=50,
        function_parameters=bytes.fromhex("aabb"),
        contract_nonces=[ContractNonceInfo(ContractId(0, 0, 789), 5)],
        signer_nonce=10,
    )


@pytest.fixture
def proto_contract_function_result(contract_id, log_info):
    """Fixture for a protobuf ContractFunctionResult."""
    log_info_proto = log_info._to_proto()

    # Create ContractNonceInfo and convert to proto
    contract_nonce = ContractNonceInfo(ContractId(0, 0, 789), 5)
    contract_nonce_proto = contract_nonce._to_proto()

    return contract_types_pb2.ContractFunctionResult(
        contractID=contract_id._to_proto(),
        contractCallResult=bytes.fromhex("aabbcc"),
        errorMessage="No errors",
        bloom=bytes.fromhex("ffff"),
        gasUsed=100000,
        logInfo=[log_info_proto],
        evm_address=BytesValue(
            value=bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
        ),
        gas=1000000,
        amount=50,
        functionParameters=bytes.fromhex("aabb"),
        contract_nonces=[contract_nonce_proto],
        signer_nonce=Int64Value(value=10),
    )


def test_initialization():
    """Test basic initialization of ContractFunctionResult."""
    result = ContractFunctionResult()

    assert result.contract_id is None
    assert result.contract_call_result is None
    assert result.error_message is None
    assert result.bloom is None
    assert result.gas_used is None
    assert result.log_info == []
    assert result.evm_address is None
    assert result.gas_available is None
    assert result.amount is None
    assert result.function_parameters is None
    assert result.contract_nonces == []
    assert result.signer_nonce is None


def test_initialization_with_values(contract_id, log_info, contract_call_result_bytes):
    """Test initialization of ContractFunctionResult with values."""
    result = ContractFunctionResult(
        contract_id=contract_id,
        contract_call_result=contract_call_result_bytes,
        error_message="No errors",
        bloom=bytes.fromhex("ffff"),
        gas_used=100000,
        log_info=[log_info],
        evm_address=ContractId(
            evm_address=bytes.fromhex("abcdef0123456789abcdef0123456789abcdef01")
        ),
        gas_available=1000000,
        amount=50,
        function_parameters=bytes.fromhex("aabb"),
        contract_nonces=[ContractNonceInfo(ContractId(0, 0, 789), 5)],
        signer_nonce=10,
    )

    assert result.contract_id == contract_id
    assert result.contract_call_result == contract_call_result_bytes
    assert result.error_message == "No errors"
    assert result.bloom == bytes.fromhex("ffff")
    assert result.gas_used == 100000
    assert result.log_info == [log_info]
    assert result.evm_address.evm_address == bytes.fromhex(
        "abcdef0123456789abcdef0123456789abcdef01"
    )
    assert result.gas_available == 1000000
    assert result.amount == 50
    assert result.function_parameters == bytes.fromhex("aabb")
    assert result.contract_nonces == [ContractNonceInfo(ContractId(0, 0, 789), 5)]
    assert result.signer_nonce == 10


def test_get_result_empty():
    """Test get_result method with empty result."""
    result = ContractFunctionResult()

    assert not result.get_result(["uint256", "bool"])


def test_get_result(contract_function_result):
    """Test get_result method with valid output types."""
    output = contract_function_result.get_result(["uint256", "bool"])

    assert output == [42, True]


def test_get_value_at_index_no_result():
    """Test _get_value_at_index with no result."""
    result = ContractFunctionResult()

    with pytest.raises(ValueError, match="Contract call result is None"):
        result._get_value_at_index(0, 32)


def test_get_value_at_index_out_of_bounds(contract_function_result):
    """Test _get_value_at_index with index out of bounds."""
    with pytest.raises(ValueError, match="Result index out of bounds"):
        contract_function_result._get_value_at_index(100, 32)


def test_contract_function_result_getters(contract_function_result):
    """Test all ContractFunctionResult getter methods using the fixture data."""
    # Test all getters with the fixture data
    assert contract_function_result.get_uint256(0) == 42
    assert contract_function_result.get_bool(1) is True
    assert (
        contract_function_result.get_address(2)
        == "abcdef0123456789abcdef0123456789abcdef01"
    )
    assert contract_function_result.get_bytes32(3) == bytes.fromhex(
        "1122334455667788990011223344556677889900112233445566778899001122"
    )
    assert contract_function_result.get_bytes(4) == bytes.fromhex(
        "12345678901234567890"
    )
    assert contract_function_result.get_string(5) == "Hello, world!"

    # Test get_result with all supported Solidity output types and verify decoded values
    decoded_result = contract_function_result.get_result(
        [
            "uint256",  # index 0: 42
            "bool",  # index 1: True
            "address",  # index 2: "abcdef0123456789abcdef0123456789abcdef01"
            "bytes32",  # index 3: bytes32 value
            "bytes",  # index 4: bytes value
            "string",  # index 5: "Hello, world!"
        ]
    )
    assert decoded_result == [
        42,
        True,
        "0xabcdef0123456789abcdef0123456789abcdef01",  # address starting with 0x
        bytes.fromhex(
            "1122334455667788990011223344556677889900112233445566778899001122"
        ),
        bytes.fromhex("12345678901234567890"),
        "Hello, world!",
    ]


def test_get_address_no_result():
    """Test get_address with no result."""
    result = ContractFunctionResult()

    with pytest.raises(ValueError, match="Contract call result is None"):
        result.get_address(0)


def test_get_address_out_of_bounds(contract_function_result):
    """Test get_address with index out of bounds."""
    with pytest.raises(ValueError, match="Result index out of bounds"):
        contract_function_result.get_address(100)


def test_get_address(contract_function_result):
    """Test get_address with valid index."""
    # Test getting the address from the third position
    address = contract_function_result.get_address(2)
    assert address == "abcdef0123456789abcdef0123456789abcdef01"


def test_uint256_values():
    """Test uint256 getter with various values."""
    test_values = [0, 1, 2**32, 2**64, 2**255, 2**256 - 1]
    encoded_bytes = b"".join(
        value.to_bytes(32, byteorder="big", signed=False) for value in test_values
    )
    result = ContractFunctionResult(contract_call_result=encoded_bytes)
    for idx, expected in enumerate(test_values):
        assert result.get_uint256(idx) == expected, f"Failed at idx={idx} for uint256"


def test_int256_values():
    """Test int256 getter with various values."""
    test_values = [0, 1, -1, 2**127 - 1, -(2**127), 123456789, -123456789]
    encoded_bytes = b"".join(
        value.to_bytes(32, byteorder="big", signed=True) for value in test_values
    )
    result = ContractFunctionResult(contract_call_result=encoded_bytes)
    for idx, expected in enumerate(test_values):
        assert result.get_int256(idx) == expected, f"Failed at idx={idx} for int256"


# Number sizes for uint and int types (in bits)
UINT_INT_SIZES = list(range(8, 257, 8))


def test_uint_getters():
    """Test all uint getters (uint8-uint256) with value 42."""
    test_value = 42
    encoded_bytes = test_value.to_bytes(32, byteorder="big", signed=False)
    result = ContractFunctionResult(contract_call_result=encoded_bytes)

    # Test all uint getters return the same value
    for size in UINT_INT_SIZES:
        getter = getattr(result, f"get_uint{size}")
        assert getter(0) == test_value


def test_int_getters():
    """Test all int getters (int8-int256) with value 42."""
    test_value = 42
    encoded_bytes = test_value.to_bytes(32, byteorder="big", signed=True)
    result = ContractFunctionResult(contract_call_result=encoded_bytes)

    for size in UINT_INT_SIZES:
        getter = getattr(result, f"get_int{size}")
        assert getter(0) == test_value


def test_edge_case_values():
    """Test edge cases for integer getters."""
    # Test maximum values for different bit sizes
    max_values = [255, 65535, 16777215, 4294967295, 1099511627775, 281474976710655]
    encoded_bytes = b"".join(
        value.to_bytes(32, byteorder="big", signed=False) for value in max_values
    )
    result = ContractFunctionResult(contract_call_result=encoded_bytes)

    # Test uint getters with max values
    assert result.get_uint8(0) == 255 and result.get_uint16(1) == 65535
    assert result.get_uint24(2) == 16777215 and result.get_uint32(3) == 4294967295
    assert (
        result.get_uint40(4) == 1099511627775
        and result.get_uint48(5) == 281474976710655
    )

    # Test negative values for int getters
    neg_values = [-1, -32768, -8388608, -2147483648]
    neg_encoded = b"".join(
        value.to_bytes(32, byteorder="big", signed=True) for value in neg_values
    )
    neg_result = ContractFunctionResult(contract_call_result=neg_encoded)

    assert neg_result.get_int8(0) == -1 and neg_result.get_int16(1) == -32768
    assert (
        neg_result.get_int24(2) == -8388608 and neg_result.get_int32(3) == -2147483648
    )


def test_string_retrieval():
    """Test string retrieval from contract function result."""
    greet_result_bytes = (
        bytes.fromhex(
            "0000000000000000000000000000000000000000000000000000000000000020"
        )  # offset
        + bytes.fromhex(
            "000000000000000000000000000000000000000000000000000000000000000d"
        )  # length
        + bytes.fromhex(
            "48656c6c6f2c20776f726c642100000000000000000000000000000000000000"
        )  # "Hello, world!"
    )
    greet_result = ContractFunctionResult(contract_call_result=greet_result_bytes)
    assert greet_result.get_string(0) == "Hello, world!"
    with pytest.raises(ValueError, match="Result index out of bounds"):
        greet_result.get_string(1)


def test_bytes32_retrieval():
    """Test bytes32 retrieval from contract function result."""
    message_result_bytes = bytes.fromhex(
        "1122334455667788990011223344556677889900112233445566778899001122"
    )
    message_result = ContractFunctionResult(contract_call_result=message_result_bytes)
    assert message_result.get_bytes32(0) == bytes.fromhex(
        "1122334455667788990011223344556677889900112233445566778899001122"
    )


def test_large_numbers():
    """Test handling of large numbers (uint256 max, int256 -1)."""
    large_numbers_bytes = bytes.fromhex(
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    ) + bytes.fromhex(
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    large_numbers_result = ContractFunctionResult(
        contract_call_result=large_numbers_bytes
    )
    assert large_numbers_result.get_uint256(0) == 2**256 - 1
    assert large_numbers_result.get_int256(1) == -1


def test_error_handling():
    """Test error handling for invalid data."""
    # Test with empty result
    empty_result = ContractFunctionResult()
    with pytest.raises(ValueError, match="Contract call result is None"):
        empty_result.get_uint256(0)

    # Test with malformed data (too short)
    short_result = ContractFunctionResult(contract_call_result=bytes.fromhex("1234"))
    with pytest.raises(ValueError, match="Result index out of bounds"):
        short_result.get_uint256(0)

    # Test with invalid offset for dynamic data
    invalid_offset_bytes = bytes.fromhex(
        "0000000000000000000000000000000000000000000000000000000000000001"
    ) + bytes.fromhex(  # valid uint256
        "000000000000000000000000000000000000000000000000000000000000ffff"
    )  # invalid offset
    invalid_offset_result = ContractFunctionResult(
        contract_call_result=invalid_offset_bytes
    )
    with pytest.raises(ValueError, match="Result index out of bounds"):
        invalid_offset_result.get_bytes(1)


def test_from_proto(proto_contract_function_result):
    """Test _from_proto method."""
    result = ContractFunctionResult._from_proto(proto_contract_function_result)

    assert result.contract_id == ContractId(0, 0, 1)
    assert result.contract_call_result == bytes.fromhex("aabbcc")
    assert result.error_message == "No errors"
    assert result.bloom == bytes.fromhex("ffff")
    assert result.gas_used == 100000
    assert len(result.log_info) == 1
    assert result.evm_address.evm_address == bytes.fromhex(
        "abcdef0123456789abcdef0123456789abcdef01"
    )
    assert result.gas_available == 1000000
    assert result.amount == 50
    assert result.function_parameters == bytes.fromhex("aabb")
    assert ContractNonceInfo(ContractId(0, 0, 789), 5) in result.contract_nonces
    assert result.signer_nonce == 10


def test_from_proto_none():
    """Test _from_proto method with None."""
    with pytest.raises(ValueError, match="Contract function result proto is None"):
        ContractFunctionResult._from_proto(None)


def test_to_proto(contract_function_result):
    """Test _to_proto method."""
    proto = contract_function_result._to_proto()

    assert proto.contractID == contract_function_result.contract_id._to_proto()
    assert proto.contractCallResult == contract_function_result.contract_call_result
    assert proto.errorMessage == contract_function_result.error_message
    assert proto.bloom == contract_function_result.bloom
    assert proto.gasUsed == contract_function_result.gas_used
    assert len(proto.logInfo) == 1
    assert proto.evm_address.value == contract_function_result.evm_address.evm_address
    assert proto.gas == contract_function_result.gas_available
    assert proto.amount == contract_function_result.amount
    assert proto.functionParameters == contract_function_result.function_parameters
    assert proto.signer_nonce.value == contract_function_result.signer_nonce
