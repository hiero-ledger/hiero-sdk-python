from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar


T = TypeVar("T")


class _LockableList(Generic[T]):
    """A mutable list with lock to prevent further modifications."""

    def __init__(self):
        """Initialize an empty, unlocked list."""
        self._items: list[T] = []
        self._index: int = 0
        self._locked: bool = False

    def _require_not_locked(self) -> None:
        """Raise an exception if the list is locked."""
        if self._locked:
            raise RuntimeError("list is unmutable")

    def set_list(self, items: list[T]) -> _LockableList[T]:
        """Replace the contents of the list and reset the current index."""
        self._require_not_locked()
        self._items = list(items)
        self._index = 0
        return self

    def get_list(self) -> list[T]:
        """Return the underlying list."""
        return self._items.copy()

    def append(self, item: T) -> _LockableList[T]:
        """Append an item to the list."""
        self._require_not_locked()
        self._items.append(item)
        return self

    def extend(self, items: Iterable[T]) -> _LockableList[T]:
        """Append all items from an iterable to the list."""
        self._require_not_locked()
        self._items.extend(items)
        return self

    def clear(self) -> _LockableList[T]:
        """Remove all items from the list."""
        self._require_not_locked()
        self._items.clear()
        self._index = 0
        return self

    def get(self, index: int) -> T:
        """Return the item at the given index."""
        return self._items[index]

    def set(self, index: int, item: T) -> _LockableList[T]:
        """Set or append an item at the given index."""
        self._require_not_locked()

        if index == len(self._items):
            self._items.append(item)
        else:
            self._items[index] = item

        return self

    def set_if_absent(self, index: int, item: T) -> _LockableList[T]:
        """Set an item if the position is missing or contains None."""
        if index == len(self._items) or self._items[index] is None:
            self.set(index, item)

        return self

    def advance(self) -> int:
        """Advance the current index and return the previous index."""
        current_index = self._index

        if self._items:
            self._index = (self._index + 1) % len(self._items)
        return current_index

    def set_lock(self, val: bool) -> _LockableList[T]:
        """Lock or unlock the list."""
        self._locked = val
        return self

    def set_index(self, val: int) -> _LockableList[T]:
        """Set the current index."""
        self._index = val
        return self

    @property
    def index(self) -> int:
        """Return the current index."""
        return self._index

    @property
    def current(self) -> T:
        """Return the current item."""
        return self.get(self._index)

    @property
    def next(self) -> T:
        """Advance to the next item and return it."""
        return self.get(self.advance())

    @property
    def is_empty(self) -> bool:
        """Return ``True`` if the list contains no items."""
        return not self._items

    def __len__(self) -> int:
        """Return the number of items in the list."""
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over the list."""
        return iter(self._items)
