from __future__ import annotations

import threading

from hiero_sdk_python import Client


_CLIENTS: dict[str, Client] = {}
_LOCK = threading.Lock()


def store_client(session_id: str, client: Client) -> None:
    """Store a client instance associated with a session ID."""
    with _LOCK:
        old_client = _CLIENTS.get(session_id)
        _CLIENTS[session_id] = client
    if old_client is not None:
        old_client.close()


def get_client(session_id: str) -> Client | None:
    """Retrieve a client instance by session ID."""
    with _LOCK:
        return _CLIENTS.get(session_id)


def remove_client(session_id: str) -> None:
    """Remove and close the client instance associated with a session ID."""
    with _LOCK:
        client = _CLIENTS.pop(session_id, None)
    if client is not None:
        client.close()
