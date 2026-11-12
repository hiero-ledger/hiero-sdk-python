"""EvmHookMappingEntry class for HIP-1195 hooks."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.hapi.services import hook_types_pb2


def _as_bytes(value: bytes | bytearray | None, name: str) -> bytes | None:
    """Validates an optional bytes field and normalizes bytearray to bytes."""
    if value is None:
        return None
    if not isinstance(value, bytes | bytearray):
        raise TypeError(f"{name} must be bytes.")
    return bytes(value)


@dataclass
class EvmHookMappingEntry:
    """
    An entry in a Solidity mapping in an EVM hook's storage.

    The entry is addressed either by an explicit `key` or by a `preimage` that
    the network hashes into the key (for variable-length mapping keys). Exactly
    one of them must be set; use `with_key` or `with_preimage` to build one.

    Attributes:
        key (bytes, optional): The explicit mapping key (at most 32 bytes,
            minimal representation).
        preimage (bytes, optional): The preimage of the mapping key.
        value (bytes): The mapping value (at most 32 bytes, minimal
            representation). Empty bytes remove the entry.
    """

    key: bytes | None = None
    preimage: bytes | None = None
    value: bytes = b""

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
            ValueError: If both key and preimage are set.
        """
        self.key = _as_bytes(self.key, "key")
        self.preimage = _as_bytes(self.preimage, "preimage")
        self.value = _as_bytes(self.value, "value") or b""
        if self.key is not None and self.preimage is not None:
            raise ValueError("EvmHookMappingEntry accepts either key or preimage, not both.")

    @classmethod
    def with_key(cls, key: bytes, value: bytes = b"") -> EvmHookMappingEntry:
        """Creates an entry addressed by an explicit mapping key."""
        return cls(key=key, value=value)

    @classmethod
    def with_preimage(cls, preimage: bytes, value: bytes = b"") -> EvmHookMappingEntry:
        """Creates an entry addressed by the preimage of its mapping key."""
        return cls(preimage=preimage, value=value)

    def _to_proto(self) -> hook_types_pb2.EvmHookMappingEntry:
        """
        Converts this entry to its protobuf representation.

        Raises:
            ValueError: If neither key nor preimage is set.
        """
        if self.key is not None:
            return hook_types_pb2.EvmHookMappingEntry(key=self.key, value=self.value)
        if self.preimage is not None:
            return hook_types_pb2.EvmHookMappingEntry(preimage=self.preimage, value=self.value)
        raise ValueError("EvmHookMappingEntry requires either a key or a preimage.")

    @classmethod
    def _from_proto(cls, proto: hook_types_pb2.EvmHookMappingEntry) -> EvmHookMappingEntry:
        """
        Creates an entry from its protobuf representation.

        Raises:
            ValueError: If the protobuf has neither key nor preimage set.
        """
        entry_key = proto.WhichOneof("entry_key")
        if entry_key == "key":
            return cls(key=proto.key, value=proto.value)
        if entry_key == "preimage":
            return cls(preimage=proto.preimage, value=proto.value)
        raise ValueError("EvmHookMappingEntry proto must have either key or preimage set.")
