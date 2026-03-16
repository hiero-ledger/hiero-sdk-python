"""Composite key-list support."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hiero_sdk_python.hapi.services import basic_types_pb2

if TYPE_CHECKING:
    from hiero_sdk_python.utils.key_utils import Key


@dataclass(frozen=True)
class KeyList:
    """A protobuf-compatible list of keys."""

    keys: tuple[Key, ...] = field(default_factory=tuple)

    def __init__(self, keys: Iterable[Key] | None = None) -> None:
        """Initialize a key list from an iterable of SDK keys."""
        object.__setattr__(self, "keys", tuple(keys or ()))

    def __len__(self) -> int:
        """Return the number of child keys."""
        return len(self.keys)

    def _to_proto_key_list(self) -> basic_types_pb2.KeyList:
        """Convert this key list to its nested protobuf form."""
        from hiero_sdk_python.utils.key_utils import key_to_proto

        return basic_types_pb2.KeyList(keys=[key_to_proto(key) for key in self.keys])

    def _to_proto(self) -> basic_types_pb2.Key:
        """Convert this key list to a protobuf Key."""
        return basic_types_pb2.Key(keyList=self._to_proto_key_list())

    @classmethod
    def _from_proto_key_list(cls, proto: basic_types_pb2.KeyList) -> KeyList:
        """Build a key list from its nested protobuf form."""
        from hiero_sdk_python.utils.key_utils import key_from_proto

        return cls(keys=[key_from_proto(key) for key in proto.keys])
