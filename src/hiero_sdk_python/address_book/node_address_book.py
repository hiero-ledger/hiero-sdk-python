from __future__ import annotations

from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.hapi.services import basic_types_pb2


class NodeAddressBook:
    """
    A list of nodes and their metadata.

    See https://docs.hedera.com/reference/protobuf/basic-types/nodeaddressbook#nodeaddressbook
    """

    def __init__(self, node_addresses: list[NodeAddress] | None = None):
        self._node_addresses: list[NodeAddress] = []
        if node_addresses is not None:
            self.set_node_addresses(node_addresses)

    @property
    def node_addresses(self) -> list[NodeAddress]:
        """
        Return a copy of the node addresses in this address book.

        Returns:
            list[NodeAddress]: A copy of the node addresses.
        """
        return list(self._node_addresses)

    def set_node_addresses(self, node_addresses: list[NodeAddress]) -> NodeAddressBook:
        """
        Set the node addresses in this address book.

        Args:
            node_addresses (list[NodeAddress]): The node addresses to set.

        Returns:
            NodeAddressBook: This address book instance for method chaining.

        Raises:
            TypeError: If node_addresses is not a list of NodeAddress
        """
        if not isinstance(node_addresses, list):
            raise TypeError("node_addresses must be of type list[NodeAddress]")

        if not all(isinstance(node_address, NodeAddress) for node_address in node_addresses):
            raise TypeError("node_addresses must contain only NodeAddress instances")

        self._node_addresses = list(node_addresses)
        return self

    @classmethod
    def _from_proto(cls, book_proto: basic_types_pb2.NodeAddressBook) -> NodeAddressBook:
        """
        Create a NodeAddressBook from a protobuf NodeAddressBook message.

        Args:
            book_proto (basic_types_pb2.NodeAddressBook): The protobuf message containing node addresses.

        Returns:
            NodeAddressBook: A NodeAddressBook containing the node addresses from the protobuf message.
        """
        node_addresses = [NodeAddress._from_proto(node_address) for node_address in book_proto.nodeAddress]
        return cls(node_addresses)

    @classmethod
    def from_bytes(cls, data: bytes) -> NodeAddressBook:
        """
        Create a NodeAddressBook from serialized protobuf bytes.

        Args:
            data (bytes): The serialized NodeAddressBook protobuf data.

        Returns:
            NodeAddressBook: A NodeAddressBook created from the serialized data.

        Raises:
            TypeError: If data is not a bytes
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be of type bytes")

        return cls._from_proto(basic_types_pb2.NodeAddressBook.FromString(data))

    def _to_proto(self) -> basic_types_pb2.NodeAddressBook:
        """
        Convert this NodeAddressBook to a protobuf NodeAddressBook message.

        Returns:
            basic_types_pb2.NodeAddressBook: The protobuf message containing this node address book.
        """
        node_addresses = [node_address._to_proto() for node_address in self.node_addresses]
        return basic_types_pb2.NodeAddressBook(nodeAddress=node_addresses)

    def to_bytes(self) -> bytes:
        """
        Serialize this NodeAddressBook to protobuf bytes.

        Returns:
            bytes: The serialized NodeAddressBook protobuf data.
        """
        return self._to_proto().SerializeToString()
