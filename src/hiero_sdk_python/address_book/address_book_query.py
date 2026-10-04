from __future__ import annotations

import time

import grpc

from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.address_book.node_address_book import NodeAddressBook
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.executable import RST_STREAM
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.mirror import mirror_network_service_pb2
from hiero_sdk_python.hapi.mirror.mirror_network_service_pb2_grpc import NetworkServiceStub


class AddressBookQuery:
    def __init__(self, file_id: FileId | None = None, limit: int | None = None):
        """
        Create an address book query.

        Args:
            file_id (FileId | None): file ID containing the address book.
            limit (int | None): maximum number of node addresses to retrieve.
                A value of 0 retrieves all available node addresses.
        """
        self._file_id: FileId | None = None
        if file_id is not None:
            self.set_file_id(file_id)

        self._limit: int | None = None
        if limit is not None:
            self.set_limit(limit)

        self._max_attempts: int = 10
        self._max_backoff: float = 8  # 8 seconds

    @property
    def file_id(self) -> FileId | None:
        """Return the file ID used for the address book query."""
        return self._file_id

    def set_file_id(self, file_id: FileId) -> AddressBookQuery:
        """
        Set the file ID used for the address book query.

        Args:
            file_id: The ID of the file containing the address book.

        Returns:
            The current instance of the class for chaining.

        Raises:
            TypeError: If file_id is not a FileId.
        """
        if not isinstance(file_id, FileId):
            raise TypeError("file_id must be of type FileId")

        self._file_id = file_id
        return self

    @property
    def limit(self) -> int | None:
        """Return the maximum number of node addresses to retrieve."""
        return self._limit

    def set_limit(self, limit: int) -> AddressBookQuery:
        """
        Set the maximum number of node addresses to retrieve.
        A value of 0 indicates that all available node addresses should be retrieved.

        Args:
            limit (int): Maximum number of node addresses to retrieve.

        Returns:
            The current instance of the class for chaining.

        Raises:
            TypeError: If limit is not an integer.
            ValueError: If limit is negative.
        """
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be of type int")

        if limit < 0:
            raise ValueError("limit must be greater than -1")

        self._limit = limit
        return self

    @property
    def max_attempts(self) -> int:
        """Return the maximum number of retry attempts."""
        return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> AddressBookQuery:
        """
        Set the maximum number of attempts for retrieving the address book.

        Args:
            max_attempts (int): Maximum number of attempts. Must be at least 1.

        Returns:
            The current instance of the class for chaining.

        Raises:
            TypeError: If max_attempts is not an integer.
            ValueError: If max_attempts is less than 1.
        """
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise TypeError("max_attempts must be of type int")

        if max_attempts < 1:
            raise ValueError("max_attempt must be greater than or equal to 1")

        self._max_attempts = max_attempts
        return self

    @property
    def max_backoff(self) -> int:
        """Return the maximum retry backoff duration in seconds."""
        return self._max_backoff

    def set_max_backoff(self, max_backoff: int) -> AddressBookQuery:
        """
        Set the maximum retry backoff duration.

        Args:
            max_backoff (int | float): Maximum backoff duration, in seconds.
                Must be at least 0.5 seconds.

        Returns:
            The current instance of the class for chaining.

        Raises:
            TypeError: If max_backoff is not an integer or float.
            ValueError: If max_backoff is less than 0.5 seconds.
        """
        if isinstance(max_backoff, bool) or not isinstance(max_backoff, (int, float)):
            raise TypeError("max_backoff must be of type int or float")

        if max_backoff < 0.5:
            raise ValueError("max_backoff must be at least 0.5s")

        self._max_backoff = max_backoff
        return self

    def _make_request(self) -> mirror_network_service_pb2.AddressBookQuery:
        """Build protobuf request for addressBook query."""
        request = mirror_network_service_pb2.AddressBookQuery()

        if self._file_id is not None:
            request.file_id.CopyFrom(self._file_id._to_proto())

        if self._limit is not None:
            request.limit = self._limit

        return request

    def _should_retry(self, err: Exception) -> bool:
        """
        Determine whether a gRPC error represents a failure that should be
        retried using exponential backoff.
        """
        if isinstance(err, grpc.RpcError):
            return err.code() in (
                grpc.StatusCode.UNAVAILABLE,
                grpc.StatusCode.RESOURCE_EXHAUSTED,
            ) or (err.code() == grpc.StatusCode.INTERNAL and bool(RST_STREAM.search(err.details())))

        return False

    def execute(self, client: Client, timeout: int | float | None = None) -> NodeAddressBook:
        """
        Execute the AddressBook query with user supplied timeout.

        Args:
            client (Client): The client instance to use for execution.
            timeout (int | float | None, optional): The total execution timeout (in seconds) for this execution.

        Returns:
            NodeAddressBook: The instance of NodeAddressBook.

        Raises:
            MaxAttemptsError: If the query fails after the maximum number of attempts or timeout
        """
        if not isinstance(client, Client):
            raise TypeError("client must be an instance of Client")

        if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, (int, float))):
            raise TypeError("timeout must be a int or float")

        logger = client.logger

        network_stub = NetworkServiceStub(client.mirror_channel)
        request = self._make_request()

        if timeout is None:
            timeout = client._request_timeout

        start = time.monotonic()

        for attempt in range(1, self._max_attempts + 1):
            if time.monotonic() - start >= timeout:
                break

            try:
                nodes = network_stub.getNodes(request)
                return NodeAddressBook([NodeAddress._from_proto(node) for node in nodes])
            except Exception as e:
                if not self._should_retry(e):
                    logger.error("Error attempting to get address book", "file_id", self.file_id, "error", e)
                    raise e

                if attempt >= self._max_attempts:
                    raise MaxAttemptsError("Exceeded maximum attempts") from e

                self._delay_for_attempt(attempt)

        raise MaxAttemptsError("Exceeded maximum attempts or request timeout")

    def _delay_for_attempt(self, attempt: int) -> None:
        """
        Delay for the specified backoff period before retrying.

        Args:
            attempt (int): The current attempt number (0-based)
            backoff (float): The current backoff period in seconds
        """
        backoff = min(self._max_backoff, 0.5 * (2**attempt))
        time.sleep(backoff)
