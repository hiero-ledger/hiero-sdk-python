import struct
from typing import Union, Optional, Any
from hiero_sdk_python.contract.contract_function_selector import ContractFunctionSelector, ArgumentType


class ContractFunctionParameters:
    """
    Class to help construct parameters for a smart contract function call.
    
    This class provides methods to add different types of parameters that will be passed to a smart contract function.
    It supports all Solidity parameter types including basic types (uint/int of various sizes, bool, address),
    arrays, strings, and bytes.
    """

    def __init__(self):
        """Initialize a new ContractFunctionParameters instance."""
        self._selector = ContractFunctionSelector()
        self._arguments: list[dict] = []

    def add_string(self, value: str) -> 'ContractFunctionParameters':
        """
        Add a string parameter.
        
        Args:
            value: The string value to add
            
        Returns:
            This instance for method chaining
        """
        self._selector.add_string()
        return self._add_param(value, True)

    def add_string_array(self, value: list[str]) -> 'ContractFunctionParameters':
        """
        Add a string array parameter.
        
        Args:
            value: The string array to add
            
        Returns:
            This instance for method chaining
        """
        self._selector.add_string_array()
        return self._add_param(value, True)

    def add_bytes(self, value: bytes) -> 'ContractFunctionParameters':
        """
        Add a bytes parameter.
        
        Args:
            value: The bytes value to add
            
        Returns:
            This instance for method chaining
        """
        self._selector.add_bytes()
        return self._add_param(value, True)

    def add_bytes32(self, value: Union[bytes, str]) -> 'ContractFunctionParameters':
        """
        Add a bytes32 parameter.
        
        Args:
            value: The bytes32 value as bytes or hex string
            
        Returns:
            This instance for method chaining
        """
        if isinstance(value, str):
            if value.startswith('0x'):
                value = value[2:]
            if len(value) != 64:
                raise ValueError("bytes32 hex string must be 64 characters")
            try:
                value = bytes.fromhex(value)
            except ValueError:
                raise ValueError("bytes32 must be valid hex string")
        
        if len(value) != 32:
            raise ValueError(f"addBytes32 expected array to be of length 32, but received {len(value)}")
        
        self._selector.add_bytes32()
        return self._add_param(value, False)

    def add_bytes_array(self, value: list[bytes]) -> 'ContractFunctionParameters':
        """
        Add a bytes array parameter.
        
        Args:
            value: The bytes array to add
            
        Returns:
            This instance for method chaining
        """
        self._selector.add_bytes_array()
        return self._add_param(value, True)

    def add_bytes32_array(self, value: list[Union[bytes, str]]) -> 'ContractFunctionParameters':
        """
        Add a bytes32 array parameter.
        
        Args:
            value: The bytes32 array to add
            
        Returns:
            This instance for method chaining
        """
        processed_values = []
        for entry in value:
            if isinstance(entry, str):
                if entry.startswith('0x'):
                    entry = entry[2:]
                if len(entry) != 64:
                    raise ValueError("bytes32 hex string must be 64 characters")
                entry = bytes.fromhex(entry)
            
            if len(entry) != 32:
                raise ValueError(f"addBytes32 expected array to be of length 32, but received {len(entry)}")
            processed_values.append(entry)
        
        self._selector.add_bytes32_array()
        return self._add_param(processed_values, True)

    def add_bool(self, value: bool) -> 'ContractFunctionParameters':
        """
        Add a boolean parameter.
        
        Args:
            value: The boolean value to add
            
        Returns:
            This instance for method chaining
        """
        self._selector.add_bool()
        return self._add_param(value, False)



    # Integer type methods
    def add_int8(self, value: int) -> 'ContractFunctionParameters':
        """Add an int8 parameter."""
        self._selector.add_int8()
        return self._add_param(value, False)

    def add_uint8(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint8 parameter."""
        self._selector.add_uint8()
        return self._add_param(value, False)

    def add_int16(self, value: int) -> 'ContractFunctionParameters':
        """Add an int16 parameter."""
        self._selector.add_int16()
        return self._add_param(value, False)

    def add_uint16(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint16 parameter."""
        self._selector.add_uint16()
        return self._add_param(value, False)

    def add_int24(self, value: int) -> 'ContractFunctionParameters':
        """Add an int24 parameter."""
        self._selector.add_int24()
        return self._add_param(value, False)

    def add_uint24(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint24 parameter."""
        self._selector.add_uint24()
        return self._add_param(value, False)

    def add_int32(self, value: int) -> 'ContractFunctionParameters':
        """Add an int32 parameter."""
        self._selector.add_int32()
        return self._add_param(value, False)

    def add_uint32(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint32 parameter."""
        self._selector.add_uint32()
        return self._add_param(value, False)

    def add_int40(self, value: int) -> 'ContractFunctionParameters':
        """Add an int40 parameter."""
        self._selector.add_int40()
        return self._add_param(value, False)

    def add_uint40(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint40 parameter."""
        self._selector.add_uint40()
        return self._add_param(value, False)

    def add_int48(self, value: int) -> 'ContractFunctionParameters':
        """Add an int48 parameter."""
        self._selector.add_int48()
        return self._add_param(value, False)

    def add_uint48(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint48 parameter."""
        self._selector.add_uint48()
        return self._add_param(value, False)

    def add_int56(self, value: int) -> 'ContractFunctionParameters':
        """Add an int56 parameter."""
        self._selector.add_int56()
        return self._add_param(value, False)

    def add_uint56(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint56 parameter."""
        self._selector.add_uint56()
        return self._add_param(value, False)

    def add_int64(self, value: int) -> 'ContractFunctionParameters':
        """Add an int64 parameter."""
        self._selector.add_int64()
        return self._add_param(value, False)

    def add_uint64(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint64 parameter."""
        self._selector.add_uint64()
        return self._add_param(value, False)

    def add_int72(self, value: int) -> 'ContractFunctionParameters':
        """Add an int72 parameter."""
        self._selector.add_int72()
        return self._add_param(value, False)

    def add_uint72(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint72 parameter."""
        self._selector.add_uint72()
        return self._add_param(value, False)

    def add_int80(self, value: int) -> 'ContractFunctionParameters':
        """Add an int80 parameter."""
        self._selector.add_int80()
        return self._add_param(value, False)

    def add_uint80(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint80 parameter."""
        self._selector.add_uint80()
        return self._add_param(value, False)

    def add_int88(self, value: int) -> 'ContractFunctionParameters':
        """Add an int88 parameter."""
        self._selector.add_int88()
        return self._add_param(value, False)

    def add_uint88(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint88 parameter."""
        self._selector.add_uint88()
        return self._add_param(value, False)

    def add_int96(self, value: int) -> 'ContractFunctionParameters':
        """Add an int96 parameter."""
        self._selector.add_int96()
        return self._add_param(value, False)

    def add_uint96(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint96 parameter."""
        self._selector.add_uint96()
        return self._add_param(value, False)

    def add_int104(self, value: int) -> 'ContractFunctionParameters':
        """Add an int104 parameter."""
        self._selector.add_int104()
        return self._add_param(value, False)

    def add_uint104(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint104 parameter."""
        self._selector.add_uint104()
        return self._add_param(value, False)

    def add_int112(self, value: int) -> 'ContractFunctionParameters':
        """Add an int112 parameter."""
        self._selector.add_int112()
        return self._add_param(value, False)

    def add_uint112(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint112 parameter."""
        self._selector.add_uint112()
        return self._add_param(value, False)

    def add_int120(self, value: int) -> 'ContractFunctionParameters':
        """Add an int120 parameter."""
        self._selector.add_int120()
        return self._add_param(value, False)

    def add_uint120(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint120 parameter."""
        self._selector.add_uint120()
        return self._add_param(value, False)

    def add_int128(self, value: int) -> 'ContractFunctionParameters':
        """Add an int128 parameter."""
        self._selector.add_int128()
        return self._add_param(value, False)

    def add_uint128(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint128 parameter."""
        self._selector.add_uint128()
        return self._add_param(value, False)

    def add_int136(self, value: int) -> 'ContractFunctionParameters':
        """Add an int136 parameter."""
        self._selector.add_int136()
        return self._add_param(value, False)

    def add_uint136(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint136 parameter."""
        self._selector.add_uint136()
        return self._add_param(value, False)

    def add_int144(self, value: int) -> 'ContractFunctionParameters':
        """Add an int144 parameter."""
        self._selector.add_int144()
        return self._add_param(value, False)

    def add_uint144(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint144 parameter."""
        self._selector.add_uint144()
        return self._add_param(value, False)

    def add_int152(self, value: int) -> 'ContractFunctionParameters':
        """Add an int152 parameter."""
        self._selector.add_int152()
        return self._add_param(value, False)

    def add_uint152(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint152 parameter."""
        self._selector.add_uint152()
        return self._add_param(value, False)

    def add_int160(self, value: int) -> 'ContractFunctionParameters':
        """Add an int160 parameter."""
        self._selector.add_int160()
        return self._add_param(value, False)

    def add_uint160(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint160 parameter."""
        self._selector.add_uint160()
        return self._add_param(value, False)

    def add_int168(self, value: int) -> 'ContractFunctionParameters':
        """Add an int168 parameter."""
        self._selector.add_int168()
        return self._add_param(value, False)

    def add_uint168(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint168 parameter."""
        self._selector.add_uint168()
        return self._add_param(value, False)

    def add_int176(self, value: int) -> 'ContractFunctionParameters':
        """Add an int176 parameter."""
        self._selector.add_int176()
        return self._add_param(value, False)

    def add_uint176(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint176 parameter."""
        self._selector.add_uint176()
        return self._add_param(value, False)

    def add_int184(self, value: int) -> 'ContractFunctionParameters':
        """Add an int184 parameter."""
        self._selector.add_int184()
        return self._add_param(value, False)

    def add_uint184(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint184 parameter."""
        self._selector.add_uint184()
        return self._add_param(value, False)

    def add_int192(self, value: int) -> 'ContractFunctionParameters':
        """Add an int192 parameter."""
        self._selector.add_int192()
        return self._add_param(value, False)

    def add_uint192(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint192 parameter."""
        self._selector.add_uint192()
        return self._add_param(value, False)

    def add_int200(self, value: int) -> 'ContractFunctionParameters':
        """Add an int200 parameter."""
        self._selector.add_int200()
        return self._add_param(value, False)

    def add_uint200(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint200 parameter."""
        self._selector.add_uint200()
        return self._add_param(value, False)

    def add_int208(self, value: int) -> 'ContractFunctionParameters':
        """Add an int208 parameter."""
        self._selector.add_int208()
        return self._add_param(value, False)

    def add_uint208(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint208 parameter."""
        self._selector.add_uint208()
        return self._add_param(value, False)

    def add_int216(self, value: int) -> 'ContractFunctionParameters':
        """Add an int216 parameter."""
        self._selector.add_int216()
        return self._add_param(value, False)

    def add_uint216(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint216 parameter."""
        self._selector.add_uint216()
        return self._add_param(value, False)

    def add_int224(self, value: int) -> 'ContractFunctionParameters':
        """Add an int224 parameter."""
        self._selector.add_int224()
        return self._add_param(value, False)

    def add_uint224(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint224 parameter."""
        self._selector.add_uint224()
        return self._add_param(value, False)

    def add_int232(self, value: int) -> 'ContractFunctionParameters':
        """Add an int232 parameter."""
        self._selector.add_int232()
        return self._add_param(value, False)

    def add_uint232(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint232 parameter."""
        self._selector.add_uint232()
        return self._add_param(value, False)

    def add_int240(self, value: int) -> 'ContractFunctionParameters':
        """Add an int240 parameter."""
        self._selector.add_int240()
        return self._add_param(value, False)

    def add_uint240(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint240 parameter."""
        self._selector.add_uint240()
        return self._add_param(value, False)

    def add_int248(self, value: int) -> 'ContractFunctionParameters':
        """Add an int248 parameter."""
        self._selector.add_int248()
        return self._add_param(value, False)

    def add_uint248(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint248 parameter."""
        self._selector.add_uint248()
        return self._add_param(value, False)

    def add_int256(self, value: int) -> 'ContractFunctionParameters':
        """Add an int256 parameter."""
        self._selector.add_int256()
        return self._add_param(value, False)

    def add_uint256(self, value: int) -> 'ContractFunctionParameters':
        """Add a uint256 parameter."""
        self._selector.add_uint256()
        return self._add_param(value, False)

    # Array methods for integer types
    def add_int8_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int8 array parameter."""
        self._selector.add_int8_array()
        return self._add_param(value, True)

    def add_uint8_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint8 array parameter."""
        self._selector.add_uint8_array()
        return self._add_param(value, True)

    def add_int16_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int16 array parameter."""
        self._selector.add_int16_array()
        return self._add_param(value, True)

    def add_uint16_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint16 array parameter."""
        self._selector.add_uint16_array()
        return self._add_param(value, True)

    def add_int32_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int32 array parameter."""
        self._selector.add_int32_array()
        return self._add_param(value, True)

    def add_uint32_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint32 array parameter."""
        self._selector.add_uint32_array()
        return self._add_param(value, True)

    def add_int64_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int64 array parameter."""
        self._selector.add_int64_array()
        return self._add_param(value, True)

    def add_uint64_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint64 array parameter."""
        self._selector.add_uint64_array()
        return self._add_param(value, True)

    def add_int256_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int256 array parameter."""
        self._selector.add_int256_array()
        return self._add_param(value, True)

    def add_uint256_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint256 array parameter."""
        self._selector.add_uint256_array()
        return self._add_param(value, True)

    # Additional array methods for all integer types
    def add_int24_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int24 array parameter."""
        self._selector.add_int24_array()
        return self._add_param(value, True)

    def add_uint24_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint24 array parameter."""
        self._selector.add_uint24_array()
        return self._add_param(value, True)

    def add_int40_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int40 array parameter."""
        self._selector.add_int40_array()
        return self._add_param(value, True)

    def add_uint40_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint40 array parameter."""
        self._selector.add_uint40_array()
        return self._add_param(value, True)

    def add_int48_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int48 array parameter."""
        self._selector.add_int48_array()
        return self._add_param(value, True)

    def add_uint48_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint48 array parameter."""
        self._selector.add_uint48_array()
        return self._add_param(value, True)

    def add_int56_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int56 array parameter."""
        self._selector.add_int56_array()
        return self._add_param(value, True)

    def add_uint56_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint56 array parameter."""
        self._selector.add_uint56_array()
        return self._add_param(value, True)

    def add_int72_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int72 array parameter."""
        self._selector.add_int72_array()
        return self._add_param(value, True)

    def add_uint72_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint72 array parameter."""
        self._selector.add_uint72_array()
        return self._add_param(value, True)

    def add_int80_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int80 array parameter."""
        self._selector.add_int80_array()
        return self._add_param(value, True)

    def add_uint80_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint80 array parameter."""
        self._selector.add_uint80_array()
        return self._add_param(value, True)

    def add_int88_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int88 array parameter."""
        self._selector.add_int88_array()
        return self._add_param(value, True)

    def add_uint88_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint88 array parameter."""
        self._selector.add_uint88_array()
        return self._add_param(value, True)

    def add_int96_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int96 array parameter."""
        self._selector.add_int96_array()
        return self._add_param(value, True)

    def add_uint96_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint96 array parameter."""
        self._selector.add_uint96_array()
        return self._add_param(value, True)

    def add_int104_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int104 array parameter."""
        self._selector.add_int104_array()
        return self._add_param(value, True)

    def add_uint104_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint104 array parameter."""
        self._selector.add_uint104_array()
        return self._add_param(value, True)

    def add_int112_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int112 array parameter."""
        self._selector.add_int112_array()
        return self._add_param(value, True)

    def add_uint112_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint112 array parameter."""
        self._selector.add_uint112_array()
        return self._add_param(value, True)

    def add_int120_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int120 array parameter."""
        self._selector.add_int120_array()
        return self._add_param(value, True)

    def add_uint120_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint120 array parameter."""
        self._selector.add_uint120_array()
        return self._add_param(value, True)

    def add_int128_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int128 array parameter."""
        self._selector.add_int128_array()
        return self._add_param(value, True)

    def add_uint128_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint128 array parameter."""
        self._selector.add_uint128_array()
        return self._add_param(value, True)

    def add_int136_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int136 array parameter."""
        self._selector.add_int136_array()
        return self._add_param(value, True)

    def add_uint136_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint136 array parameter."""
        self._selector.add_uint136_array()
        return self._add_param(value, True)

    def add_int144_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int144 array parameter."""
        self._selector.add_int144_array()
        return self._add_param(value, True)

    def add_uint144_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint144 array parameter."""
        self._selector.add_uint144_array()
        return self._add_param(value, True)

    def add_int152_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int152 array parameter."""
        self._selector.add_int152_array()
        return self._add_param(value, True)

    def add_uint152_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint152 array parameter."""
        self._selector.add_uint152_array()
        return self._add_param(value, True)

    def add_int160_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int160 array parameter."""
        self._selector.add_int160_array()
        return self._add_param(value, True)

    def add_uint160_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint160 array parameter."""
        self._selector.add_uint160_array()
        return self._add_param(value, True)

    def add_int168_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int168 array parameter."""
        self._selector.add_int168_array()
        return self._add_param(value, True)

    def add_uint168_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint168 array parameter."""
        self._selector.add_uint168_array()
        return self._add_param(value, True)

    def add_int176_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int176 array parameter."""
        self._selector.add_int176_array()
        return self._add_param(value, True)

    def add_uint176_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint176 array parameter."""
        self._selector.add_uint176_array()
        return self._add_param(value, True)

    def add_int184_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int184 array parameter."""
        self._selector.add_int184_array()
        return self._add_param(value, True)

    def add_uint184_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint184 array parameter."""
        self._selector.add_uint184_array()
        return self._add_param(value, True)

    def add_int192_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int192 array parameter."""
        self._selector.add_int192_array()
        return self._add_param(value, True)

    def add_uint192_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint192 array parameter."""
        self._selector.add_uint192_array()
        return self._add_param(value, True)

    def add_int200_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int200 array parameter."""
        self._selector.add_int200_array()
        return self._add_param(value, True)

    def add_uint200_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint200 array parameter."""
        self._selector.add_uint200_array()
        return self._add_param(value, True)

    def add_int208_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int208 array parameter."""
        self._selector.add_int208_array()
        return self._add_param(value, True)

    def add_uint208_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint208 array parameter."""
        self._selector.add_uint208_array()
        return self._add_param(value, True)

    def add_int216_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int216 array parameter."""
        self._selector.add_int216_array()
        return self._add_param(value, True)

    def add_uint216_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint216 array parameter."""
        self._selector.add_uint216_array()
        return self._add_param(value, True)

    def add_int224_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int224 array parameter."""
        self._selector.add_int224_array()
        return self._add_param(value, True)

    def add_uint224_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint224 array parameter."""
        self._selector.add_uint224_array()
        return self._add_param(value, True)

    def add_int232_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int232 array parameter."""
        self._selector.add_int232_array()
        return self._add_param(value, True)

    def add_uint232_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint232 array parameter."""
        self._selector.add_uint232_array()
        return self._add_param(value, True)

    def add_int240_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int240 array parameter."""
        self._selector.add_int240_array()
        return self._add_param(value, True)

    def add_uint240_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint240 array parameter."""
        self._selector.add_uint240_array()
        return self._add_param(value, True)

    def add_int248_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add an int248 array parameter."""
        self._selector.add_int248_array()
        return self._add_param(value, True)

    def add_uint248_array(self, value: list[int]) -> 'ContractFunctionParameters':
        """Add a uint248 array parameter."""
        self._selector.add_uint248_array()
        return self._add_param(value, True)

    def add_address(self, value: str) -> 'ContractFunctionParameters':
        """
        Add an address parameter.
        
        Args:
            value: The address value as a hex string (with or without 0x prefix)
            
        Returns:
            This instance for method chaining
        """
        # Allow 0x prefix
        if value.startswith('0x'):
            if len(value) != 42:
                raise ValueError("`address` type requires parameter to be 42 characters with 0x prefix")
            address_bytes = bytes.fromhex(value[2:])
        else:
            if len(value) != 40:
                raise ValueError("`address` type requires parameter to be 40 characters")
            address_bytes = bytes.fromhex(value)
        
        self._selector.add_address()
        return self._add_param(address_bytes, False)

    def add_address_array(self, value: list[str]) -> 'ContractFunctionParameters':
        """
        Add an address array parameter.
        
        Args:
            value: The address array to add
            
        Returns:
            This instance for method chaining
        """
        processed_addresses = []
        for entry in value:
            if entry.startswith('0x'):
                if len(entry) != 42:
                    raise ValueError("`address` type requires parameter to be 42 characters with 0x prefix")
                address_bytes = bytes.fromhex(entry[2:])
            else:
                if len(entry) != 40:
                    raise ValueError("`address` type requires parameter to be 40 characters")
                address_bytes = bytes.fromhex(entry)
            processed_addresses.append(address_bytes)
        
        self._selector.add_address_array()
        return self._add_param(processed_addresses, True)

    def add_function(self, address: str, selector: ContractFunctionSelector) -> 'ContractFunctionParameters':
        """
        Add a function parameter.
        
        Args:
            address: The contract address
            selector: The function selector
            
        Returns:
            This instance for method chaining
        """
        if address.startswith('0x'):
            address = address[2:]
        
        address_bytes = bytes.fromhex(address)
        if len(address_bytes) != 20:
            raise ValueError("`function` type requires parameter `address` to be exactly 20 bytes")
        
        function_selector = selector.build()
        
        self._selector.add_function()
        
        # Combine address (20 bytes) + function selector (4 bytes) = 24 bytes
        proto = bytearray(24)
        proto[0:20] = address_bytes
        proto[20:24] = function_selector
        
        return self._add_param(bytes(proto), False)

    def _add_param(self, param: Any, dynamic: bool) -> 'ContractFunctionParameters':
        """
        Internal method to add a parameter.
        
        Args:
            param: The parameter value
            dynamic: Whether the parameter is dynamic
            
        Returns:
            This instance for method chaining
        """
        index = len(self._selector._param_types) - 1
        value = self._argument_to_bytes(param, self._selector._param_types[index])
        
        self._arguments.append({"dynamic": dynamic, "value": value})
        return self

    def _build(self, name: Optional[str] = None) -> bytes:
        """
        Internal method to build the encoded parameters.
        
        Args:
            name: Optional function name for selector
            
        Returns:
            The encoded parameter bytes
        """
        include_id = name is not None
        name_offset = 4 if include_id else 0
        
        if len(self._arguments) == 0:
            length = name_offset
        else:
            dynamic_length = sum(len(arg["value"]) for arg in self._arguments if arg["dynamic"])
            length = len(self._arguments) * 32 + dynamic_length + name_offset
        
        func = bytearray(length)
        
        if include_id:
            func[0:4] = self._selector.build(name)
        
        offset = 32 * len(self._arguments)
        
        for i, arg in enumerate(self._arguments):
            if arg["dynamic"]:
                # Pack offset as big-endian uint32 at position 28 bytes from start of current element slot
                struct.pack_into('>I', func, name_offset + i * 32 + 28, offset)
                # Write value bytes at offset position after array length
                func[offset + name_offset:offset + name_offset + len(arg["value"])] = arg["value"]
                offset += len(arg["value"])
            else:
                # Write data directly at parameter position
                func[name_offset + i * 32:name_offset + i * 32 + len(arg["value"])] = arg["value"]
        
        return bytes(func)

    def _argument_to_bytes(self, param: Any, param_type) -> bytes:
        """
        Convert a parameter to its ABI-encoded bytes representation.
        
        Args:
            param: The parameter value
            param_type: The parameter type information (SolidityType)
            
        Returns:
            The encoded parameter bytes
        """
        if param_type.array:
            return self._encode_array(param, param_type)
        else:
            return self._encode_single(param, param_type.ty)

    def _encode_array(self, param: list[Any], param_type) -> bytes:
        """Encode an array parameter."""
        if not isinstance(param, list):
            raise TypeError("SolidityType indicates type is array, but parameter is not an array")
        
        values = []
        for p in param:
            arg = self._encode_single(p, param_type.ty)
            values.append(arg)
        
        # Array length (32 bytes) + elements
        total_length = 32 + sum(len(v) for v in values)
        
        # For dynamic types, we need additional space for offsets
        if param_type.ty in [ArgumentType.STRING, ArgumentType.BYTES]:
            total_length += len(values) * 32
        
        result = bytearray(total_length)
        
        # Pack array length as big-endian uint32 at offset 28
        struct.pack_into('>I', result, 28, len(values))
        
        if param_type.ty in [ArgumentType.STRING, ArgumentType.BYTES]:
            # Dynamic array elements
            offset = 32 * len(values)
            for i, value in enumerate(values):
                # Write offset for dynamic array element - packs offset as big-endian uint32 at position 28 bytes from start of current element slot
                struct.pack_into('>I', result, 32 + i * 32 + 28, offset)
                
                # Write value bytes at offset position after array length
                result[32 + offset:32 + offset + len(value)] = value
                offset += len(value)
        else:
            # Static array elements
            for i, value in enumerate(values):
                result[32 + i * 32:32 + i * 32 + len(value)] = value
        
        return bytes(result)

    def _encode_single(self, param: Any, arg_type: ArgumentType) -> bytes:
        """Encode a single parameter."""
        value = bytearray(32)
        
        if arg_type == ArgumentType.BOOL:
            value[31] = 1 if param else 0
        
        elif arg_type == ArgumentType.ADDRESS:
            if isinstance(param, bytes) and len(param) == 20:
                value[12:32] = param
            else:
                raise ValueError("Address must be 20 bytes")
        
        elif arg_type == ArgumentType.BYTES32:
            if isinstance(param, bytes) and len(param) == 32:
                value[0:32] = param
            else:
                raise ValueError("bytes32 must be exactly 32 bytes")
        
        elif arg_type == ArgumentType.STRING:
            if isinstance(param, str):
                param = param.encode('utf-8')
            
            # String length + padded data
            padded_length = ((len(param) + 31) // 32) * 32
            result = bytearray(32 + padded_length)
            
            # Pack array length as big-endian uint32 at offset 28
            struct.pack_into('>I', result, 28, len(param))
            # Write data
            result[32:32 + len(param)] = param
            
            return bytes(result)
        
        elif arg_type == ArgumentType.BYTES:
            # Bytes length + padded data
            padded_length = ((len(param) + 31) // 32) * 32
            result = bytearray(32 + padded_length)
            
            # Pack array length as big-endian uint32 at offset 28
            struct.pack_into('>I', result, 28, len(param))
            # Write data
            result[32:32 + len(param)] = param
            
            return bytes(result)
        
        elif arg_type in [ArgumentType.UINT8, ArgumentType.UINT16, ArgumentType.UINT32, ArgumentType.UINT64,
                          ArgumentType.UINT256, ArgumentType.INT8, ArgumentType.INT16, ArgumentType.INT32,
                          ArgumentType.INT64, ArgumentType.INT256]:
            # Integer types
            if isinstance(param, int):
                if arg_type.name.startswith('UINT'):
                    if param < 0:
                        raise ValueError(f"Unsigned integer cannot be negative: {param}")
                    value = param.to_bytes(32, byteorder='big')
                else:
                    # Signed integer
                    if param < 0:
                        # Two's complement
                        value = (2**256 + param).to_bytes(32, byteorder='big')
                    else:
                        value = param.to_bytes(32, byteorder='big')
            else:
                raise TypeError(f"Integer type expected, got {type(param)}")
        
        else:
            raise ValueError(f"Unsupported argument type: {arg_type}")
        
        return bytes(value)

    def to_bytes(self) -> bytes:
        """
        Convert the parameters to their ABI-encoded bytes representation.
        
        Returns:
            The ABI-encoded parameter bytes
        """
        return self._build()

    def __bytes__(self) -> bytes:
        """Allow conversion to bytes using bytes() function."""
        return self.to_bytes()

    def __len__(self) -> int:
        """Return the number of parameters added."""
        return len(self._arguments)

    def clear(self) -> 'ContractFunctionParameters':
        """
        Clear all parameters.
        
        Returns:
            This instance for method chaining
        """
        self._arguments.clear()
        self._selector = ContractFunctionSelector()
        return self
