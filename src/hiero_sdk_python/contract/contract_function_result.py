# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-public-methods
"""
This module provides the ContractFunctionResult class for decoding results from smart
contract function calls. It supports all standard Solidity return types and uses eth-abi for
decoding. Results can be accessed through type-specific getter methods.
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

import eth_abi
from google.protobuf.wrappers_pb2 import BytesValue, Int64Value

from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.contract.contract_log_info import ContractLogInfo
from hiero_sdk_python.contract.contract_nonce_info import ContractNonceInfo
from hiero_sdk_python.hapi.services import contract_types_pb2


@dataclass
class ContractFunctionResult:
    """
    A smart contract function call result decoder using eth-abi.

    This class provides a clean interface for decoding and accessing return values from
    Hedera smart contract function calls, using the eth-abi library to handle the decoding logic.
    """

    contract_id: Optional[ContractId] = None
    contract_call_result: Optional[bytes] = None
    error_message: Optional[str] = None
    bloom: Optional[bytes] = None
    gas_used: Optional[int] = None
    log_info: List[ContractLogInfo] = field(default_factory=list)
    evm_address: Optional[ContractId] = None
    gas_available: Optional[int] = None
    amount: Optional[int] = None
    function_parameters: Optional[bytes] = None
    contract_nonces: List[ContractNonceInfo] = field(default_factory=list)
    signer_nonce: Optional[int] = None

    def get_result(self, output_types: List[str]) -> List[Any]:
        """
        Decode the result bytes according to the provided Solidity output types.

        Args:
            output_types: List of Solidity type strings in the order they were
                returned by the contract function (e.g., ["uint256", "string", "bool"])

        Returns:
            List of decoded values in the order they were returned by the contract function

        Raises:
            Exception: If there is an error decoding the results
        """
        if not self.contract_call_result or len(self.contract_call_result) == 0:
            return []

        try:
            return list(eth_abi.decode(output_types, self.contract_call_result))
        except Exception as e:
            raise ValueError(f"Failed to decode contract result: {str(e)}") from e

    def _validate_contract_call_result(self) -> None:
        """Validate that contract_call_result is not None."""
        if not self.contract_call_result:
            raise ValueError("Contract call result is None")

    def _validate_result_index(self, index: int) -> None:
        """Validate that the index is within bounds."""
        if index < 0 or index > len(self.contract_call_result):
            raise ValueError("Result index out of bounds")

    def _get_value_at_index(self, index: int, size: int, signed: bool = False) -> int:
        """
        Helper method to get a value of specified size from the result at the given index.

        Args:
            index: The index of the value to retrieve
            size: The size in bytes of the value
            signed: Whether to interpret the value as signed

        Returns:
            The value at the specified index

        Raises:
            ValueError: If the index is out of bounds or the contract call result is None
        """
        self._validate_contract_call_result()

        position = index * 32 + (32 - size)

        self._validate_result_index(position + size)

        return int.from_bytes(
            self.contract_call_result[position : position + size],
            byteorder="big",
            signed=signed,
        )

    def get_address(self, index: int) -> str:
        """Gets a Solidity address from the result at the given index."""
        self._validate_contract_call_result()

        start = index * 32 + 12
        end = index * 32 + 32

        self._validate_result_index(end)
        return self.contract_call_result[start:end].hex()

    def get_uint8(self, index: int) -> int:
        """Gets a Solidity uint8 from the result at the given index."""
        return self._get_value_at_index(index, size=1)

    def get_int8(self, index: int) -> int:
        """Gets a Solidity int8 from the result at the given index."""
        return self._get_value_at_index(index, size=1, signed=True)

    def get_uint16(self, index: int) -> int:
        """Gets a Solidity uint16 from the result at the given index."""
        return self._get_value_at_index(index, size=2)

    def get_int16(self, index: int) -> int:
        """Gets a Solidity int16 from the result at the given index."""
        return self._get_value_at_index(index, size=2, signed=True)

    def get_uint24(self, index: int) -> int:
        """Gets a Solidity uint24 from the result at the given index."""
        return self._get_value_at_index(index, size=3)

    def get_int24(self, index: int) -> int:
        """Gets a Solidity int24 from the result at the given index."""
        return self._get_value_at_index(index, size=3, signed=True)

    def get_uint32(self, index: int) -> int:
        """Gets a Solidity uint32 from the result at the given index."""
        return self._get_value_at_index(index, size=4)

    def get_int32(self, index: int) -> int:
        """Gets a Solidity int32 from the result at the given index."""
        return self._get_value_at_index(index, size=4, signed=True)

    def get_uint40(self, index: int) -> int:
        """Gets a Solidity uint40 from the result at the given index."""
        return self._get_value_at_index(index, size=5)

    def get_int40(self, index: int) -> int:
        """Gets a Solidity int40 from the result at the given index."""
        return self._get_value_at_index(index, size=5, signed=True)

    def get_uint48(self, index: int) -> int:
        """Gets a Solidity uint48 from the result at the given index."""
        return self._get_value_at_index(index, size=6)

    def get_int48(self, index: int) -> int:
        """Gets a Solidity int48 from the result at the given index."""
        return self._get_value_at_index(index, size=6, signed=True)

    def get_uint56(self, index: int) -> int:
        """Gets a Solidity uint56 from the result at the given index."""
        return self._get_value_at_index(index, size=7)

    def get_int56(self, index: int) -> int:
        """Gets a Solidity int56 from the result at the given index."""
        return self._get_value_at_index(index, size=7, signed=True)

    def get_uint64(self, index: int) -> int:
        """Gets a Solidity uint64 from the result at the given index."""
        return self._get_value_at_index(index, size=8)

    def get_int64(self, index: int) -> int:
        """Gets a Solidity int64 from the result at the given index."""
        return self._get_value_at_index(index, size=8, signed=True)

    def get_uint72(self, index: int) -> int:
        """Gets a Solidity uint72 from the result at the given index."""
        return self._get_value_at_index(index, size=9)

    def get_int72(self, index: int) -> int:
        """Gets a Solidity int72 from the result at the given index."""
        return self._get_value_at_index(index, size=9, signed=True)

    def get_uint80(self, index: int) -> int:
        """Gets a Solidity uint80 from the result at the given index."""
        return self._get_value_at_index(index, size=10)

    def get_int80(self, index: int) -> int:
        """Gets a Solidity int80 from the result at the given index."""
        return self._get_value_at_index(index, size=10, signed=True)

    def get_uint88(self, index: int) -> int:
        """Gets a Solidity uint88 from the result at the given index."""
        return self._get_value_at_index(index, size=11)

    def get_int88(self, index: int) -> int:
        """Gets a Solidity int88 from the result at the given index."""
        return self._get_value_at_index(index, size=11, signed=True)

    def get_uint96(self, index: int) -> int:
        """Gets a Solidity uint96 from the result at the given index."""
        return self._get_value_at_index(index, size=12)

    def get_int96(self, index: int) -> int:
        """Gets a Solidity int96 from the result at the given index."""
        return self._get_value_at_index(index, size=12, signed=True)

    def get_uint104(self, index: int) -> int:
        """Gets a Solidity uint104 from the result at the given index."""
        return self._get_value_at_index(index, size=13)

    def get_int104(self, index: int) -> int:
        """Gets a Solidity int104 from the result at the given index."""
        return self._get_value_at_index(index, size=13, signed=True)

    def get_uint112(self, index: int) -> int:
        """Gets a Solidity uint112 from the result at the given index."""
        return self._get_value_at_index(index, size=14)

    def get_int112(self, index: int) -> int:
        """Gets a Solidity int112 from the result at the given index."""
        return self._get_value_at_index(index, size=14, signed=True)

    def get_uint120(self, index: int) -> int:
        """Gets a Solidity uint120 from the result at the given index."""
        return self._get_value_at_index(index, size=15)

    def get_int120(self, index: int) -> int:
        """Gets a Solidity int120 from the result at the given index."""
        return self._get_value_at_index(index, size=15, signed=True)

    def get_uint128(self, index: int) -> int:
        """Gets a Solidity uint128 from the result at the given index."""
        return self._get_value_at_index(index, size=16)

    def get_int128(self, index: int) -> int:
        """Gets a Solidity int128 from the result at the given index."""
        return self._get_value_at_index(index, size=16, signed=True)

    def get_uint136(self, index: int) -> int:
        """Gets a Solidity uint136 from the result at the given index."""
        return self._get_value_at_index(index, size=17)

    def get_int136(self, index: int) -> int:
        """Gets a Solidity int136 from the result at the given index."""
        return self._get_value_at_index(index, size=17, signed=True)

    def get_uint144(self, index: int) -> int:
        """Gets a Solidity uint144 from the result at the given index."""
        return self._get_value_at_index(index, size=18)

    def get_int144(self, index: int) -> int:
        """Gets a Solidity int144 from the result at the given index."""
        return self._get_value_at_index(index, size=18, signed=True)

    def get_uint152(self, index: int) -> int:
        """Gets a Solidity uint152 from the result at the given index."""
        return self._get_value_at_index(index, size=19)

    def get_int152(self, index: int) -> int:
        """Gets a Solidity int152 from the result at the given index."""
        return self._get_value_at_index(index, size=19, signed=True)

    def get_uint160(self, index: int) -> int:
        """Gets a Solidity uint160 from the result at the given index."""
        return self._get_value_at_index(index, size=20)

    def get_int160(self, index: int) -> int:
        """Gets a Solidity int160 from the result at the given index."""
        return self._get_value_at_index(index, size=20, signed=True)

    def get_uint168(self, index: int) -> int:
        """Gets a Solidity uint168 from the result at the given index."""
        return self._get_value_at_index(index, size=21)

    def get_int168(self, index: int) -> int:
        """Gets a Solidity int168 from the result at the given index."""
        return self._get_value_at_index(index, size=21, signed=True)

    def get_uint176(self, index: int) -> int:
        """Gets a Solidity uint176 from the result at the given index."""
        return self._get_value_at_index(index, size=22)

    def get_int176(self, index: int) -> int:
        """Gets a Solidity int176 from the result at the given index."""
        return self._get_value_at_index(index, size=22, signed=True)

    def get_uint184(self, index: int) -> int:
        """Gets a Solidity uint184 from the result at the given index."""
        return self._get_value_at_index(index, size=23)

    def get_int184(self, index: int) -> int:
        """Gets a Solidity int184 from the result at the given index."""
        return self._get_value_at_index(index, size=23, signed=True)

    def get_uint192(self, index: int) -> int:
        """Gets a Solidity uint192 from the result at the given index."""
        return self._get_value_at_index(index, size=24)

    def get_int192(self, index: int) -> int:
        """Gets a Solidity int192 from the result at the given index."""
        return self._get_value_at_index(index, size=24, signed=True)

    def get_uint200(self, index: int) -> int:
        """Gets a Solidity uint200 from the result at the given index."""
        return self._get_value_at_index(index, size=25)

    def get_int200(self, index: int) -> int:
        """Gets a Solidity int200 from the result at the given index."""
        return self._get_value_at_index(index, size=25, signed=True)

    def get_uint208(self, index: int) -> int:
        """Gets a Solidity uint208 from the result at the given index."""
        return self._get_value_at_index(index, size=26)

    def get_int208(self, index: int) -> int:
        """Gets a Solidity int208 from the result at the given index."""
        return self._get_value_at_index(index, size=26, signed=True)

    def get_uint216(self, index: int) -> int:
        """Gets a Solidity uint216 from the result at the given index."""
        return self._get_value_at_index(index, size=27)

    def get_int216(self, index: int) -> int:
        """Gets a Solidity int216 from the result at the given index."""
        return self._get_value_at_index(index, size=27, signed=True)

    def get_uint224(self, index: int) -> int:
        """Gets a Solidity uint224 from the result at the given index."""
        return self._get_value_at_index(index, size=28)

    def get_int224(self, index: int) -> int:
        """Gets a Solidity int224 from the result at the given index."""
        return self._get_value_at_index(index, size=28, signed=True)

    def get_uint232(self, index: int) -> int:
        """Gets a Solidity uint232 from the result at the given index."""
        return self._get_value_at_index(index, size=29)

    def get_int232(self, index: int) -> int:
        """Gets a Solidity int232 from the result at the given index."""
        return self._get_value_at_index(index, size=29, signed=True)

    def get_uint240(self, index: int) -> int:
        """Gets a Solidity uint240 from the result at the given index."""
        return self._get_value_at_index(index, size=30)

    def get_int240(self, index: int) -> int:
        """Gets a Solidity int240 from the result at the given index."""
        return self._get_value_at_index(index, size=30, signed=True)

    def get_uint248(self, index: int) -> int:
        """Gets a Solidity uint248 from the result at the given index."""
        return self._get_value_at_index(index, size=31)

    def get_int248(self, index: int) -> int:
        """Gets a Solidity int248 from the result at the given index."""
        return self._get_value_at_index(index, size=31, signed=True)

    def get_uint256(self, index: int) -> int:
        """Gets a Solidity uint256 from the result at the given index."""
        return self._get_value_at_index(index, size=32)

    def get_int256(self, index: int) -> int:
        """Gets a Solidity int256 from the result at the given index."""
        return self._get_value_at_index(index, size=32, signed=True)

    def get_bool(self, index: int) -> bool:
        """Gets a Solidity bool from the result at the given index."""
        return self._get_value_at_index(index, size=1) == 1

    def get_bytes32(self, index: int) -> bytes:
        """Gets a Solidity bytes32 from the result at the given index."""
        self._validate_contract_call_result()

        start = index * 32
        end = start + 32

        self._validate_result_index(end)

        return self.contract_call_result[start:end]

    def get_bytes(self, index: int) -> bytes:
        """
        Gets a dynamic-length bytes array (Solidity 'bytes') from the result at the given index.

        In Ethereum ABI encoding, dynamic types like 'bytes' are stored as offsets pointing to
        their actual data. The value at the specified index is a 32-byte offset (in bytes)
        from the start of the result data. At that offset location, the first 32 bytes contain
        the length of the bytes array (right-aligned, big-endian), followed immediately by the
        actual bytes data.

        Args:
            index: The index in the return data array where the dynamic bytes value is located.
                This index points to a 32-byte word containing the offset (in bytes) from the
                start of the result data to the actual bytes value. At that offset, the first
                32 bytes represent the length of the bytes array, followed by the bytes data
                itself.

        Returns:
            The decoded bytes value at the specified index in the contract call result.

        Raises:
            ValueError: If the contract call result is not set or the index is out of bounds.
        """
        self._validate_contract_call_result()

        # The value at the index is a 32-byte offset (big-endian) from the start of the result
        offset = self.get_uint256(index)

        # Validate that the offset is within bounds
        self._validate_result_index(offset + 32)

        # The length is stored in the 32 bytes at [offset:offset+32], right-aligned
        length_bytes = self.contract_call_result[offset : offset + 32]
        length = int.from_bytes(length_bytes, byteorder="big")

        # Validate that the length is within bounds
        start = offset + 32
        end = start + length
        self._validate_result_index(end)

        return self.contract_call_result[start:end]

    def get_string(self, index: int) -> str:
        """
        Gets a Solidity string from the result at the given index.

        In Ethereum ABI encoding, dynamic types like 'string' are stored as offsets
        pointing to their actual data. The value at the specified index is a 32-byte
        offset (in bytes) from the start of the result data. At that offset location,
        the first 32 bytes contain the length of the string (right-aligned, big-endian),
        followed immediately by the UTF-8 encoded string data.

        Args:
            index: The index in the return data array where the dynamic string value is
                located. This index points to a 32-byte word containing the offset (in
                bytes) from the start of the result data to the actual string value. At
                that offset, the first 32 bytes represent the length of the string,
                followed by the UTF-8 encoded string data.

        Returns:
            The decoded string value at the specified index in the contract call result.

        Raises:
            ValueError: If the contract call result is not set or the index is out of
                bounds.
            UnicodeDecodeError: If the bytes data cannot be decoded as UTF-8.
        """
        return self.get_bytes(index).decode("utf-8")

    @classmethod
    def _from_proto(
        cls, proto: contract_types_pb2.ContractFunctionResult
    ) -> "ContractFunctionResult":
        """
        Deserializes a ContractFunctionResult from a protobuf message.

        Args:
            proto: The protobuf message to deserialize.

        Returns:
            A ContractFunctionResult object deserialized from the protobuf message.

        Raises:
            ValueError: If the protobuf message is None or the contract call result is empty.
        """
        if proto is None:
            raise ValueError("Contract function result proto is None")

        logs = []
        for log_info in proto.logInfo:
            logs.append(ContractLogInfo._from_proto(log_info))

        evm_address = (
            ContractId(evm_address=proto.evm_address.value)
            if len(proto.evm_address.value) > 0
            else None
        )

        contract_nonces = []
        for contract_nonce in proto.contract_nonces:
            contract_nonces.append(ContractNonceInfo._from_proto(contract_nonce))

        return cls(
            contract_id=(
                ContractId._from_proto(proto.contractID) if proto.contractID else None
            ),
            contract_call_result=proto.contractCallResult,
            error_message=proto.errorMessage,
            bloom=proto.bloom,
            gas_used=proto.gasUsed,
            log_info=logs,
            evm_address=evm_address,
            gas_available=proto.gas,
            amount=proto.amount,
            function_parameters=proto.functionParameters,
            contract_nonces=contract_nonces,
            signer_nonce=proto.signer_nonce.value if proto.signer_nonce else None,
        )

    def _to_proto(self) -> contract_types_pb2.ContractFunctionResult:
        """
        Serializes a ContractFunctionResult to a protobuf message.

        Returns:
            A protobuf message representing the ContractFunctionResult.
        """
        return contract_types_pb2.ContractFunctionResult(
            contractID=self.contract_id._to_proto() if self.contract_id else None,
            contractCallResult=self.contract_call_result,
            errorMessage=self.error_message,
            bloom=self.bloom,
            gasUsed=self.gas_used,
            logInfo=[log_info._to_proto() for log_info in self.log_info or []],
            evm_address=(
                BytesValue(value=self.evm_address.evm_address)
                if self.evm_address
                else None
            ),
            gas=self.gas_available,
            amount=self.amount,
            functionParameters=self.function_parameters,
            signer_nonce=Int64Value(value=self.signer_nonce),
            contract_nonces=[
                contract_nonce._to_proto()
                for contract_nonce in self.contract_nonces or []
            ],
        )
