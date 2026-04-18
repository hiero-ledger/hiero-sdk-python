from __future__ import annotations

from concurrent import futures
from importlib import metadata as importlib_metadata
from unittest.mock import Mock, patch

import grpc
import pytest

from hiero_sdk_python.user_agent_interceptor import (
    _USER_AGENT_HEADER,
    _apply_user_agent_interceptor,
    _ClientCallDetails,
    _get_sdk_version,
    _UserAgentInterceptor,
)


pytestmark = pytest.mark.unit


def _call_details(metadata=None):
    return _ClientCallDetails(
        method="/proto.Service/Method",
        timeout=30,
        metadata=metadata,
        credentials=None,
        wait_for_ready=None,
        compression=None,
    )


def test_get_sdk_version_returns_installed_version():
    assert _get_sdk_version()


@patch("hiero_sdk_python.user_agent_interceptor.importlib_metadata.version")
def test_get_sdk_version_falls_back_to_dev(mock_version):
    mock_version.side_effect = importlib_metadata.PackageNotFoundError

    assert _get_sdk_version() == "dev"


@patch("hiero_sdk_python.user_agent_interceptor._get_sdk_version", return_value="1.2.3")
def test_unary_unary_interceptor_adds_user_agent_header(mock_get_version):
    interceptor = _UserAgentInterceptor()
    continuation = Mock(return_value="response")

    response = interceptor.intercept_unary_unary(continuation, _call_details(), request="request")

    assert response == "response"
    modified_call_details = continuation.call_args.args[0]
    assert (_USER_AGENT_HEADER, "hiero-sdk-python/1.2.3") in modified_call_details.metadata


@patch("hiero_sdk_python.user_agent_interceptor._get_sdk_version", return_value="1.2.3")
def test_unary_stream_interceptor_adds_user_agent_header(mock_get_version):
    interceptor = _UserAgentInterceptor()
    continuation = Mock(return_value=iter(["response"]))

    response = interceptor.intercept_unary_stream(continuation, _call_details(), request="request")

    assert list(response) == ["response"]
    modified_call_details = continuation.call_args.args[0]
    assert (_USER_AGENT_HEADER, "hiero-sdk-python/1.2.3") in modified_call_details.metadata


@patch("hiero_sdk_python.user_agent_interceptor._get_sdk_version", return_value="1.2.3")
def test_interceptor_preserves_existing_metadata(mock_get_version):
    interceptor = _UserAgentInterceptor()
    continuation = Mock(return_value="response")
    original_metadata = [("authorization", "token")]

    interceptor.intercept_unary_unary(continuation, _call_details(original_metadata), request="request")

    modified_metadata = continuation.call_args.args[0].metadata
    assert modified_metadata == [
        ("authorization", "token"),
        (_USER_AGENT_HEADER, "hiero-sdk-python/1.2.3"),
    ]


@patch("grpc.intercept_channel")
def test_apply_user_agent_interceptor_wraps_channel(mock_intercept_channel):
    channel = Mock(spec=grpc.Channel)
    intercepted_channel = Mock(spec=grpc.Channel)
    mock_intercept_channel.return_value = intercepted_channel

    assert _apply_user_agent_interceptor(channel) is intercepted_channel
    mock_intercept_channel.assert_called_once()
    assert mock_intercept_channel.call_args.args[0] is channel
    assert isinstance(mock_intercept_channel.call_args.args[1], _UserAgentInterceptor)


def test_interceptor_sends_valid_grpc_metadata():
    received_metadata = []

    def handle_request(request, context):
        received_metadata.extend(context.invocation_metadata())
        return b"response"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    method_handler = grpc.unary_unary_rpc_method_handler(
        handle_request,
        request_deserializer=lambda request: request,
        response_serializer=lambda response: response,
    )
    server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler("test.Service", {"Method": method_handler}),))
    port = server.add_insecure_port("127.0.0.1:0")
    server.start()

    try:
        channel = _apply_user_agent_interceptor(grpc.insecure_channel(f"127.0.0.1:{port}"))
        method = channel.unary_unary(
            "/test.Service/Method",
            request_serializer=lambda request: request,
            response_deserializer=lambda response: response,
        )

        assert method(b"request", timeout=5) == b"response"
    finally:
        server.stop(0)

    user_agent_values = [value for key, value in received_metadata if key == _USER_AGENT_HEADER]
    assert len(user_agent_values) == 1
    assert user_agent_values[0].startswith("hiero-sdk-python/")
