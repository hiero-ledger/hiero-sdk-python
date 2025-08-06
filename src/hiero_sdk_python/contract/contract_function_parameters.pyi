# pylint: disable=[too-many-lines]
"""
ContractFunctionParameters Type Stub File

This module provides comprehensive type hints for the ContractFunctionParameters class,
which handles Ethereum ABI encoding for smart contract function calls.

Key Features:
- Supports all Solidity parameter types (bool, address, string, bytes, int8-256, uint8-256)
- Array support for all basic types
- Function selector generation
- ABI-compliant parameter encoding
- Method chaining for fluent API
"""

from typing import Any, List, Optional, Union

class ContractFunctionParameters:
    """
    A simplified contract function interface using eth-abi for parameter encoding.
    This stub file provides type hints for the ContractFunctionParameters class to enable
    dynamic type checking and IDE support.
    """

    function_name: Optional[str]
    _types: List[str]
    _values: List[Any]

    def __init__(self, function_name: Optional[str] = None) -> None:
        """
        Initialize a new ContractFunctionParameters instance.

        Args:
            function_name: Optional function name to use for the function selector
        """

    def _add_param(self, type_name: str, value: Any) -> "ContractFunctionParameters":
        """
        Internal helper to add a parameter.

        Args:
            type_name: The Solidity type name
            value: The value to add

        Returns:
            This instance for method chaining
        """
    # Explicitly defined methods
    def add_bool(self, value: bool) -> "ContractFunctionParameters":
        """
        Add a boolean parameter.

        Args:
            value: The boolean value to add

        Returns:
            This instance for method chaining
        """

    def add_address(self, value: Union[str, bytes]) -> "ContractFunctionParameters":
        """
        Add an address parameter.

        Args:
            value: The address as a hex string (with or without 0x prefix) or bytes

        Returns:
            This instance for method chaining
        """

    def add_string(self, value: str) -> "ContractFunctionParameters":
        """
        Add a string parameter.

        Args:
            value: The string value to add

        Returns:
            This instance for method chaining
        """

    def add_bytes(self, value: bytes) -> "ContractFunctionParameters":
        """
        Add a bytes parameter.

        Args:
            value: The bytes value to add

        Returns:
            This instance for method chaining
        """

    def add_bytes32(self, value: bytes) -> "ContractFunctionParameters":
        """
        Add a bytes32 parameter.

        Args:
            value: The bytes value to add, must be exactly 32 bytes long

        Returns:
            This instance for method chaining

        Raises:
            ValueError: If value is not exactly 32 bytes
            TypeError: If value is not bytes type
        """
    # Array methods for basic types
    def add_bool_array(self, value: List[bool]) -> "ContractFunctionParameters":
        """
        Add a boolean array parameter.

        Args:
            value: The boolean array to add

        Returns:
            This instance for method chaining
        """

    def add_address_array(
        self, value: List[Union[str, bytes]]
    ) -> "ContractFunctionParameters":
        """
        Add an address array parameter.

        Args:
            value: The address array to add, each can be hex string or bytes

        Returns:
            This instance for method chaining
        """

    def add_string_array(self, value: List[str]) -> "ContractFunctionParameters":
        """
        Add a string array parameter.

        Args:
            value: The string array to add

        Returns:
            This instance for method chaining
        """

    def add_bytes_array(self, value: List[bytes]) -> "ContractFunctionParameters":
        """
        Add a bytes array parameter.

        Args:
            value: The bytes array to add

        Returns:
            This instance for method chaining
        """

    def add_bytes32_array(self, value: List[bytes]) -> "ContractFunctionParameters":
        """
        Add a bytes32 array parameter.

        Args:
            value: The bytes32 array to add, each element must be exactly 32 bytes

        Returns:
            This instance for method chaining
        """

    def get_function_selector(self) -> bytes:
        """
        Get the function selector (first 4 bytes of the keccak256 hash of the function signature).

        Returns:
            The function selector as bytes

        Raises:
            ValueError: If no function name was provided
        """

    def encode_parameters(self) -> bytes:
        """
        Encode the parameters according to the Ethereum ABI spec.

        Returns:
            The ABI-encoded parameter bytes (without the function selector)

        Raises:
            Exception: If there is an error encoding the parameters
        """

    def to_bytes(self) -> bytes:
        """
        Get the full encoded function call including selector and parameters.

        Returns:
            The complete function call data as bytes

        Raises:
            ValueError: If no function name was provided
            Exception: If there is an error encoding the parameters
        """

    def __bytes__(self) -> bytes:
        """Allow conversion to bytes using bytes() function."""

    def clear(self) -> "ContractFunctionParameters":
        """
        Clear all parameters.

        Returns:
            This instance for method chaining
        """
    # Comprehensive integer type support (int8-256, uint8-256)
    # Each type has its own method for explicit type checking and IDE support
    def add_int8(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int8 parameter.

        Args:
            value: The int8 value to add

        Returns:
            This instance for method chaining
        """

    def add_int16(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int16 parameter.

        Args:
            value: The int16 value to add

        Returns:
            This instance for method chaining
        """

    def add_int24(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int24 parameter.

        Args:
            value: The int24 value to add

        Returns:
            This instance for method chaining
        """

    def add_int32(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int32 parameter.

        Args:
            value: The int32 value to add

        Returns:
            This instance for method chaining
        """

    def add_int40(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int40 parameter.

        Args:
            value: The int40 value to add

        Returns:
            This instance for method chaining
        """

    def add_int48(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int48 parameter.

        Args:
            value: The int48 value to add

        Returns:
            This instance for method chaining
        """

    def add_int56(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int56 parameter.

        Args:
            value: The int56 value to add

        Returns:
            This instance for method chaining
        """

    def add_int64(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int64 parameter.

        Args:
            value: The int64 value to add

        Returns:
            This instance for method chaining
        """

    def add_int72(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int72 parameter.

        Args:
            value: The int72 value to add

        Returns:
            This instance for method chaining
        """

    def add_int80(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int80 parameter.

        Args:
            value: The int80 value to add

        Returns:
            This instance for method chaining
        """

    def add_int88(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int88 parameter.

        Args:
            value: The int88 value to add

        Returns:
            This instance for method chaining
        """

    def add_int96(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int96 parameter.

        Args:
            value: The int96 value to add

        Returns:
            This instance for method chaining
        """

    def add_int104(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int104 parameter.

        Args:
            value: The int104 value to add

        Returns:
            This instance for method chaining
        """

    def add_int112(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int112 parameter.

        Args:
            value: The int112 value to add

        Returns:
            This instance for method chaining
        """

    def add_int120(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int120 parameter.

        Args:
            value: The int120 value to add

        Returns:
            This instance for method chaining
        """

    def add_int128(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int128 parameter.

        Args:
            value: The int128 value to add

        Returns:
            This instance for method chaining
        """

    def add_int136(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int136 parameter.

        Args:
            value: The int136 value to add

        Returns:
            This instance for method chaining
        """

    def add_int144(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int144 parameter.

        Args:
            value: The int144 value to add

        Returns:
            This instance for method chaining
        """

    def add_int152(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int152 parameter.

        Args:
            value: The int152 value to add

        Returns:
            This instance for method chaining
        """

    def add_int160(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int160 parameter.

        Args:
            value: The int160 value to add

        Returns:
            This instance for method chaining
        """

    def add_int168(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int168 parameter.

        Args:
            value: The int168 value to add

        Returns:
            This instance for method chaining
        """

    def add_int176(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int176 parameter.

        Args:
            value: The int176 value to add

        Returns:
            This instance for method chaining
        """

    def add_int184(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int184 parameter.

        Args:
            value: The int184 value to add

        Returns:
            This instance for method chaining
        """

    def add_int192(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int192 parameter.

        Args:
            value: The int192 value to add

        Returns:
            This instance for method chaining
        """

    def add_int200(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int200 parameter.

        Args:
            value: The int200 value to add

        Returns:
            This instance for method chaining
        """

    def add_int208(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int208 parameter.

        Args:
            value: The int208 value to add

        Returns:
            This instance for method chaining
        """

    def add_int216(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int216 parameter.

        Args:
            value: The int216 value to add

        Returns:
            This instance for method chaining
        """

    def add_int224(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int224 parameter.

        Args:
            value: The int224 value to add

        Returns:
            This instance for method chaining
        """

    def add_int232(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int232 parameter.

        Args:
            value: The int232 value to add

        Returns:
            This instance for method chaining
        """

    def add_int240(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int240 parameter.

        Args:
            value: The int240 value to add

        Returns:
            This instance for method chaining
        """

    def add_int248(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int248 parameter.

        Args:
            value: The int248 value to add

        Returns:
            This instance for method chaining
        """

    def add_int256(self, value: int) -> "ContractFunctionParameters":
        """
        Add an int256 parameter.

        Args:
            value: The int256 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint8(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint8 parameter.

        Args:
            value: The uint8 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint16(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint16 parameter.

        Args:
            value: The uint16 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint24(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint24 parameter.

        Args:
            value: The uint24 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint32(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint32 parameter.

        Args:
            value: The uint32 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint40(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint40 parameter.

        Args:
            value: The uint40 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint48(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint48 parameter.

        Args:
            value: The uint48 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint56(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint56 parameter.

        Args:
            value: The uint56 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint64(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint64 parameter.

        Args:
            value: The uint64 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint72(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint72 parameter.

        Args:
            value: The uint72 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint80(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint80 parameter.

        Args:
            value: The uint80 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint88(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint88 parameter.

        Args:
            value: The uint88 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint96(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint96 parameter.

        Args:
            value: The uint96 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint104(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint104 parameter.

        Args:
            value: The uint104 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint112(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint112 parameter.

        Args:
            value: The uint112 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint120(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint120 parameter.

        Args:
            value: The uint120 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint128(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint128 parameter.

        Args:
            value: The uint128 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint136(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint136 parameter.

        Args:
            value: The uint136 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint144(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint144 parameter.

        Args:
            value: The uint144 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint152(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint152 parameter.

        Args:
            value: The uint152 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint160(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint160 parameter.

        Args:
            value: The uint160 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint168(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint168 parameter.

        Args:
            value: The uint168 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint176(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint176 parameter.

        Args:
            value: The uint176 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint184(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint184 parameter.

        Args:
            value: The uint184 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint192(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint192 parameter.

        Args:
            value: The uint192 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint200(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint200 parameter.

        Args:
            value: The uint200 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint208(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint208 parameter.

        Args:
            value: The uint208 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint216(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint216 parameter.

        Args:
            value: The uint216 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint224(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint224 parameter.

        Args:
            value: The uint224 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint232(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint232 parameter.

        Args:
            value: The uint232 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint240(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint240 parameter.

        Args:
            value: The uint240 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint248(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint248 parameter.

        Args:
            value: The uint248 value to add

        Returns:
            This instance for method chaining
        """

    def add_uint256(self, value: int) -> "ContractFunctionParameters":
        """
        Add a uint256 parameter.

        Args:
            value: The uint256 value to add

        Returns:
            This instance for method chaining
        """

    def add_int8_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int8 array parameter.

        Args:
            value: The int8 array to add

        Returns:
            This instance for method chaining
        """

    def add_int16_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int16 array parameter.

        Args:
            value: The int16 array to add

        Returns:
            This instance for method chaining
        """

    def add_int24_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int24 array parameter.

        Args:
            value: The int24 array to add

        Returns:
            This instance for method chaining
        """

    def add_int32_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int32 array parameter.

        Args:
            value: The int32 array to add

        Returns:
            This instance for method chaining
        """

    def add_int40_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int40 array parameter.

        Args:
            value: The int40 array to add

        Returns:
            This instance for method chaining
        """

    def add_int48_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int48 array parameter.

        Args:
            value: The int48 array to add

        Returns:
            This instance for method chaining
        """

    def add_int56_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int56 array parameter.

        Args:
            value: The int56 array to add

        Returns:
            This instance for method chaining
        """

    def add_int64_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int64 array parameter.

        Args:
            value: The int64 array to add

        Returns:
            This instance for method chaining
        """

    def add_int72_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int72 array parameter.

        Args:
            value: The int72 array to add

        Returns:
            This instance for method chaining
        """

    def add_int80_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int80 array parameter.

        Args:
            value: The int80 array to add

        Returns:
            This instance for method chaining
        """

    def add_int88_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int88 array parameter.

        Args:
            value: The int88 array to add

        Returns:
            This instance for method chaining
        """

    def add_int96_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int96 array parameter.

        Args:
            value: The int96 array to add

        Returns:
            This instance for method chaining
        """

    def add_int104_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int104 array parameter.

        Args:
            value: The int104 array to add

        Returns:
            This instance for method chaining
        """

    def add_int112_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int112 array parameter.

        Args:
            value: The int112 array to add

        Returns:
            This instance for method chaining
        """

    def add_int120_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int120 array parameter.

        Args:
            value: The int120 array to add

        Returns:
            This instance for method chaining
        """

    def add_int128_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int128 array parameter.

        Args:
            value: The int128 array to add

        Returns:
            This instance for method chaining
        """

    def add_int136_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int136 array parameter.

        Args:
            value: The int136 array to add

        Returns:
            This instance for method chaining
        """

    def add_int144_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int144 array parameter.

        Args:
            value: The int144 array to add

        Returns:
            This instance for method chaining
        """

    def add_int152_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int152 array parameter.

        Args:
            value: The int152 array to add

        Returns:
            This instance for method chaining
        """

    def add_int160_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int160 array parameter.

        Args:
            value: The int160 array to add

        Returns:
            This instance for method chaining
        """

    def add_int168_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int168 array parameter.

        Args:
            value: The int168 array to add

        Returns:
            This instance for method chaining
        """

    def add_int176_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int176 array parameter.

        Args:
            value: The int176 array to add

        Returns:
            This instance for method chaining
        """

    def add_int184_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int184 array parameter.

        Args:
            value: The int184 array to add

        Returns:
            This instance for method chaining
        """

    def add_int192_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int192 array parameter.

        Args:
            value: The int192 array to add

        Returns:
            This instance for method chaining
        """

    def add_int200_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int200 array parameter.

        Args:
            value: The int200 array to add

        Returns:
            This instance for method chaining
        """

    def add_int208_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int208 array parameter.

        Args:
            value: The int208 array to add

        Returns:
            This instance for method chaining
        """

    def add_int216_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int216 array parameter.

        Args:
            value: The int216 array to add

        Returns:
            This instance for method chaining
        """

    def add_int224_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int224 array parameter.

        Args:
            value: The int224 array to add

        Returns:
            This instance for method chaining
        """

    def add_int232_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int232 array parameter.

        Args:
            value: The int232 array to add

        Returns:
            This instance for method chaining
        """

    def add_int240_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int240 array parameter.

        Args:
            value: The int240 array to add

        Returns:
            This instance for method chaining
        """

    def add_int248_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int248 array parameter.

        Args:
            value: The int248 array to add

        Returns:
            This instance for method chaining
        """

    def add_int256_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add an int256 array parameter.

        Args:
            value: The int256 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint8_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint8 array parameter.

        Args:
            value: The uint8 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint16_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint16 array parameter.

        Args:
            value: The uint16 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint24_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint24 array parameter.

        Args:
            value: The uint24 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint32_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint32 array parameter.

        Args:
            value: The uint32 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint40_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint40 array parameter.

        Args:
            value: The uint40 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint48_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint48 array parameter.

        Args:
            value: The uint48 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint56_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint56 array parameter.

        Args:
            value: The uint56 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint64_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint64 array parameter.

        Args:
            value: The uint64 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint72_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint72 array parameter.

        Args:
            value: The uint72 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint80_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint80 array parameter.

        Args:
            value: The uint80 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint88_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint88 array parameter.

        Args:
            value: The uint88 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint96_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint96 array parameter.

        Args:
            value: The uint96 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint104_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint104 array parameter.

        Args:
            value: The uint104 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint112_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint112 array parameter.

        Args:
            value: The uint112 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint120_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint120 array parameter.

        Args:
            value: The uint120 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint128_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint128 array parameter.

        Args:
            value: The uint128 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint136_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint136 array parameter.

        Args:
            value: The uint136 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint144_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint144 array parameter.

        Args:
            value: The uint144 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint152_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint152 array parameter.

        Args:
            value: The uint152 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint160_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint160 array parameter.

        Args:
            value: The uint160 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint168_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint168 array parameter.

        Args:
            value: The uint168 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint176_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint176 array parameter.

        Args:
            value: The uint176 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint184_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint184 array parameter.

        Args:
            value: The uint184 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint192_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint192 array parameter.

        Args:
            value: The uint192 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint200_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint200 array parameter.

        Args:
            value: The uint200 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint208_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint208 array parameter.

        Args:
            value: The uint208 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint216_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint216 array parameter.

        Args:
            value: The uint216 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint224_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint224 array parameter.

        Args:
            value: The uint224 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint232_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint232 array parameter.

        Args:
            value: The uint232 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint240_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint240 array parameter.

        Args:
            value: The uint240 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint248_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint248 array parameter.

        Args:
            value: The uint248 array to add

        Returns:
            This instance for method chaining
        """

    def add_uint256_array(self, value: List[int]) -> "ContractFunctionParameters":
        """
        Add a uint256 array parameter.

        Args:
            value: The uint256 array to add

        Returns:
            This instance for method chaining
        """
