"""TCK response models for node endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NodeResponse:
    """Represent the response for all the node related transaction."""

    nodeId: str | None = None
    status: str | None = None


@dataclass
class EndpointResponse:
    """Represent the Endpoint JSON-RPC response."""

    ipAddressV4: str | None = None
    port: int | None = None
    domainName: str | None = None


@dataclass
class NodeAddressResponse:
    """Represent the NodeAddress JSON-RPC response."""

    rsaPublicKey: str | None = None
    accountId: str | None = None
    nodeId: int | None = None
    nodeCertHash: str | None = None
    serviceEndpoints: list[EndpointResponse] | None = None
    description: str | None = None
    stake: int | None = None


@dataclass
class GetAddressBookResponse:
    """Respresent the response form the getAddressBook endpoint."""

    nodeAddresses: list[NodeAddressResponse] | None = None
