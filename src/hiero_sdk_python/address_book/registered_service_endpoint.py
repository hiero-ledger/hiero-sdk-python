from __future__ import annotations

from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class RegisteredServiceEndpoint:
    """Base SDK model for a registered service endpoint."""

    def __init__(
        self,
        ip_address: bytes | None = None,
        domain_name: str | None = None,
        port: int = 0,
        requires_tls: bool = False,
    ) -> None:
        self._validate_address_init(ip_address, domain_name)
        self._validate_port(port)
        if not isinstance(requires_tls, bool):
            raise ValueError("requires_tls must be a bool")

        self.ip_address: bytes | None = ip_address
        self.domain_name: str | None = domain_name
        self.port: int = port
        self.requires_tls: bool = requires_tls

    def set_ip_address(self, ip_address: bytes) -> RegisteredServiceEndpoint:
        """Set the IP address, clearing any existing domain name."""
        self._validate_ip_address(ip_address)
        self.ip_address = ip_address
        self.domain_name = None
        return self

    def set_domain_name(self, domain_name: str) -> RegisteredServiceEndpoint:
        """Set the domain name, clearing any existing IP address."""
        self._validate_domain_name(domain_name)
        self.domain_name = domain_name
        self.ip_address = None
        return self

    def set_port(self, port: int) -> RegisteredServiceEndpoint:
        """Set the port number."""
        self._validate_port(port)
        self.port = port
        return self

    def set_requires_tls(self, requires_tls: bool) -> RegisteredServiceEndpoint:
        """Set whether TLS is required."""
        if not isinstance(requires_tls, bool):
            raise ValueError("requires_tls must be a bool")
        self.requires_tls = requires_tls
        return self

    @staticmethod
    def _validate_address_init(ip_address: bytes | None, domain_name: str | None) -> None:
        """Validate address arguments at construction time.

        Allows both to be ``None`` so that the builder/setter pattern works::

            endpoint = BlockNodeServiceEndpoint().set_domain_name("example.com")

        Rejects providing *both* at the same time.
        """
        if ip_address is not None and domain_name is not None:
            raise ValueError("Exactly one of ip_address or domain_name must be provided, not both")
        if ip_address is not None:
            RegisteredServiceEndpoint._validate_ip_address(ip_address)
        if domain_name is not None:
            RegisteredServiceEndpoint._validate_domain_name(domain_name)

    @staticmethod
    def _validate_ip_address(ip_address: bytes) -> None:
        if not isinstance(ip_address, bytes) or len(ip_address) not in (4, 16):
            raise ValueError("ip_address must be 4 bytes (IPv4) or 16 bytes (IPv6)")

    @staticmethod
    def _validate_domain_name(domain_name: str) -> None:
        if not isinstance(domain_name, str):
            raise ValueError("domain_name must be a string")
        try:
            domain_name.encode("ascii")
        except UnicodeEncodeError as err:
            raise ValueError("domain_name must be ASCII") from err
        if len(domain_name) > 250:
            raise ValueError("domain_name must be 250 characters or fewer")

    @staticmethod
    def _validate_port(port: int) -> None:
        if not isinstance(port, int) or isinstance(port, bool):
            raise ValueError("port must be an int")
        if port < 0 or port > 65535:
            raise ValueError("port must be in range 0 to 65535")

    def _to_proto(self) -> RegisteredServiceEndpointProto:
        if self.ip_address is None and self.domain_name is None:
            raise ValueError("Exactly one of ip_address or domain_name must be set before serialization")
        proto = RegisteredServiceEndpointProto(
            port=self.port,
            requires_tls=self.requires_tls,
        )
        if self.ip_address is not None:
            proto.ip_address = self.ip_address
        else:
            proto.domain_name = self.domain_name

        self._set_endpoint_type(proto)
        return proto

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        """Subclasses override to set the endpoint_type oneof field."""

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> RegisteredServiceEndpoint:
        """Deserialize from protobuf, returning the appropriate subclass."""
        from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
        from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
        from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
        from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint

        ip_address: bytes | None = None
        domain_name: str | None = None
        address_field = proto.WhichOneof("address")
        if address_field == "ip_address":
            ip_address = proto.ip_address
        elif address_field == "domain_name":
            domain_name = proto.domain_name

        port = proto.port
        requires_tls = proto.requires_tls

        endpoint_type = proto.WhichOneof("endpoint_type")
        if endpoint_type == "block_node":
            return BlockNodeServiceEndpoint._from_proto_inner(proto, ip_address, domain_name, port, requires_tls)
        if endpoint_type == "mirror_node":
            return MirrorNodeServiceEndpoint._from_proto_inner(proto, ip_address, domain_name, port, requires_tls)
        if endpoint_type == "rpc_relay":
            return RpcRelayServiceEndpoint._from_proto_inner(proto, ip_address, domain_name, port, requires_tls)
        if endpoint_type == "general_service":
            return GeneralServiceEndpoint._from_proto_inner(proto, ip_address, domain_name, port, requires_tls)
        raise ValueError(f"Unknown endpoint_type: {endpoint_type!r}")

    @classmethod
    def _from_dict(cls, data: dict) -> RegisteredServiceEndpoint:
        """Deserialize from a mirror-node JSON dict, returning the appropriate subclass."""
        from hiero_sdk_python.address_book.block_node_service_endpoint import BlockNodeServiceEndpoint
        from hiero_sdk_python.address_book.general_service_endpoint import GeneralServiceEndpoint
        from hiero_sdk_python.address_book.mirror_node_service_endpoint import MirrorNodeServiceEndpoint
        from hiero_sdk_python.address_book.rpc_relay_service_endpoint import RpcRelayServiceEndpoint

        ip_address: bytes | None = None
        domain_name: str | None = data.get("domain_name") or None

        raw_ip = data.get("ip_address")
        if raw_ip:
            import ipaddress as _ipaddress

            ip_address = _ipaddress.ip_address(raw_ip).packed

        port = data.get("port", 0)
        requires_tls = data.get("requires_tls", False)

        ep_type = (data.get("type") or "").upper()

        base_kwargs = dict(ip_address=ip_address, domain_name=domain_name, port=port, requires_tls=requires_tls)

        if ep_type == "BLOCK_NODE":
            return BlockNodeServiceEndpoint._from_dict_inner(data.get("block_node", {}), **base_kwargs)
        if ep_type == "MIRROR_NODE":
            return MirrorNodeServiceEndpoint._from_dict_inner(data.get("mirror_node", {}), **base_kwargs)
        if ep_type == "RPC_RELAY":
            return RpcRelayServiceEndpoint._from_dict_inner(data.get("rpc_relay", {}), **base_kwargs)
        if ep_type == "GENERAL_SERVICE":
            return GeneralServiceEndpoint._from_dict_inner(data.get("general_service", {}), **base_kwargs)
        raise ValueError(f"Unknown endpoint type from mirror node: {ep_type!r}")
