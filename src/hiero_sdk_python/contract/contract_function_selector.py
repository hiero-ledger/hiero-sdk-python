from enum import IntEnum
from typing import List, NamedTuple, Optional

from hiero_sdk_python.utils.crypto_utils import keccak256

class ArgumentType(IntEnum):
    """Enum for Solidity argument types."""
    UINT8 = 0
    INT8 = 1
    UINT16 = 2
    INT16 = 3
    UINT24 = 4
    INT24 = 5
    UINT32 = 6
    INT32 = 7
    UINT40 = 8
    INT40 = 9
    UINT48 = 10
    INT48 = 11
    UINT56 = 12
    INT56 = 13
    UINT64 = 14
    INT64 = 15
    UINT72 = 16
    INT72 = 17
    UINT80 = 18
    INT80 = 19
    UINT88 = 20
    INT88 = 21
    UINT96 = 22
    INT96 = 23
    UINT104 = 24
    INT104 = 25
    UINT112 = 26
    INT112 = 27
    UINT120 = 28
    INT120 = 29
    UINT128 = 30
    INT128 = 31
    UINT136 = 32
    INT136 = 33
    UINT144 = 34
    INT144 = 35
    UINT152 = 36
    INT152 = 37
    UINT160 = 38
    INT160 = 39
    UINT168 = 40
    INT168 = 41
    UINT176 = 42
    INT176 = 43
    UINT184 = 44
    INT184 = 45
    UINT192 = 46
    INT192 = 47
    UINT200 = 48
    INT200 = 49
    UINT208 = 50
    INT208 = 51
    UINT216 = 52
    INT216 = 53
    UINT224 = 54
    INT224 = 55
    UINT232 = 56
    INT232 = 57
    UINT240 = 58
    INT240 = 59
    UINT248 = 60
    INT248 = 61
    UINT256 = 62
    INT256 = 63
    STRING = 64
    BOOL = 65
    BYTES = 66
    BYTES32 = 67
    ADDRESS = 68
    FUNC = 69


class SolidityType(NamedTuple):
    """Represents a Solidity type with array flag."""
    ty: ArgumentType
    array: bool


class ContractFunctionSelector:
    """
    Class to help construct function selectors for smart contract function calls.
    Function selectors are the first 4 bytes of the Keccak-256 hash of the function's signature.

    This class provides methods to build function signatures by adding parameters of various Solidity types.
    It supports all standard Solidity parameter types and their array variants.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize a ContractFunctionSelector.

        Args:
            name: Optional function name
        """
        self._name: Optional[str] = name
        self._params: str = ""
        self._param_types: List[SolidityType] = []

    def add_string(self) -> 'ContractFunctionSelector':
        """Add a string parameter."""
        return self._add_param(SolidityType(ArgumentType.STRING, False))

    def add_string_array(self) -> 'ContractFunctionSelector':
        """Add a string array parameter."""
        return self._add_param(SolidityType(ArgumentType.STRING, True))

    def add_bytes(self) -> 'ContractFunctionSelector':
        """Add a bytes parameter."""
        return self._add_param(SolidityType(ArgumentType.BYTES, False))

    def add_bytes32(self) -> 'ContractFunctionSelector':
        """Add a bytes32 parameter."""
        return self._add_param(SolidityType(ArgumentType.BYTES32, False))

    def add_bytes_array(self) -> 'ContractFunctionSelector':
        """Add a bytes array parameter."""
        return self._add_param(SolidityType(ArgumentType.BYTES, True))

    def add_bytes32_array(self) -> 'ContractFunctionSelector':
        """Add a bytes32 array parameter."""
        return self._add_param(SolidityType(ArgumentType.BYTES32, True))

    def add_int8(self) -> 'ContractFunctionSelector':
        """Add an int8 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT8, False))

    def add_uint8(self) -> 'ContractFunctionSelector':
        """Add a uint8 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT8, False))

    def add_int16(self) -> 'ContractFunctionSelector':
        """Add an int16 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT16, False))

    def add_uint16(self) -> 'ContractFunctionSelector':
        """Add a uint16 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT16, False))

    def add_int24(self) -> 'ContractFunctionSelector':
        """Add an int24 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT24, False))

    def add_uint24(self) -> 'ContractFunctionSelector':
        """Add a uint24 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT24, False))

    def add_int32(self) -> 'ContractFunctionSelector':
        """Add an int32 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT32, False))

    def add_uint32(self) -> 'ContractFunctionSelector':
        """Add a uint32 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT32, False))

    def add_int40(self) -> 'ContractFunctionSelector':
        """Add an int40 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT40, False))

    def add_uint40(self) -> 'ContractFunctionSelector':
        """Add a uint40 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT40, False))

    def add_int48(self) -> 'ContractFunctionSelector':
        """Add an int48 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT48, False))

    def add_uint48(self) -> 'ContractFunctionSelector':
        """Add a uint48 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT48, False))

    def add_int56(self) -> 'ContractFunctionSelector':
        """Add an int56 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT56, False))

    def add_uint56(self) -> 'ContractFunctionSelector':
        """Add a uint56 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT56, False))

    def add_int64(self) -> 'ContractFunctionSelector':
        """Add an int64 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT64, False))

    def add_uint64(self) -> 'ContractFunctionSelector':
        """Add a uint64 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT64, False))

    def add_int72(self) -> 'ContractFunctionSelector':
        """Add an int72 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT72, False))

    def add_uint72(self) -> 'ContractFunctionSelector':
        """Add a uint72 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT72, False))

    def add_int80(self) -> 'ContractFunctionSelector':
        """Add an int80 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT80, False))

    def add_uint80(self) -> 'ContractFunctionSelector':
        """Add a uint80 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT80, False))

    def add_int88(self) -> 'ContractFunctionSelector':
        """Add an int88 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT88, False))

    def add_uint88(self) -> 'ContractFunctionSelector':
        """Add a uint88 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT88, False))

    def add_int96(self) -> 'ContractFunctionSelector':
        """Add an int96 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT96, False))

    def add_uint96(self) -> 'ContractFunctionSelector':
        """Add a uint96 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT96, False))

    def add_int104(self) -> 'ContractFunctionSelector':
        """Add an int104 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT104, False))

    def add_uint104(self) -> 'ContractFunctionSelector':
        """Add a uint104 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT104, False))

    def add_int112(self) -> 'ContractFunctionSelector':
        """Add an int112 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT112, False))

    def add_uint112(self) -> 'ContractFunctionSelector':
        """Add a uint112 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT112, False))

    def add_int120(self) -> 'ContractFunctionSelector':
        """Add an int120 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT120, False))

    def add_uint120(self) -> 'ContractFunctionSelector':
        """Add a uint120 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT120, False))

    def add_int128(self) -> 'ContractFunctionSelector':
        """Add an int128 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT128, False))

    def add_uint128(self) -> 'ContractFunctionSelector':
        """Add a uint128 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT128, False))

    def add_int136(self) -> 'ContractFunctionSelector':
        """Add an int136 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT136, False))

    def add_uint136(self) -> 'ContractFunctionSelector':
        """Add a uint136 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT136, False))

    def add_int144(self) -> 'ContractFunctionSelector':
        """Add an int144 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT144, False))

    def add_uint144(self) -> 'ContractFunctionSelector':
        """Add a uint144 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT144, False))

    def add_int152(self) -> 'ContractFunctionSelector':
        """Add an int152 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT152, False))

    def add_uint152(self) -> 'ContractFunctionSelector':
        """Add a uint152 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT152, False))

    def add_int160(self) -> 'ContractFunctionSelector':
        """Add an int160 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT160, False))

    def add_uint160(self) -> 'ContractFunctionSelector':
        """Add a uint160 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT160, False))

    def add_int168(self) -> 'ContractFunctionSelector':
        """Add an int168 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT168, False))

    def add_uint168(self) -> 'ContractFunctionSelector':
        """Add a uint168 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT168, False))

    def add_int176(self) -> 'ContractFunctionSelector':
        """Add an int176 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT176, False))

    def add_uint176(self) -> 'ContractFunctionSelector':
        """Add a uint176 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT176, False))

    def add_int184(self) -> 'ContractFunctionSelector':
        """Add an int184 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT184, False))

    def add_uint184(self) -> 'ContractFunctionSelector':
        """Add a uint184 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT184, False))

    def add_int192(self) -> 'ContractFunctionSelector':
        """Add an int192 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT192, False))

    def add_uint192(self) -> 'ContractFunctionSelector':
        """Add a uint192 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT192, False))

    def add_int200(self) -> 'ContractFunctionSelector':
        """Add an int200 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT200, False))

    def add_uint200(self) -> 'ContractFunctionSelector':
        """Add a uint200 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT200, False))

    def add_int208(self) -> 'ContractFunctionSelector':
        """Add an int208 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT208, False))

    def add_uint208(self) -> 'ContractFunctionSelector':
        """Add a uint208 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT208, False))

    def add_int216(self) -> 'ContractFunctionSelector':
        """Add an int216 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT216, False))

    def add_uint216(self) -> 'ContractFunctionSelector':
        """Add a uint216 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT216, False))

    def add_int224(self) -> 'ContractFunctionSelector':
        """Add an int224 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT224, False))

    def add_uint224(self) -> 'ContractFunctionSelector':
        """Add a uint224 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT224, False))

    def add_int232(self) -> 'ContractFunctionSelector':
        """Add an int232 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT232, False))

    def add_uint232(self) -> 'ContractFunctionSelector':
        """Add a uint232 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT232, False))

    def add_int240(self) -> 'ContractFunctionSelector':
        """Add an int240 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT240, False))

    def add_uint240(self) -> 'ContractFunctionSelector':
        """Add a uint240 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT240, False))

    def add_int248(self) -> 'ContractFunctionSelector':
        """Add an int248 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT248, False))

    def add_uint248(self) -> 'ContractFunctionSelector':
        """Add a uint248 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT248, False))

    def add_int256(self) -> 'ContractFunctionSelector':
        """Add an int256 parameter."""
        return self._add_param(SolidityType(ArgumentType.INT256, False))

    def add_uint256(self) -> 'ContractFunctionSelector':
        """Add a uint256 parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT256, False))

    # Array versions for integer types
    def add_int8_array(self) -> 'ContractFunctionSelector':
        """Add an int8 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT8, True))

    def add_uint8_array(self) -> 'ContractFunctionSelector':
        """Add a uint8 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT8, True))

    def add_int16_array(self) -> 'ContractFunctionSelector':
        """Add an int16 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT16, True))

    def add_uint16_array(self) -> 'ContractFunctionSelector':
        """Add a uint16 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT16, True))

    def add_int24_array(self) -> 'ContractFunctionSelector':
        """Add an int24 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT24, True))

    def add_uint24_array(self) -> 'ContractFunctionSelector':
        """Add a uint24 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT24, True))

    def add_int32_array(self) -> 'ContractFunctionSelector':
        """Add an int32 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT32, True))

    def add_uint32_array(self) -> 'ContractFunctionSelector':
        """Add a uint32 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT32, True))

    def add_int40_array(self) -> 'ContractFunctionSelector':
        """Add an int40 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT40, True))

    def add_uint40_array(self) -> 'ContractFunctionSelector':
        """Add a uint40 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT40, True))

    def add_int48_array(self) -> 'ContractFunctionSelector':
        """Add an int48 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT48, True))

    def add_uint48_array(self) -> 'ContractFunctionSelector':
        """Add a uint48 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT48, True))

    def add_int56_array(self) -> 'ContractFunctionSelector':
        """Add an int56 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT56, True))

    def add_uint56_array(self) -> 'ContractFunctionSelector':
        """Add a uint56 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT56, True))

    def add_int64_array(self) -> 'ContractFunctionSelector':
        """Add an int64 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT64, True))

    def add_uint64_array(self) -> 'ContractFunctionSelector':
        """Add a uint64 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT64, True))

    def add_int72_array(self) -> 'ContractFunctionSelector':
        """Add an int72 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT72, True))

    def add_uint72_array(self) -> 'ContractFunctionSelector':
        """Add a uint72 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT72, True))

    def add_int80_array(self) -> 'ContractFunctionSelector':
        """Add an int80 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT80, True))

    def add_uint80_array(self) -> 'ContractFunctionSelector':
        """Add a uint80 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT80, True))

    def add_int88_array(self) -> 'ContractFunctionSelector':
        """Add an int88 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT88, True))

    def add_uint88_array(self) -> 'ContractFunctionSelector':
        """Add a uint88 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT88, True))

    def add_int96_array(self) -> 'ContractFunctionSelector':
        """Add an int96 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT96, True))

    def add_uint96_array(self) -> 'ContractFunctionSelector':
        """Add a uint96 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT96, True))

    def add_int104_array(self) -> 'ContractFunctionSelector':
        """Add an int104 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT104, True))

    def add_uint104_array(self) -> 'ContractFunctionSelector':
        """Add a uint104 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT104, True))

    def add_int112_array(self) -> 'ContractFunctionSelector':
        """Add an int112 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT112, True))

    def add_uint112_array(self) -> 'ContractFunctionSelector':
        """Add a uint112 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT112, True))

    def add_int120_array(self) -> 'ContractFunctionSelector':
        """Add an int120 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT120, True))

    def add_uint120_array(self) -> 'ContractFunctionSelector':
        """Add a uint120 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT120, True))

    def add_int128_array(self) -> 'ContractFunctionSelector':
        """Add an int128 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT128, True))

    def add_uint128_array(self) -> 'ContractFunctionSelector':
        """Add a uint128 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT128, True))

    def add_int136_array(self) -> 'ContractFunctionSelector':
        """Add an int136 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT136, True))

    def add_uint136_array(self) -> 'ContractFunctionSelector':
        """Add a uint136 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT136, True))

    def add_int144_array(self) -> 'ContractFunctionSelector':
        """Add an int144 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT144, True))

    def add_uint144_array(self) -> 'ContractFunctionSelector':
        """Add a uint144 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT144, True))

    def add_int152_array(self) -> 'ContractFunctionSelector':
        """Add an int152 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT152, True))

    def add_uint152_array(self) -> 'ContractFunctionSelector':
        """Add a uint152 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT152, True))

    def add_int160_array(self) -> 'ContractFunctionSelector':
        """Add an int160 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT160, True))

    def add_uint160_array(self) -> 'ContractFunctionSelector':
        """Add a uint160 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT160, True))

    def add_int168_array(self) -> 'ContractFunctionSelector':
        """Add an int168 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT168, True))

    def add_uint168_array(self) -> 'ContractFunctionSelector':
        """Add a uint168 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT168, True))

    def add_int176_array(self) -> 'ContractFunctionSelector':
        """Add an int176 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT176, True))

    def add_uint176_array(self) -> 'ContractFunctionSelector':
        """Add a uint176 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT176, True))

    def add_int184_array(self) -> 'ContractFunctionSelector':
        """Add an int184 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT184, True))

    def add_uint184_array(self) -> 'ContractFunctionSelector':
        """Add a uint184 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT184, True))

    def add_int192_array(self) -> 'ContractFunctionSelector':
        """Add an int192 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT192, True))

    def add_uint192_array(self) -> 'ContractFunctionSelector':
        """Add a uint192 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT192, True))

    def add_int200_array(self) -> 'ContractFunctionSelector':
        """Add an int200 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT200, True))

    def add_uint200_array(self) -> 'ContractFunctionSelector':
        """Add a uint200 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT200, True))

    def add_int208_array(self) -> 'ContractFunctionSelector':
        """Add an int208 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT208, True))

    def add_uint208_array(self) -> 'ContractFunctionSelector':
        """Add a uint208 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT208, True))

    def add_int216_array(self) -> 'ContractFunctionSelector':
        """Add an int216 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT216, True))

    def add_uint216_array(self) -> 'ContractFunctionSelector':
        """Add a uint216 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT216, True))

    def add_int224_array(self) -> 'ContractFunctionSelector':
        """Add an int224 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT224, True))

    def add_uint224_array(self) -> 'ContractFunctionSelector':
        """Add a uint224 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT224, True))

    def add_int232_array(self) -> 'ContractFunctionSelector':
        """Add an int232 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT232, True))

    def add_uint232_array(self) -> 'ContractFunctionSelector':
        """Add a uint232 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT232, True))

    def add_int240_array(self) -> 'ContractFunctionSelector':
        """Add an int240 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT240, True))

    def add_uint240_array(self) -> 'ContractFunctionSelector':
        """Add a uint240 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT240, True))

    def add_int248_array(self) -> 'ContractFunctionSelector':
        """Add an int248 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT248, True))

    def add_uint248_array(self) -> 'ContractFunctionSelector':
        """Add a uint248 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT248, True))

    def add_int256_array(self) -> 'ContractFunctionSelector':
        """Add an int256 array parameter."""
        return self._add_param(SolidityType(ArgumentType.INT256, True))

    def add_uint256_array(self) -> 'ContractFunctionSelector':
        """Add a uint256 array parameter."""
        return self._add_param(SolidityType(ArgumentType.UINT256, True))

    def add_bool(self) -> 'ContractFunctionSelector':
        """Add a bool parameter."""
        return self._add_param(SolidityType(ArgumentType.BOOL, False))

    def add_address(self) -> 'ContractFunctionSelector':
        """Add an address parameter."""
        return self._add_param(SolidityType(ArgumentType.ADDRESS, False))

    def add_address_array(self) -> 'ContractFunctionSelector':
        """Add an address array parameter."""
        return self._add_param(SolidityType(ArgumentType.ADDRESS, True))

    def add_function(self) -> 'ContractFunctionSelector':
        """Add a function parameter."""
        return self._add_param(SolidityType(ArgumentType.FUNC, False))

    def _add_param(self, ty: SolidityType) -> 'ContractFunctionSelector':
        """Add a parameter to the function signature."""
        if len(self._param_types) > 0:
            self._params += ","

        self._params += solidity_type_to_string(ty)
        self._param_types.append(ty)

        return self

    def build(self, name: Optional[str] = None) -> bytes:
        """
        Build the function selector.

        Args:
            name: Optional function name to use

        Returns:
            The first 4 bytes of the Keccak-256 hash of the function signature

        Raises:
            ValueError: If no name is provided and none was set in constructor
        """
        if name is not None:
            self._name = name
        elif self._name is None:
            raise ValueError("Function name is required for ContractFunctionSelector")

        func_signature = str(self)
        func_bytes = func_signature.encode('utf-8')
        
        # Calculate Keccak-256 hash
        hash_bytes = keccak256(func_bytes)
        # Return first 4 bytes
        return hash_bytes[:4]

    def __str__(self) -> str:
        """Return the function signature string."""
        name = self._name if self._name is not None else ""
        return f"{name}({self._params})"


def solidity_type_to_string(ty: SolidityType) -> str:
    """
    Convert a SolidityType to its string representation.

    Args:
        ty: The SolidityType to convert

    Returns:
        String representation of the Solidity type
    """
    type_map = {
        ArgumentType.UINT8: "uint8",
        ArgumentType.INT8: "int8",
        ArgumentType.UINT16: "uint16",
        ArgumentType.INT16: "int16",
        ArgumentType.UINT24: "uint24",
        ArgumentType.INT24: "int24",
        ArgumentType.UINT32: "uint32",
        ArgumentType.INT32: "int32",
        ArgumentType.UINT40: "uint40",
        ArgumentType.INT40: "int40",
        ArgumentType.UINT48: "uint48",
        ArgumentType.INT48: "int48",
        ArgumentType.UINT56: "uint56",
        ArgumentType.INT56: "int56",
        ArgumentType.UINT64: "uint64",
        ArgumentType.INT64: "int64",
        ArgumentType.UINT72: "uint72",
        ArgumentType.INT72: "int72",
        ArgumentType.UINT80: "uint80",
        ArgumentType.INT80: "int80",
        ArgumentType.UINT88: "uint88",
        ArgumentType.INT88: "int88",
        ArgumentType.UINT96: "uint96",
        ArgumentType.INT96: "int96",
        ArgumentType.UINT104: "uint104",
        ArgumentType.INT104: "int104",
        ArgumentType.UINT112: "uint112",
        ArgumentType.INT112: "int112",
        ArgumentType.UINT120: "uint120",
        ArgumentType.INT120: "int120",
        ArgumentType.UINT128: "uint128",
        ArgumentType.INT128: "int128",
        ArgumentType.UINT136: "uint136",
        ArgumentType.INT136: "int136",
        ArgumentType.UINT144: "uint144",
        ArgumentType.INT144: "int144",
        ArgumentType.UINT152: "uint152",
        ArgumentType.INT152: "int152",
        ArgumentType.UINT160: "uint160",
        ArgumentType.INT160: "int160",
        ArgumentType.UINT168: "uint168",
        ArgumentType.INT168: "int168",
        ArgumentType.UINT176: "uint176",
        ArgumentType.INT176: "int176",
        ArgumentType.UINT184: "uint184",
        ArgumentType.INT184: "int184",
        ArgumentType.UINT192: "uint192",
        ArgumentType.INT192: "int192",
        ArgumentType.UINT200: "uint200",
        ArgumentType.INT200: "int200",
        ArgumentType.UINT208: "uint208",
        ArgumentType.INT208: "int208",
        ArgumentType.UINT216: "uint216",
        ArgumentType.INT216: "int216",
        ArgumentType.UINT224: "uint224",
        ArgumentType.INT224: "int224",
        ArgumentType.UINT232: "uint232",
        ArgumentType.INT232: "int232",
        ArgumentType.UINT240: "uint240",
        ArgumentType.INT240: "int240",
        ArgumentType.UINT248: "uint248",
        ArgumentType.INT248: "int248",
        ArgumentType.UINT256: "uint256",
        ArgumentType.INT256: "int256",
        ArgumentType.STRING: "string",
        ArgumentType.BOOL: "bool",
        ArgumentType.BYTES: "bytes",
        ArgumentType.BYTES32: "bytes32",
        ArgumentType.ADDRESS: "address",
        ArgumentType.FUNC: "function",
    }
    
    s = type_map.get(ty.ty, "")
    
    if ty.array:
        s += "[]"
    
    return s
