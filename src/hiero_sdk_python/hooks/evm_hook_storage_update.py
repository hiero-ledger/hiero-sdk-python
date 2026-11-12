"""EVM hook storage update classes for HIP-1195 hooks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from hiero_sdk_python.hapi.services import hook_types_pb2
from hiero_sdk_python.hooks.evm_hook_mapping_entry import EvmHookMappingEntry


class EvmHookStorageUpdate(ABC):
    """
    A change to an EVM hook's storage.

    Use `EvmHookStorageSlot` to write a raw storage slot, or
    `EvmHookMappingEntries` to write entries of a Solidity mapping.
    """

    @abstractmethod
    def _to_proto(self) -> hook_types_pb2.EvmHookStorageUpdate:
        """Converts this update to its protobuf representation."""

    @classmethod
    def _from_proto(cls, proto: hook_types_pb2.EvmHookStorageUpdate) -> EvmHookStorageUpdate:
        """
        Creates the matching storage update subclass from its protobuf representation.

        Raises:
            ValueError: If the protobuf has neither a storage slot nor mapping entries set.
        """
        update = proto.WhichOneof("update")
        if update == "storage_slot":
            return EvmHookStorageSlot._from_slot_proto(proto.storage_slot)
        if update == "mapping_entries":
            return EvmHookMappingEntries._from_entries_proto(proto.mapping_entries)
        raise ValueError("EvmHookStorageUpdate proto must have either storage_slot or mapping_entries set.")


@dataclass
class EvmHookStorageSlot(EvmHookStorageUpdate):
    """
    A write to a single raw storage slot of an EVM hook.

    Attributes:
        key (bytes): The slot key (at most 32 bytes, minimal representation).
        value (bytes): The slot value (at most 32 bytes, minimal representation).
            Empty bytes clear the slot.
    """

    key: bytes = b""
    value: bytes = b""

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field is not bytes.
        """
        for name in ("key", "value"):
            current = getattr(self, name)
            if not isinstance(current, bytes | bytearray):
                raise TypeError(f"{name} must be bytes.")
            setattr(self, name, bytes(current))

    def _to_proto(self) -> hook_types_pb2.EvmHookStorageUpdate:
        """Converts this slot write to its protobuf representation."""
        return hook_types_pb2.EvmHookStorageUpdate(
            storage_slot=hook_types_pb2.EvmHookStorageSlot(key=self.key, value=self.value)
        )

    @classmethod
    def _from_slot_proto(cls, proto: hook_types_pb2.EvmHookStorageSlot) -> EvmHookStorageSlot:
        """Creates a slot write from an EvmHookStorageSlot protobuf."""
        return cls(key=proto.key, value=proto.value)


@dataclass
class EvmHookMappingEntries(EvmHookStorageUpdate):
    """
    Writes to entries of a Solidity mapping in an EVM hook's storage.

    Attributes:
        mapping_slot (bytes): The storage slot of the Solidity mapping
            (minimal representation).
        entries (list[EvmHookMappingEntry]): The mapping entries to write.
    """

    mapping_slot: bytes = b""
    entries: list[EvmHookMappingEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Validates the field types.

        Raises:
            TypeError: If a field has the wrong type.
        """
        if not isinstance(self.mapping_slot, bytes | bytearray):
            raise TypeError("mapping_slot must be bytes.")
        self.mapping_slot = bytes(self.mapping_slot)
        self.entries = list(self.entries)
        if not all(isinstance(entry, EvmHookMappingEntry) for entry in self.entries):
            raise TypeError("entries must be EvmHookMappingEntry instances.")

    def _to_proto(self) -> hook_types_pb2.EvmHookStorageUpdate:
        """Converts these mapping writes to their protobuf representation."""
        return hook_types_pb2.EvmHookStorageUpdate(
            mapping_entries=hook_types_pb2.EvmHookMappingEntries(
                mapping_slot=self.mapping_slot,
                entries=[entry._to_proto() for entry in self.entries],
            )
        )

    @classmethod
    def _from_entries_proto(cls, proto: hook_types_pb2.EvmHookMappingEntries) -> EvmHookMappingEntries:
        """Creates mapping writes from an EvmHookMappingEntries protobuf."""
        return cls(
            mapping_slot=proto.mapping_slot,
            entries=[EvmHookMappingEntry._from_proto(entry) for entry in proto.entries],
        )
