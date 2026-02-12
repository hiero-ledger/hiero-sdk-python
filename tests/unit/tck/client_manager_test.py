"""Unit tests for the client manager module."""
from unittest.mock import MagicMock
import pytest
from tck.client_manager import store_client, get_client, remove_client, _clients

pytestmark = pytest.mark.unit

@pytest.fixture(autouse=True)
def clear_clients():
    """Clear the clients registry before each test."""
    _clients.clear()
    yield
    _clients.clear()


class TestClientManager:
    """Test client storage, retrieval, and cleanup."""
    
    def test_store_and_retrieve_client(self):
        """Test that a client can be stored and retrieved by session ID."""
        mock_client = MagicMock()
        session_id = "session123"

        store_client(session_id, mock_client)
        retrieved_client = get_client(session_id)

        if retrieved_client is not mock_client:
            raise AssertionError("Expected stored client to be returned for session123")

    def test_retrieve_nonexistent_client_returns_none(self):
        """Test that retrieving a non-existent client returns None."""
        result = get_client("nonexistent_session")
        if result is not None:
            raise AssertionError("Expected None when retrieving a missing session ID")

    def test_store_multiple_clients(self):
        """Test storing and retrieving multiple clients with different session IDs."""
        client1 = MagicMock()
        client2 = MagicMock()
        client3 = MagicMock()
        
        store_client("session1", client1)
        store_client("session2", client2)
        store_client("session3", client3)
        
        if get_client("session1") is not client1:
            raise AssertionError("Expected client1 to be returned for session1")
        if get_client("session2") is not client2:
            raise AssertionError("Expected client2 to be returned for session2")
        if get_client("session3") is not client3:
            raise AssertionError("Expected client3 to be returned for session3")
    
    def test_overwrite_existing_client(self):
        """Test that storing a client with an existing session ID overwrites it."""
        old_client = MagicMock()
        new_client = MagicMock()
        session_id = "session_to_overwrite"

        store_client(session_id, old_client)
        store_client(session_id, new_client)

        retrieved = get_client(session_id)
        if retrieved is not new_client:
            raise AssertionError("Expected new_client after overwrite")
        if retrieved is old_client:
            raise AssertionError("Old client should no longer be stored")

        # Verify that close() was called on the old client
        old_client.close.assert_called_once()


    def test_remove_client_calls_close(self):
        """Test that remove_client calls close() on the client."""
        mock_client = MagicMock()
        session_id = "session_to_remove"

        store_client(session_id, mock_client)
        remove_client(session_id)

        # Verify close() was called
        mock_client.close.assert_called_once()

        # Verify client was removed from storage
        if get_client(session_id) is not None:
            raise AssertionError("Expected client to be removed from storage")

    def test_remove_nonexistent_client_does_not_raise(self):
        """Test that removing a non-existent client does not raise an error."""
        # Should not raise any exception
        remove_client("nonexistent_session")

    def test_remove_client_multiple_times(self):
        """Test that removing a client multiple times does not cause issues."""
        mock_client = MagicMock()
        session_id = "session_multi_remove"

        store_client(session_id, mock_client)
        remove_client(session_id)

        # Remove again - should not raise
        remove_client(session_id)

        # close() should only be called once (from first removal)
        mock_client.close.assert_called_once()

    def test_remove_one_client_does_not_affect_others(self):
        """Test that removing one client does not affect other stored clients."""
        client1 = MagicMock()
        client2 = MagicMock()
        client3 = MagicMock()

        store_client("session1", client1)
        store_client("session2", client2)
        store_client("session3", client3)

        remove_client("session2")

        # session2 should be removed
        if get_client("session2") is not None:
            raise AssertionError("Expected session2 client to be removed")
        client2.close.assert_called_once()

        # Others should remain
        if get_client("session1") is not client1:
            raise AssertionError("Expected session1 client to remain")
        if get_client("session3") is not client3:
            raise AssertionError("Expected session3 client to remain")
        client1.close.assert_not_called()
        client3.close.assert_not_called()
