"""Read-side container for a collection of HIP-1137 registered nodes."""

from __future__ import annotations

from collections.abc import Iterator

from hiero_sdk_python.address_book.registered_node import RegisteredNode


class RegisteredNodeAddressBook:
    """Immutable container of :class:`RegisteredNode` entries.

    No protobuf ``RegisteredNodeAddressBook`` message exists in the current
    protobufs, so this is a pure SDK-side convenience wrapper that mirrors
    the role of the legacy ``NodeAddressBook`` model.
    """

    def __init__(self, nodes: tuple[RegisteredNode, ...] = ()) -> None:
        self._nodes = tuple(nodes)

    @property
    def nodes(self) -> tuple[RegisteredNode, ...]:
        return self._nodes

    def __len__(self) -> int:
        return len(self._nodes)

    def __iter__(self) -> Iterator[RegisteredNode]:
        return iter(self._nodes)

    def __getitem__(self, index: int) -> RegisteredNode:
        return self._nodes[index]

    def __repr__(self) -> str:
        return f"RegisteredNodeAddressBook(nodes={len(self._nodes)})"
