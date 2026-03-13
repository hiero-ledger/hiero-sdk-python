"""Unit tests for RegisteredNodeAddressBook."""

from dataclasses import FrozenInstanceError

import pytest

from hiero_sdk_python.address_book.registered_node import RegisteredNode
from hiero_sdk_python.address_book.registered_node_address_book import (
    RegisteredNodeAddressBook,
)

pytestmark = pytest.mark.unit


def test_registered_node_address_book_iteration_and_indexing():
    """The address book should behave like a small immutable collection."""
    first = RegisteredNode(registered_node_id=1)
    second = RegisteredNode(registered_node_id=2)

    address_book = RegisteredNodeAddressBook.from_iterable([first, second])

    assert len(address_book) == 2
    assert list(address_book) == [first, second]
    assert address_book[0] == first
    assert address_book[1] == second


def test_registered_node_address_book_is_immutable():
    """The address book dataclass should be immutable."""
    address_book = RegisteredNodeAddressBook.from_iterable([RegisteredNode(registered_node_id=1)])

    with pytest.raises(FrozenInstanceError):
        address_book.registered_nodes = ()
