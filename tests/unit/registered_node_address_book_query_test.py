"""Unit tests for RegisteredNodeAddressBookQuery."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hiero_sdk_python.address_book.registered_node_address_book_query import (
    RegisteredNodeAddressBookQuery,
)


pytestmark = pytest.mark.unit


def test_execute_raises_until_mirror_node_api_exists():
    """The query skeleton should be explicit about its deferred status."""
    query = RegisteredNodeAddressBookQuery()

    with pytest.raises(
        NotImplementedError,
        match="RegisteredNodeAddressBookQuery is not available until the mirror node API is defined.",
    ):
        query.execute(MagicMock())
