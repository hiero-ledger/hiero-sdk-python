"""
This module provides the ContractFunctionParameters class for encoding parameters for Hedera smart
contract function calls. It supports all standard Solidity parameter types and uses eth-abi for
encoding. Parameters can be encoded into a bytes format suitable for smart contract function calls.
"""

from typing import Any, List, Optional, Union

import eth_abi
from eth_utils import function_signature_to_4byte_selector


class ContractFunctionParameters:
    """
    A simplified contract function interface using eth-abi for parameter encoding.

    This class provides a clean interface for encoding parameters to be passed to Hedera
    smart contract function calls, using the eth-abi library to handle the encoding logic.
    """

    def __init__(self, function_name: Optional[str] = None):
        """
        Initialize a new ContractFunctionParameters instance.

        Args:
            function_name: Optional function name to use for the function selector
        """
        self.function_name = function_name
        self._types: List[str] = []
        self._values: List[Any] = []

    def _add_param(self, type_name: str, value: Any) -> "ContractFunctionParameters":
        """
        Internal helper to add a parameter.

        Args:
            type_name: The Solidity type name
            value: The value to add

        Returns:
            This instance for method chaining
        """
        self._types.append(type_name)
        self._values.append(value)
        return self

    # Basic types - explicitly define method signatures for IDE support
    def add_bool(self, value: bool) -> "ContractFunctionParameters":
        """
        Add a boolean parameter.

        Args:
            value: The boolean value to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("bool", value)

    def add_address(self, value: Union[str, bytes]) -> "ContractFunctionParameters":
        """
        Add an address parameter.

        Args:
            value: The address as a hex string (with or without 0x prefix) or bytes

        Returns:
            This instance for method chaining
        """
        return self._add_param("address", value)

    def add_string(self, value: str) -> "ContractFunctionParameters":
        """
        Add a string parameter.

        Args:
            value: The string value to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("string", value)

    def add_bytes(self, value: bytes) -> "ContractFunctionParameters":
        """
        Add a bytes parameter.

        Args:
            value: The bytes value to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("bytes", value)

    def add_bytes32(self, value: bytes) -> "ContractFunctionParameters":
        """
        Add a bytes32 parameter.

        Args:
            value: The bytes value to add, must be exactly 32 bytes long

        Returns:
            This instance for method chaining
        """
        return self._add_param("bytes32", value)

    # Array type methods for basic types
    def add_bool_array(self, value: List[bool]) -> "ContractFunctionParameters":
        """
        Add a boolean array parameter.

        Args:
            value: The boolean array to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("bool[]", value)

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
        return self._add_param("address[]", value)

    def add_string_array(self, value: List[str]) -> "ContractFunctionParameters":
        """
        Add a string array parameter.

        Args:
            value: The string array to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("string[]", value)

    def add_bytes_array(self, value: List[bytes]) -> "ContractFunctionParameters":
        """
        Add a bytes array parameter.

        Args:
            value: The bytes array to add

        Returns:
            This instance for method chaining
        """
        return self._add_param("bytes[]", value)

    def add_bytes32_array(self, value: List[bytes]) -> "ContractFunctionParameters":
        """
        Add a bytes32 array parameter.

        Args:
            value: The bytes32 array to add, each element must be exactly 32 bytes

        Returns:
            This instance for method chaining
        """
        return self._add_param("bytes32[]", value)

    def _get_function_selector(self) -> bytes:
        """
        Get the function selector (first 4 bytes of the keccak256 hash of the function signature).

        Returns:
            The function selector as bytes

        Raises:
            ValueError: If no function name was provided
        """
        if not self.function_name:
            raise ValueError("Function name is required for selector")

        signature = f"{self.function_name}({','.join(self._types)})"
        return function_signature_to_4byte_selector(signature)

    def _encode_parameters(self) -> bytes:
        """
        Encode the parameters according to the Ethereum ABI spec.

        Returns:
            The ABI-encoded parameter bytes (without the function selector)

        Raises:
            Exception: If there is an error encoding the parameters
        """
        return eth_abi.encode(self._types, self._values)

    def to_bytes(self) -> bytes:
        """
        Get the full encoded function call including selector and parameters.

        Returns:
            The complete function call data as bytes

        Raises:
            ValueError: If no function name was provided
            Exception: If there is an error encoding the parameters
        """
        if self.function_name:
            return self._get_function_selector() + self._encode_parameters()

        return self._encode_parameters()

    def __bytes__(self) -> bytes:
        """Allow conversion to bytes using bytes() function."""
        return self.to_bytes()

    def clear(self) -> "ContractFunctionParameters":
        """
        Clear all parameters.

        Returns:
            This instance for method chaining
        """
        self._types.clear()
        self._values.clear()
        return self


# Dynamically generate integer type methods
def _create_method(class_type, method_name, type_name, doc, is_array=False):
    """
    Helper function to create and attach a method to the ContractFunctionParameters class.

    Args:
        class_type: The class to attach the method to
        method_name: The name of the method to create
        type_name: The Solidity type name to use
        doc: The docstring for the method
        is_array: Whether this is an array type method
    """

    def method(
        self: Any, value: List[int] if is_array else int
    ) -> "ContractFunctionParameters":
        """
        Dynamically created method to add an integer parameter or array of integers.
        Takes either a single integer value or a list of integers depending on is_array flag.
        Returns the ContractFunctionParameters instance for method chaining.
        """
        return self._add_param(type_name, value)

    method.__doc__ = doc
    setattr(class_type, method_name, method)


def _generate_int_type_methods(size: int):
    """
    Generate int and uint methods for a specific size.

    Args:
        size: The bit size of the integer type
    """
    # Int methods
    int_doc = f"""
    Add an int{size} parameter.

    Args:
        value: The int{size} value to add

    Returns:
        This instance for method chaining
    """
    _create_method(ContractFunctionParameters, f"add_int{size}", f"int{size}", int_doc)

    # Uint methods
    uint_doc = f"""
    Add a uint{size} parameter.

    Args:
        value: The uint{size} value to add

    Returns:
        This instance for method chaining
    """
    _create_method(
        ContractFunctionParameters, f"add_uint{size}", f"uint{size}", uint_doc
    )


def _generate_int_array_methods(size: int):
    """
    Generate int array and uint array methods for a specific size.

    Args:
        size: The bit size of the integer type
    """
    # Int array methods
    int_array_doc = f"""
    Add an int{size} array parameter.

    Args:
        value: The int{size} array to add

    Returns:
        This instance for method chaining
    """
    _create_method(
        ContractFunctionParameters,
        f"add_int{size}_array",
        f"int{size}[]",
        int_array_doc,
        is_array=True,
    )

    # Uint array methods
    uint_array_doc = f"""
    Add a uint{size} array parameter.

    Args:
        value: The uint{size} array to add

    Returns:
        This instance for method chaining
    """
    _create_method(
        ContractFunctionParameters,
        f"add_uint{size}_array",
        f"uint{size}[]",
        uint_array_doc,
        is_array=True,
    )


def _generate_int_methods():
    """Generate all int and uint methods for the ContractFunctionParameters class."""
    int_sizes = list(range(8, 257, 8))

    for size in int_sizes:
        _generate_int_type_methods(size)
        _generate_int_array_methods(size)


# Generate all the integer methods
_generate_int_methods()
