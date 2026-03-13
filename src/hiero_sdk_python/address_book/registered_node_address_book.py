"""Collection type for registered nodes."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from hiero_sdk_python.address_book.registered_node import RegisteredNode


@dataclass(frozen=True)
class RegisteredNodeAddressBook:
    """A collection of registered nodes."""

    registered_nodes: tuple[RegisteredNode, ...] = field(default_factory=tuple)

    def __iter__(self) -> Iterator[RegisteredNode]:
        """Iterate over registered nodes."""
        return iter(self.registered_nodes)

    def __len__(self) -> int:
        """Return the number of registered nodes."""
        return len(self.registered_nodes)

    def __getitem__(self, index: int) -> RegisteredNode:
        """Return the registered node at the given index."""
        return self.registered_nodes[index]

    @classmethod
    def from_iterable(cls, registered_nodes: Iterable[RegisteredNode]) -> RegisteredNodeAddressBook:
        """Create an address book from any iterable of registered nodes."""
        return cls(tuple(registered_nodes))
