"""Registered general service endpoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hiero_sdk_python.address_book.registered_service_endpoint import (
    RegisteredServiceEndpoint,
)
from hiero_sdk_python.hapi.services.registered_service_endpoint_pb2 import (
    RegisteredServiceEndpoint as RegisteredServiceEndpointProto,
)


@dataclass(eq=True)
class GeneralServiceEndpoint(RegisteredServiceEndpoint):
    """A registered endpoint for a general-purpose service."""

    description: str | None = None
    MAX_DESCRIPTION_BYTES = 100

    def __post_init__(self) -> None:
        """Run base endpoint validation and validate optional description."""
        super().__post_init__()
        if self.description is not None and len(self.description.encode("utf-8")) > self.MAX_DESCRIPTION_BYTES:
            raise ValueError("description must not exceed 100 UTF-8 bytes.")

    @classmethod
    def _resolve_general_endpoint_descriptor(
        cls,
    ) -> tuple[str, type[Any]]:
        """Resolve the endpoint_type oneof entry and nested protobuf message for general endpoints."""
        endpoint_type_oneof = RegisteredServiceEndpointProto.DESCRIPTOR.oneofs_by_name.get("endpoint_type")
        if endpoint_type_oneof is None:
            raise NotImplementedError("RegisteredServiceEndpoint endpoint_type oneof is unavailable in this protobuf.")

        for field in endpoint_type_oneof.fields:
            message_type = field.message_type
            if message_type is not None and "General" in message_type.name:
                nested_type = getattr(RegisteredServiceEndpointProto, message_type.name, None)
                if nested_type is None:
                    raise NotImplementedError(
                        "General service endpoint nested protobuf type is unavailable in this protobuf."
                    )
                return field.name, nested_type

        raise NotImplementedError("General service endpoints are unavailable in this protobuf version.")

    def _endpoint_type_proto(self) -> dict[str, Any]:
        """Return the protobuf general-service subtype."""
        field_name, nested_type = self._resolve_general_endpoint_descriptor()
        endpoint_proto = nested_type()

        if self.description is not None:
            if not hasattr(endpoint_proto, "description"):
                raise NotImplementedError(
                    "General service endpoint descriptions are unavailable in this protobuf version."
                )
            endpoint_proto.description = self.description

        return {field_name: endpoint_proto}

    @classmethod
    def _from_proto(cls, proto: RegisteredServiceEndpointProto) -> GeneralServiceEndpoint:
        """Build a general service endpoint from protobuf."""
        field_name, _ = cls._resolve_general_endpoint_descriptor()
        endpoint_proto = getattr(proto, field_name)
        description = endpoint_proto.description if hasattr(endpoint_proto, "description") else None
        return cls(
            description=description or None,
            **cls._base_kwargs_from_proto(proto),
        )
