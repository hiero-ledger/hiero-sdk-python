from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar


T = TypeVar("T")


class _LockableList(Generic[T]):
    def __init__(self):
        self._items: list[T] = []
        self._index: int = 0
        self._locked: bool = False

    def _required_not_locked(self) -> None:
        if self._locked:
            raise RuntimeError("list in unmutable")

    def set_list(self, items: list[T]) -> _LockableList[T]:
        self._required_not_locked()
        self._items = list(items)
        self._index = 0
        return self

    def get_list(self) -> list[T]:
        return self._items

    def append(self, item: T) -> _LockableList[T]:
        self._required_not_locked()
        self._items.append(item)
        return self

    def extend(self, items: Iterable[T]) -> _LockableList[T]:
        self._required_not_locked()
        self._items.extend(items)
        return self

    def clear(self) -> _LockableList[T]:
        self._require_not_locked()
        self._items.clear()
        return self

    def get(self, index: int) -> T:
        return self._items[index]

    def set(self, index: int, item: T) -> _LockableList[T]:
        self._require_not_locked()

        if index == len(self._items):
            self._items.append(item)
        else:
            self._items[index] = item

        return self

    def set_if_absent(self, index: int, item: T) -> _LockableList[T]:
        if index == len(self._items) or self._items[index] is None:
            self.set(index, item)

        return self

    def advance(self) -> int:
        current_index = self._index

        if self._items:
            self._index = (self._index + 1) % len(self._items)
        return current_index

    def set_lock(self, val: bool) -> _LockableList[T]:
        self._locked = val
        return self

    @property
    def current(self) -> T:
        return self.get(self._index)

    @property
    def next(self) -> T:
        return self.get(self.advance())

    @property
    def is_empty(self) -> bool:
        return not self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)
