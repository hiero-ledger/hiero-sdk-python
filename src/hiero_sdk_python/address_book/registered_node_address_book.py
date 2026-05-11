"""Read-side container for a collection of registered nodes."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from hiero_sdk_python.address_book.registered_node import RegisteredNode


@dataclass(frozen=True)
class RegisteredNodeAddressBook:
    """Immutable container of :class:`RegisteredNode` entries.

    No protobuf ``RegisteredNodeAddressBook`` message exists in the current
    protobufs, so this is a pure SDK-side convenience wrapper that mirrors
    the role of the legacy ``NodeAddressBook`` model.
    """

    nodes: tuple[RegisteredNode, ...] = field(default_factory=tuple)

    def __post_init__(self):
        object.__setattr__(self, "nodes", tuple(self.nodes))

    def __len__(self) -> int:
        return len(self.nodes)

    def __iter__(self) -> Iterator[RegisteredNode]:
        return iter(self.nodes)

    def __getitem__(self, index: int) -> RegisteredNode:
        return self.nodes[index]

    def __repr__(self) -> str:
        return f"RegisteredNodeAddressBook(nodes={len(self.nodes)})"
