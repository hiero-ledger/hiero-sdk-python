"""
Integration tests for the ddressBookQuery class.
"""

from __future__ import annotations

import grpc
import pytest

from hiero_sdk_python.address_book.address_book_query import AddressBookQuery
from hiero_sdk_python.address_book.node_address_book import NodeAddressBook
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.file.file_id import FileId


@pytest.mark.integration
def test_address_book_query_can_be_executed(env):
    """Test that the AddressBookQuery return the NodeAddressBook."""
    address_book = (
        AddressBookQuery()
        .set_file_id(FileId.from_string("0.0.102"))  # address book query work with only "0.0.102" and "0.0.101" file_id
        .execute(env.client)
    )
    assert address_book is not None
    assert isinstance(address_book, NodeAddressBook)


@pytest.mark.integration
def test_address_book_query_with_client_operator_not_set(env):
    """Test that the AddressBookQuery return the NodeAddressBook when client operator not set."""
    address_book = (
        AddressBookQuery()
        .set_file_id(FileId.from_string("0.0.102"))  # address book query work with only "0.0.102" and "0.0.101" file_id
        .execute(Client.for_testnet())
    )
    assert address_book is not None
    assert isinstance(address_book, NodeAddressBook)


@pytest.mark.integration
def test_address_book_query_with_invalid_id_raise_error(env):
    """Test that the AddressBookQuery raise error if file id not 0.0.101 and 0.0.102."""
    query = AddressBookQuery().set_file_id(FileId.from_string("0.0.103"))

    with pytest.raises(grpc.RpcError):
        query.execute(env.client)


@pytest.mark.integration
def test_address_book_query_can_be_executed_with_limit(env):
    """Test that the AddressBookQuery return the NodeAddressBook with given limit."""
    # this will always return single node when run on solo, cause it contain single node
    address_book = AddressBookQuery().set_file_id(FileId.from_string("0.0.102")).set_limit(1).execute(env.client)
    assert address_book is not None
    assert isinstance(address_book, NodeAddressBook)
    assert len(address_book.node_addresses) == 1
