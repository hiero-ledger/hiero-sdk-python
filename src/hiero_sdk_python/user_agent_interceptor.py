from __future__ import annotations

from collections import namedtuple
from importlib import metadata as importlib_metadata

import grpc


_SDK_PACKAGE_NAME = "hiero-sdk-python"
_USER_AGENT_HEADER = "x-user-agent"


def _get_sdk_version() -> str:
    """Return the installed SDK version, or dev for local checkouts."""
    try:
        return importlib_metadata.version(_SDK_PACKAGE_NAME)
    except importlib_metadata.PackageNotFoundError:
        return "dev"


class _ClientCallDetails(
    namedtuple(
        "_ClientCallDetails",
        ("method", "timeout", "metadata", "credentials", "wait_for_ready", "compression"),
    ),
    grpc.ClientCallDetails,
):
    """Concrete call details used to attach metadata in client interceptors."""


class _UserAgentInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor):
    """gRPC client interceptor that identifies this SDK to Hiero nodes."""

    def __init__(self) -> None:
        self._user_agent = f"{_SDK_PACKAGE_NAME}/{_get_sdk_version()}"

    def intercept_unary_unary(self, continuation, client_call_details, request):
        return continuation(self._with_user_agent(client_call_details), request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        return continuation(self._with_user_agent(client_call_details), request)

    def _with_user_agent(self, client_call_details):
        metadata = list(client_call_details.metadata or ())
        metadata.append((_USER_AGENT_HEADER, self._user_agent))

        return _ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
            client_call_details.compression,
        )


_USER_AGENT_INTERCEPTOR = _UserAgentInterceptor()


def _apply_user_agent_interceptor(channel: grpc.Channel) -> grpc.Channel:
    """Wrap a channel so every outgoing call includes the SDK user-agent header."""
    return grpc.intercept_channel(channel, _USER_AGENT_INTERCEPTOR)
