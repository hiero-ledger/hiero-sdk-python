from __future__ import annotations

import pytest

from tck.handlers.node import _build_node_update_transaction
from tck.param.node import CreateNodeParams, ServiceEndpointParams, UpdateNodeParams
from tck.util.param_utils import decode_hex


@pytest.mark.parametrize(
    "params",
    [
        (bytes([127, 0, 0, 1]).hex(), "test.com", 8080),
        (None, "test.com", 8080),
        (bytes([127, 0, 0, 1]).hex(), None, 8080),
        (bytes([127, 0, 0, 1]).hex(), "test.com", None),
    ],
)
def test_parse_service_endpoint(params):
    """Test json-rpc request is parse to ServiceEndpointParams."""
    response = {"ipAddressV4": params[0], "domainName": params[1], "port": params[2]}
    result = ServiceEndpointParams._from_dict(response)

    assert result is not None
    assert result.ipAddressV4 == params[0]
    assert result.domainName == params[1]
    assert result.port == params[2]


@pytest.mark.parametrize(
    "params",
    [
        ServiceEndpointParams(bytes([127, 0, 0, 1]).hex(), "test.com", 8080),
        ServiceEndpointParams(None, "test.com", 8080),
        ServiceEndpointParams(bytes([127, 0, 0, 1]).hex(), None, 8080),
        ServiceEndpointParams(bytes([127, 0, 0, 1]).hex(), "test.com", None),
    ],
)
def test_service_endpoint_to_sdk_endpoint(params):
    """Test json-rpc request is parse to ServiceEndpointParams."""
    result = ServiceEndpointParams.to_sdk_endpoint(params)

    assert result is not None
    assert result._domain_name == params.domainName
    assert result._port == params.port

    if result._address is not None:
        assert result._address == decode_hex(params.ipAddressV4)


def test_parse_create_node_params_with_service_endpoint_params():
    """Test json-rpc request is parse to CreateNodeParams with ServiceEndpoint in it."""
    params = {
        "accountId": "0.0.1002",
        "gossipEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}],
        "serviceEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}],
        "gossipCaCertificate": "19eae025b630028d18...",
        "adminKey": "302e020100300506032b65700422...",
        "commonTransactionParams": {"signers": ["302e020100300506032b6570042..."]},
        "sessionId": "NodeCreateTransaction",
    }

    result = CreateNodeParams.parse_json_params(params)
    assert result is not None
    assert result.accountId == params.get("accountId")
    assert result.gossipCaCertificate == params.get("gossipCaCertificate")
    assert len(result.serviceEndpoints) == 1
    assert result.serviceEndpoints[0] == ServiceEndpointParams._from_dict(params.get("serviceEndpoints")[0])
    assert len(result.gossipEndpoints) == 1
    assert result.gossipEndpoints[0] == ServiceEndpointParams._from_dict(params.get("gossipEndpoints")[0])
    assert result.adminKey == params.get("adminKey")
    assert result.sessionId == params.get("sessionId")


def test_parse_create_node_params_with_mutiple_service_endpoint_params():
    """Test json-rpc request is parse to CreateNodeParams with multiple ServiceEndpoint in it."""
    params = {
        "accountId": "0.0.1002",
        "gossipEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}, {"ipAddressV4": "7f000001", "port": 50211}],
        "serviceEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}],
        "gossipCaCertificate": "19eae025b630028d18...",
        "adminKey": "302e020100300506032b6570042204203b2f...",
        "commonTransactionParams": {"signers": ["302e020100300506032b6570042204203b2f20fe..."]},
        "sessionId": "NodeCreateTransaction",
    }

    result = CreateNodeParams.parse_json_params(params)
    assert result is not None
    assert result.accountId == params.get("accountId")
    assert result.gossipCaCertificate == params.get("gossipCaCertificate")

    assert len(result.serviceEndpoints) == len(params.get("serviceEndpoints"))
    for index, endpoint in enumerate(params.get("serviceEndpoints")):
        assert result.serviceEndpoints[index] == ServiceEndpointParams._from_dict(endpoint)

    assert len(result.gossipEndpoints) == len(params.get("gossipEndpoints"))
    for index, endpoint in enumerate(params.get("gossipEndpoints")):
        assert result.gossipEndpoints[index] == ServiceEndpointParams._from_dict(endpoint)

    assert result.adminKey == params.get("adminKey")
    assert result.sessionId == params.get("sessionId")


def test_parse_update_node_params_with_service_endpoint_params():
    """Test json-rpc request is parse to UpdateNodeParams with ServiceEndpoint in it."""
    params = {
        "nodeId": "3",
        "accountId": "0.0.1002",
        "description": "test description",
        "gossipEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}],
        "serviceEndpoints": [{"ipAddressV4": "7f000001", "port": 50211}],
        "gossipCaCertificate": "19eae025b630028d18...",
        "grpcCertificateHash": "a1b2c3d4e5f6",
        "grpcWebProxyEndpoint": {"domainName": "proxy.example.com", "port": 443},
        "adminKey": "302e020100300506032b65700422...",
        "declineReward": True,
        "commonTransactionParams": {"signers": ["302e020100300506032b6570042..."]},
        "sessionId": "NodeUpdateTransaction",
    }

    result = UpdateNodeParams.parse_json_params(params)
    assert result is not None
    assert result.nodeId == params.get("nodeId")
    assert result.accountId == params.get("accountId")
    assert result.description == params.get("description")
    assert result.gossipEndpoints == [ServiceEndpointParams._from_dict(params.get("gossipEndpoints")[0])]
    assert result.serviceEndpoints == [ServiceEndpointParams._from_dict(params.get("serviceEndpoints")[0])]
    assert result.gossipCaCertificate == params.get("gossipCaCertificate")
    assert result.grpcCertificateHash == params.get("grpcCertificateHash")
    assert result.grpcWebProxyEndpoint == ServiceEndpointParams._from_dict(params.get("grpcWebProxyEndpoint"))
    assert result.adminKey == params.get("adminKey")
    assert result.declineReward is True
    assert result.commonTransactionParams is not None
    assert result.sessionId == params.get("sessionId")


@pytest.mark.parametrize("node_id", ["3", "-1", "18446744073709551615"])
def test_parse_update_node_params_with_only_node_id(node_id):
    """Test nodeId is kept as the given string and absent fields are None."""
    result = UpdateNodeParams.parse_json_params({"nodeId": node_id, "sessionId": "NodeUpdateTransaction"})

    assert result.nodeId == node_id
    assert result.accountId is None
    assert result.description is None
    assert result.gossipEndpoints is None
    assert result.serviceEndpoints is None
    assert result.gossipCaCertificate is None
    assert result.grpcCertificateHash is None
    assert result.grpcWebProxyEndpoint is None
    assert result.adminKey is None
    assert result.declineReward is None
    assert result.commonTransactionParams is None


def test_parse_update_node_params_preserves_empty_values():
    """Test empty values are kept so they reach the SDK instead of being treated as absent."""
    params = {
        "nodeId": "3",
        "description": "",
        "gossipEndpoints": [],
        "serviceEndpoints": [],
        "grpcWebProxyEndpoint": {},
        "sessionId": "NodeUpdateTransaction",
    }

    result = UpdateNodeParams.parse_json_params(params)
    assert result.description == ""
    assert result.gossipEndpoints == []
    assert result.serviceEndpoints == []
    assert result.grpcWebProxyEndpoint == ServiceEndpointParams(ipAddressV4=None, domainName=None, port=None)


@pytest.mark.parametrize(("decline_reward", "expected"), [(False, False), ("false", False), (True, True)])
def test_parse_update_node_params_decline_reward(decline_reward, expected):
    """Test declineReward is parsed to a bool."""
    result = UpdateNodeParams.parse_json_params(
        {"nodeId": "3", "declineReward": decline_reward, "sessionId": "NodeUpdateTransaction"}
    )

    assert result.declineReward is expected


@pytest.mark.parametrize("field_name", ["gossipEndpoints", "serviceEndpoints"])
def test_parse_update_node_params_with_non_list_endpoints(field_name):
    """Test endpoint lists must be JSON arrays."""
    with pytest.raises(ValueError, match=f"{field_name} must be a list"):
        UpdateNodeParams.parse_json_params(
            {"nodeId": "3", field_name: {"port": 50211}, "sessionId": "NodeUpdateTransaction"}
        )


@pytest.mark.parametrize("params_cls", [CreateNodeParams, UpdateNodeParams])
@pytest.mark.parametrize(
    "endpoint_params",
    [
        {"gossipEndpoints": ["7f000001"]},
        {"serviceEndpoints": [None]},
        {"grpcWebProxyEndpoint": "proxy.example.com"},
        {"grpcWebProxyEndpoint": []},
    ],
)
def test_parse_node_params_with_non_object_endpoint(params_cls, endpoint_params):
    """Test every endpoint must be a JSON object."""
    with pytest.raises(ValueError, match="endpoint must be a JSON object"):
        params_cls.parse_json_params({"nodeId": "3", **endpoint_params, "sessionId": "NodeTransaction"})


def test_build_node_update_transaction_sets_only_supplied_fields():
    """Test the update builder leaves every field that was not supplied absent from the body."""
    params = UpdateNodeParams.parse_json_params(
        {"nodeId": "3", "description": "test description", "sessionId": "NodeUpdateTransaction"}
    )

    body = _build_node_update_transaction(params)._build_proto_body()
    assert body.node_id == 3
    assert body.description.value == "test description"
    assert not body.HasField("account_id")
    assert not body.HasField("gossip_ca_certificate")
    assert not body.HasField("grpc_certificate_hash")
    assert not body.HasField("admin_key")
    assert not body.HasField("decline_reward")
    assert not body.HasField("grpc_proxy_endpoint")
    assert not body.HasField("associated_registered_node_list")
    assert len(body.gossip_endpoint) == 0
    assert len(body.service_endpoint) == 0


def test_build_node_update_transaction_with_empty_grpc_web_proxy_endpoint():
    """Test an empty grpcWebProxyEndpoint is sent, which deletes the proxy on the network."""
    params = UpdateNodeParams.parse_json_params(
        {"nodeId": "3", "grpcWebProxyEndpoint": {}, "sessionId": "NodeUpdateTransaction"}
    )

    body = _build_node_update_transaction(params)._build_proto_body()
    assert body.HasField("grpc_proxy_endpoint")
