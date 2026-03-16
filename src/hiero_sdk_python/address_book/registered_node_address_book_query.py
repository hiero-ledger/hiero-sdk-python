"""Deferred registered node address book query."""

from hiero_sdk_python.address_book.registered_node_address_book import (
    RegisteredNodeAddressBook,
)
from hiero_sdk_python.client.client import Client


class RegisteredNodeAddressBookQuery:
    """Query contract for registered nodes once mirror support exists."""

    def execute(self, client: Client) -> RegisteredNodeAddressBook:
        """Execute the query once the mirror node API exists."""
        raise NotImplementedError(
            "RegisteredNodeAddressBookQuery is not available until the mirror node API is defined."
        )
