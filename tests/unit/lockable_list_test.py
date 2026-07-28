from __future__ import annotations

import pytest

from hiero_sdk_python.lockable_list import _LockableList


pytestmark = pytest.mark.unit


def test_list_initialization():
    """Test a new created list is empty."""
    lst = _LockableList[int]()

    assert lst.is_empty
    assert len(lst) == 0
    assert lst.get_list() == []


def test_set_list():
    """Test set_list() replace the list contents."""
    lst = _LockableList[int]().set_list([1, 2, 3])

    assert lst.get_list() == [1, 2, 3]
    assert lst.current == 1


def test_set_list_resets_index():
    """Test set_list() resets the current index."""
    lst = _LockableList[int]()
    lst.set_list([1, 2, 3])
    assert lst.get_list() == [1, 2, 3]

    lst.set_index(2)
    lst.set_list([10, 20])

    assert lst.get_list() == [10, 20]
    assert lst.current == 10


def test_append():
    """Test appending an item."""
    lst = _LockableList[int]()

    returned = lst.append(1).append(2)

    assert returned is lst
    assert lst.get_list() == [1, 2]


def test_extend():
    """Test extending the list with multiple items."""
    lst = _LockableList[int]()

    returned = lst.extend([1, 2, 3])

    assert returned is lst
    assert lst.get_list() == [1, 2, 3]


def test_extend_append_with_existing_items():
    """Test extending the multiple items with list contents not empty."""
    lst = _LockableList[int]()
    lst.set_list([1, 2])

    assert lst.get_list() == [1, 2]

    returned = lst.extend([3, 4])

    assert returned is lst
    assert lst.get_list() == [1, 2, 3, 4]


def test_clear():
    """Test clearing all items."""
    lst = _LockableList[int]().set_list([1, 2])
    assert lst.get_list() == [1, 2]

    lst.clear()

    assert lst.is_empty


def test_get():
    """Test retrieving an item by index."""
    lst = _LockableList[int]().set_list([5, 6])

    assert lst.get(0) == 5
    assert lst.get(1) == 6


def test_get_invalid_index():
    """Test get() raises IndexError for an invalid index."""
    lst = _LockableList[int]()

    with pytest.raises(IndexError):
        lst.get(0)


def test_set_existing_index():
    """Test replacing an existing item."""
    lst = _LockableList[int]().set_list([1, 2])
    lst.set(1, 99)

    assert lst.get_list() == [1, 99]


def test_set_append():
    """Test appending when index equals the list length."""
    lst = _LockableList[int]().set_list([1])
    lst.set(1, 2)

    assert lst.get_list() == [1, 2]


def test_set_invalid_index():
    """Test set() raises IndexError when the index is too large."""
    lst = _LockableList[int]().set_list([1])

    with pytest.raises(IndexError):
        lst.set(5, 10)


def test_set_if_absent_appends():
    """Test set_if_absent() appends a missing item."""
    lst = _LockableList[int]()

    lst.set_if_absent(0, 5)

    assert lst.get_list() == [5]


def test_set_if_absent_sets_none():
    """Test set_if_absent() replaces a None value."""
    lst = _LockableList[int | None]().set_list([None])

    lst.set_if_absent(0, 10)

    assert lst.get_list() == [10]


def test_set_if_absent_does_not_replace_existing():
    """Test set_if_absent() leaves existing values unchanged."""
    lst = _LockableList[int]().set_list([1])

    lst.set_if_absent(0, 2)

    assert lst.get_list() == [1]


def test_current():
    """Test retrieving the current item."""
    lst = _LockableList[int]().set_list([1, 2, 3])
    assert lst.current == 1

    lst.set_index(2)
    assert lst.current == 3


def test_advance():
    """Test advancing to the next item."""
    lst = _LockableList[int]().set_list([1, 2, 3])

    assert lst.advance() == 0
    assert lst.current == 2


def test_advance_wraps():
    """Test advance() wraps to the beginning."""
    lst = _LockableList[int]().set_list([1, 2])
    lst.set_index(1)

    assert lst.advance() == 1
    assert lst.current == 1


def test_advance_empty():
    """Test advance() on an empty list."""
    lst = _LockableList[int]()

    assert lst.advance() == 0
    assert lst.is_empty


def test_next():
    """Test the next property advances the current index."""
    lst = _LockableList[int]().set_list([1, 2, 3])

    assert lst.next == 1
    assert lst.current == 2


def test_set_index():
    """Test updating the current index."""
    lst = _LockableList[int]().set_list([1, 2, 3])
    lst.set_index(2)

    assert lst.current == 3


def test_len():
    """Test retrieving the list length."""
    lst = _LockableList[int]().set_list([1, 2, 3])

    assert len(lst) == 3


def test_iter():
    """Test iterating over the list."""
    lst = _LockableList[int]().set_list([1, 2, 3])

    assert list(lst) == [1, 2, 3]


def test_append_locked():
    """Test append() raises RuntimeError when the list is locked."""
    lst = _LockableList[int]().set_lock(True)

    with pytest.raises(RuntimeError):
        lst.append(1)


def test_extend_locked():
    """Test extend() raises RuntimeError when the list is locked."""
    lst = _LockableList[int]().set_lock(True)

    with pytest.raises(RuntimeError):
        lst.extend([1])


def test_set_list_locked():
    """Test set_list() raises RuntimeError when the list is locked."""
    lst = _LockableList[int]().set_lock(True)

    with pytest.raises(RuntimeError):
        lst.set_list([1])


def test_clear_locked():
    """Test clear() raises RuntimeError when the list is locked."""
    lst = _LockableList[int]().set_list([1]).set_lock(True)

    with pytest.raises(RuntimeError):
        lst.clear()


def test_set_locked():
    """Test set() raises RuntimeError when the list is locked."""
    lst = _LockableList[int]().set_list([1]).set_lock(True)

    with pytest.raises(RuntimeError):
        lst.set(0, 2)
