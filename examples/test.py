from hiero_sdk_python.address_book.address_book_query import AddressBookQuery
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.file.file_id import FileId


def main():
    client = Client.from_env()

    for node in client.network.nodes:
        for env in node._address_book._addresses:
            print("\n")
            print(env)

    query = AddressBookQuery().set_file_id(FileId.from_string("0.0.102")).set_limit(2)

    print("------------------------\n\nTest\n\n")
    nodes = query.execute(client)
    print(len(nodes))
    for node in nodes:
        print(node)


if __name__ == "__main__":
    main()
