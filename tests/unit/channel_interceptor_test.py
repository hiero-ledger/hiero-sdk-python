from __future__ import annotations

import grpc
import pytest

from hiero_sdk_python import channels
from hiero_sdk_python.channels import _UserAgentInterceptor


pytestmark = pytest.mark.unit


class _DummyCallDetails:
    def __init__(
        self,
        metadata=None,
        method: str = "/proto.Service/Method",
        timeout: float | None = None,
        credentials=None,
        wait_for_ready: bool | None = None,
        compression=None,
    ):
        self.method = method
        self.timeout = timeout
        self.metadata = metadata
        self.credentials = credentials
        self.wait_for_ready = wait_for_ready
        self.compression = compression


def test_user_agent_value_from_installed_version(monkeypatch):
    """Interceptor should build x-user-agent from package version when available."""

    monkeypatch.setattr(channels, "version", lambda _name: "0.0.0")

    interceptor = _UserAgentInterceptor()
    assert interceptor._user_agent == "hiero-sdk-python/0.0.0"


def test_user_agent_value_falls_back_to_dev(monkeypatch):
    """Interceptor should fall back to dev when package metadata is unavailable."""

    def _raise_not_found(_name):
        raise channels.PackageNotFoundError

    monkeypatch.setattr(channels, "version", _raise_not_found)

    interceptor = _UserAgentInterceptor()
    assert interceptor._user_agent == "hiero-sdk-python/dev"


def test_intercept_unary_unary_appends_user_agent_metadata(monkeypatch):
    """Unary calls should forward metadata including x-user-agent."""

    monkeypatch.setattr(channels, "version", lambda _name: "0.0.0")

    interceptor = _UserAgentInterceptor()
    request = object()
    captured = {}

    def continuation(client_call_details, req):
        captured["details"] = client_call_details
        captured["request"] = req
        return "ok"

    details = _DummyCallDetails(metadata=[("existing", "value")])
    result = interceptor.intercept_unary_unary(continuation, details, request)

    assert result == "ok"
    assert captured["request"] is request
    assert ("existing", "value") in captured["details"].metadata
    expected_header = (interceptor._HEADER_KEY, f"{interceptor._SDK_NAME}/0.0.0")
    assert expected_header in captured["details"].metadata


def test_intercept_unary_stream_adds_metadata_when_none(monkeypatch):
    """Unary-stream calls should work even when original metadata is None."""

    monkeypatch.setattr(channels, "version", lambda _name: "0.0.0")

    interceptor = _UserAgentInterceptor()
    request = object()
    captured = {}

    def continuation(client_call_details, req):
        captured["details"] = client_call_details
        captured["request"] = req
        return "stream"

    details = _DummyCallDetails(metadata=None)
    result = interceptor.intercept_unary_stream(continuation, details, request)

    assert result == "stream"
    assert captured["request"] is request
    expected_header = (interceptor._HEADER_KEY, f"{interceptor._SDK_NAME}/0.0.0")
    assert captured["details"].metadata == [expected_header]


def test_interceptor_implements_required_grpc_interfaces():
    """Guard against accidental loss of gRPC interceptor interface inheritance."""
    interceptor = _UserAgentInterceptor()
    assert isinstance(interceptor, grpc.UnaryUnaryClientInterceptor)
    assert isinstance(interceptor, grpc.UnaryStreamClientInterceptor)
