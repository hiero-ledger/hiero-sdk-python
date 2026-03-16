"""Base type for registered service endpoints."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from typing import Any

from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)

_DOMAIN_LABEL_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


@dataclass(eq=True)
class RegisteredServiceEndpoint:
    """Shared fields for a registered node service endpoint."""

    ip_address: bytes | None = None
    domain_name: str | None = None
    port: int = 0
    requires_tls: bool = False

    def __post_init__(self) -> None:
        """Validate fields after dataclass initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate the common endpoint fields."""
        has_ip_address = self.ip_address is not None
        has_domain_name = self.domain_name is not None

        if has_ip_address == has_domain_name:
            raise ValueError("Exactly one of ip_address or domain_name must be set.")

        if not 0 <= self.port <= 65535:
            raise ValueError("port must be between 0 and 65535.")

        if self.ip_address is not None:
            self._validate_ip_address()

        if self.domain_name is not None:
            self._validate_domain_name()

    def _validate_ip_address(self) -> None:
        """Validate the packed IP address bytes."""
        try:
            ipaddress.ip_address(self.ip_address)
        except ValueError as exc:
            raise ValueError("ip_address must be a valid packed IPv4 or IPv6 address.") from exc

    def _validate_domain_name(self) -> None:
        """Validate the endpoint domain name."""
        domain_name = self.domain_name
        self._validate_domain_name_presence(domain_name)
        self._validate_domain_name_length_and_ascii(domain_name)
        normalized_domain = self._normalize_domain_name(domain_name)
        self._validate_domain_labels(normalized_domain)

    def _validate_domain_name_presence(self, domain_name: str | None) -> None:
        """Ensure the domain name is present."""
        if not domain_name:
            raise ValueError("domain_name must not be empty.")

    def _validate_domain_name_length_and_ascii(self, domain_name: str) -> None:
        """Ensure the domain name length and charset are valid."""
        if len(domain_name) > 250:
            raise ValueError("domain_name must not exceed 250 ASCII characters.")

        try:
            domain_name.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError("domain_name must contain only ASCII characters.") from exc

    def _normalize_domain_name(self, domain_name: str) -> str:
        """Normalize a domain name for validation."""
        normalized_domain = domain_name[:-1] if domain_name.endswith(".") else domain_name
        if not normalized_domain:
            raise ValueError("domain_name must not be empty.")

        return normalized_domain

    def _validate_domain_labels(self, normalized_domain: str) -> None:
        """Validate each label in the normalized domain name."""
        labels = normalized_domain.split(".")
        if any(not label for label in labels):
            raise ValueError("domain_name must be a valid domain name.")

        for label in labels:
            if not _DOMAIN_LABEL_RE.fullmatch(label):
                raise ValueError("domain_name must be a valid domain name.")

    @classmethod
    def _base_kwargs_from_proto(cls, proto: RegisteredServiceEndpointProto) -> dict[str, Any]:
        """Extract the common constructor kwargs from protobuf."""
        address_type = proto.WhichOneof("address")
        if address_type == "ip_address":
            return {
                "ip_address": proto.ip_address,
                "domain_name": None,
                "port": proto.port,
                "requires_tls": proto.requires_tls,
            }

        if address_type == "domain_name":
            return {
                "ip_address": None,
                "domain_name": proto.domain_name,
                "port": proto.port,
                "requires_tls": proto.requires_tls,
            }

        raise ValueError("Registered service endpoint address is required.")

    def _endpoint_type_proto(self) -> dict[str, Any]:
        """Return the endpoint-type-specific protobuf field."""
        raise NotImplementedError("Subclasses must implement _endpoint_type_proto().")

    def _to_proto(self) -> RegisteredServiceEndpointProto:
        """Convert the endpoint to protobuf."""
        proto_kwargs = {
            "port": self.port,
            "requires_tls": self.requires_tls,
            **self._endpoint_type_proto(),
        }

        if self.ip_address is not None:
            proto_kwargs["ip_address"] = self.ip_address
        else:
            proto_kwargs["domain_name"] = self.domain_name

        return RegisteredServiceEndpointProto(**proto_kwargs)

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> RegisteredServiceEndpoint:
        """Build the concrete endpoint type from protobuf."""
        endpoint_type = proto.WhichOneof("endpoint_type")

        if endpoint_type == "block_node":
            from hiero_sdk_python.address_book.block_node_service_endpoint import (
                BlockNodeServiceEndpoint,
            )

            return BlockNodeServiceEndpoint._from_proto(proto)

        if endpoint_type == "mirror_node":
            from hiero_sdk_python.address_book.mirror_node_service_endpoint import (
                MirrorNodeServiceEndpoint,
            )

            return MirrorNodeServiceEndpoint._from_proto(proto)

        if endpoint_type == "rpc_relay":
            from hiero_sdk_python.address_book.rpc_relay_service_endpoint import (
                RpcRelayServiceEndpoint,
            )

            return RpcRelayServiceEndpoint._from_proto(proto)

        raise ValueError("Registered service endpoint type is required.")
