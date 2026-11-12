"""EvmHookCall class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import basic_types_pb2


@dataclass
class EvmHookCall:
    """
    The call data and gas limit for a call to an EVM hook.

    Attributes:
        data (bytes): Call data passed to the hook through `HookContext.data`.
        gas_limit (int): The gas limit for the hook's execution.
    """

    data: bytes = b""
    gas_limit: int = 0

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
            ValueError: If gas_limit is negative.
        """
        if not isinstance(self.data, bytes | bytearray):
            raise TypeError("data must be bytes.")
        self.data = bytes(self.data)
        if isinstance(self.gas_limit, bool) or not isinstance(self.gas_limit, int):
            raise TypeError("gas_limit must be an integer.")
        if self.gas_limit < 0:
            raise ValueError("gas_limit must be non-negative.")

    def _to_proto(self) -> basic_types_pb2.EvmHookCall:
        """Converts this EvmHookCall to its protobuf representation."""
        return basic_types_pb2.EvmHookCall(data=self.data, gas_limit=self.gas_limit)

    @classmethod
    def _from_proto(cls, proto: basic_types_pb2.EvmHookCall) -> EvmHookCall:
        """Creates an EvmHookCall from its protobuf representation."""
        return cls(data=proto.data, gas_limit=proto.gas_limit)
