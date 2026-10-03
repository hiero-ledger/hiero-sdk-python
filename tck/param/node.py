"""TCK request parameter models for node endpoints."""

from __future__ import annotations

from dataclasses import dataclass

from hiero_sdk_python.address_book.endpoint import Endpoint
from tck.param.base import BaseTransactionParams
from tck.util.param_utils import parse_common_transaction_params, parse_session_id, to_bool, to_int


@dataclass
class CreateNodeParams(BaseTransactionParams):
    """Request parameters for createNode endpoint."""

    accountId: str | None = None
    description: str | None = None
    gossipEndpoints: list[ServiceEndpointParams] | None = None
    serviceEndpoints: list[ServiceEndpointParams] | None = None
    gossipCaCertificate: str | None = None
    grpcCertificateHash: str | None = None
    grpcWebProxyEndpoint: ServiceEndpointParams | None = None
    adminKey: str | None = None
    declineReward: bool | None = None

    @classmethod
    def parse_json_params(cls, params: dict) -> CreateNodeParams:
        """Parse JSON-RPC params into a CreateNodeParams instance."""
        gossipEndpoints = params.get("gossipEndpoints")
        if gossipEndpoints is not None and not isinstance(gossipEndpoints, list):
            raise ValueError("gossipEndpoints must be a list")

        serviceEndpoints = params.get("serviceEndpoints")
        if serviceEndpoints is not None and not isinstance(serviceEndpoints, list):
            raise ValueError("serviceEndpoints must be a list")

        grpcWebProxyEndpoint = params.get("grpcWebProxyEndpoint")

        return cls(
            accountId=params.get("accountId"),
            description=params.get("description"),
            gossipEndpoints=(
                [ServiceEndpointParams._from_dict(endpoints) for endpoints in gossipEndpoints]
                if gossipEndpoints is not None
                else None
            ),
            serviceEndpoints=(
                [ServiceEndpointParams._from_dict(endpoints) for endpoints in serviceEndpoints]
                if serviceEndpoints is not None
                else None
            ),
            gossipCaCertificate=params.get("gossipCaCertificate"),
            grpcCertificateHash=params.get("grpcCertificateHash"),
            grpcWebProxyEndpoint=(
                ServiceEndpointParams._from_dict(grpcWebProxyEndpoint) if grpcWebProxyEndpoint is not None else None
            ),
            adminKey=params.get("adminKey"),
            declineReward=to_bool(params.get("declineReward")),
            sessionId=parse_session_id(params),
            commonTransactionParams=parse_common_transaction_params(params),
        )


@dataclass
class ServiceEndpointParams:
    """Represent ServiceEndpoint parameter in JSON-RPC request."""

    ipAddressV4: str | None = None
    domainName: str | None = None
    port: int | None = None

    @classmethod
    def _from_dict(cls, params: dict) -> ServiceEndpointParams:
        """Parse dict into a ServiceEndpointParams instance."""
        return cls(
            ipAddressV4=params.get("ipAddressV4"), domainName=params.get("domainName"), port=to_int(params.get("port"))
        )

    def to_sdk_endpoint(self) -> Endpoint:
        return Endpoint(
            address=bytes.fromhex(self.ipAddressV4) if self.ipAddressV4 is not None else None,
            port=self.port,
            domain_name=self.domainName,
        )
