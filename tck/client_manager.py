from typing import Optional, Dict
from hiero_sdk_python import Client

_clients: Dict[str, Client] = {}

def store_client(session_id: str, client: 'Client') -> None:
    """Store a client instance associated with a session ID."""
    _clients[session_id] = client

def get_client(session_id: str) -> Optional['Client']:
    """Retrieve a client instance by session ID."""
    return _clients.get(session_id)

def remove_client(session_id: str) -> None:
    """Remove and close the client instance associated with a session ID."""
    client = _clients.pop(session_id, None)
    if client is not None:
        client.close()
