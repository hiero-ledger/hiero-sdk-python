from __future__ import annotations

import time

import grpc

from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.exceptions import MaxAttemptsError
from hiero_sdk_python.executable import RST_STREAM
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.mirror import mirror_network_service_pb2
from hiero_sdk_python.hapi.mirror.mirror_network_service_pb2_grpc import NetworkServiceStub


class AddressBookQuery:
    def __init__(self):
        self._file_id: FileId | None = None
        self._limit: int | None = None
        self._max_attempts: int = 10
        self._max_backoff: int = 8

    @property
    def file_id(self) -> FileId | None:
        return self._file_id

    def set_file_id(self, file_id: FileId) -> AddressBookQuery:
        if not isinstance(file_id, FileId):
            raise TypeError("file_id must be of type FileId")

        self._file_id = file_id
        return self

    @property
    def limit(self) -> int | None:
        return self._limit

    def set_limit(self, limit: int) -> AddressBookQuery:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be of type int")

        self._limit = limit
        return self

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    def set_max_attempts(self, max_attempts: int) -> AddressBookQuery:
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int):
            raise TypeError("max_attempts must be of type int")

        self._max_attempts = max_attempts
        return self

    @property
    def max_backoff(self) -> int:
        return self._max_backoff

    def set_max_backoff(self, max_backoff: int) -> AddressBookQuery:
        if isinstance(max_backoff, bool) or not isinstance(max_backoff, int):
            raise TypeError("max_backoff must be of type int")

        self._max_backoff = max_backoff
        return self

    def _make_request(self) -> mirror_network_service_pb2.AddressBookQuery:
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

        return True

    def execute(self, client: Client, timeout: float | None = None) -> list[NodeAddress]:
        network_stub = NetworkServiceStub(client.mirror_channel)
        request = self._make_request()

        if timeout is None:
            timeout = client._request_timeout

        start = time.monotonic()

        for attempt in range(self._max_attempts):
            if time.monotonic() - start >= timeout:
                break

            try:
                nodes = network_stub.getNodes(request)
                return [NodeAddress._from_proto(node) for node in nodes]
            except Exception as e:
                if not self._should_retry(e):
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
        backoff = min(self._max_backoff, 0.5 * (2 ** (attempt + 1)))
        time.sleep(backoff)
