from __future__ import annotations

from hiero_sdk_python.address_book.registered_service_endpoint import RegisteredServiceEndpoint
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


class GeneralServiceEndpoint(RegisteredServiceEndpoint):
    """A registered service endpoint for a general service."""

    def __init__(
        self,
        ip_address: bytes | None = None,
        domain_name: str | None = None,
        port: int = 0,
        requires_tls: bool = False,
        description: str | None = None,
    ) -> None:
        super().__init__(ip_address=ip_address, domain_name=domain_name, port=port, requires_tls=requires_tls)
        if description is not None and len(description.encode("utf-8")) > 100:
            raise ValueError("description must be 100 UTF-8 bytes or fewer")
        self.description: str | None = description

    def _set_endpoint_type(self, proto: RegisteredServiceEndpointProto) -> None:
        if self.description is not None:
            proto.general_service.description = self.description
        else:
            proto.general_service.SetInParent()

    @classmethod
    def _from_proto_inner(
        cls,
        proto: RegisteredServiceEndpointProto,
        ip_address: bytes | None,
        domain_name: str | None,
        port: int,
        requires_tls: bool,
    ) -> GeneralServiceEndpoint:
        desc = proto.general_service.description or None
        return cls(
            ip_address=ip_address,
            domain_name=domain_name,
            port=port,
            requires_tls=requires_tls,
            description=desc,
        )

    @classmethod
    def _from_dict_inner(cls, type_data: dict, **base_kwargs) -> GeneralServiceEndpoint:
        """Build from the ``general_service`` sub-dict of a mirror-node JSON endpoint."""
        desc = type_data.get("description") or None
        return cls(description=desc, **base_kwargs)
