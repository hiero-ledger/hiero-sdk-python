"""Skeleton query for fetching the registered-node address book (HIP-1137)."""

from __future__ import annotations

from hiero_sdk_python.address_book.registered_node_address_book import RegisteredNodeAddressBook


class RegisteredNodeAddressBookQuery:
    """Query to retrieve the registered-node address book from the network.

    .. warning::

        Query execution is **not yet available**. The mirror-node API endpoint
        required by this query has not been implemented in this SDK release.
        Calling :meth:`execute` will raise :class:`NotImplementedError`.
    """

    def __init__(self) -> None:
        self._max_registered_node_count: int | None = None

    def set_max_registered_node_count(self, count: int) -> RegisteredNodeAddressBookQuery:
        """Limit the number of registered nodes returned.

        Args:
            count: Maximum number of nodes. Must be positive.

        Returns:
            This query instance for method chaining.
        """
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            raise ValueError("count must be a positive integer")
        self._max_registered_node_count = count
        return self

    def execute(self, client: object = None) -> RegisteredNodeAddressBook:
        """Execute the query against the network.

        Raises:
            NotImplementedError: Always. Mirror-node API support for
                registered-node queries is not yet available in this SDK.
        """
        raise NotImplementedError(
            "RegisteredNodeAddressBookQuery requires HIP-1137 mirror node API support, "
            "which is not yet available in this SDK."
        )
