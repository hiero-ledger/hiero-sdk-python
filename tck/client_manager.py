from typing import Optional, Dict
from hiero_sdk_python import Client
import threading

_clients: Dict[str, Client] = {}
_lock = threading.Lock()

def store_client(session_id: str, client: Client) -> None:
    """Store a client instance associated with a session ID."""
    with _lock:
        old_client = _clients.get(session_id)
        _clients[session_id] = client
    if old_client is not None:
        old_client.close()

def get_client(session_id: str) -> Optional[Client]:
    """Retrieve a client instance by session ID."""
    with _lock:
        return _clients.get(session_id)

def remove_client(session_id: str) -> None:
    """Remove and close the client instance associated with a session ID."""
    with _lock:
        client = _clients.pop(session_id, None)
    if client is not None:
        client.close()
