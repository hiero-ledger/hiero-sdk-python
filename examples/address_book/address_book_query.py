"""
Address Book Query Example.

This example demonstrates how to query the network address book using
AddressBookQuery(), both with and without an operator account.

Run with:
uv run -m examples.address_book.address_book_query
python -m examples.address_book.address_book_query
"""

import sys

from hiero_sdk_python.address_book.address_book_query import AddressBookQuery
from hiero_sdk_python.address_book.node_address_book import NodeAddressBook
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.file.file_id import FileId


def query_address_book(client: Client) -> NodeAddressBook:
    """Query the network address book."""
    return (
        AddressBookQuery()
        .set_file_id(FileId.from_string("0.0.102"))
        .set_limit(2)  # this will return single node when run on solo, cause it contain single node
        .execute(client)
    )


def print_address_book(address_book: NodeAddressBook) -> None:
    """Print the nodes returned by the address book query."""
    print("NodeAddressBook:")
    for node_address in address_book.node_addresses:
        print(f"{node_address}")


def main() -> None:
    try:
        # Query using a client configured from environment variables.
        print("=== Address Book Query with Operator ===")
        client = Client.from_env()
        print(f"Operator account: {client.operator_account_id}")

        address_book = query_address_book(client)
        print_address_book(address_book)

        # Query using a client without an operator account.
        # AddressBookQuery does not require an operator to execute.
        print("\n=== Address Book Query without Operator ===")
        client = Client(network=Network(network="solo"))

        address_book = query_address_book(client)
        print_address_book(address_book)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
