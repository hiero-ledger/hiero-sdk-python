from __future__ import annotations

import pytest

from tck.param.node import CreateNodeParams, ServiceEndpointParams
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
