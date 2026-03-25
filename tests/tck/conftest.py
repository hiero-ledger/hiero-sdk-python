"""Fixtures for JSON-RPC request tests."""
import pytest

@pytest.fixture
def valid_jsonrpc_request():
    """Returns a valid JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "method": "setup",
        "params": {},
        "id": 1,
    }

@pytest.fixture
def invalid_json_request():
    """Returns a malformed JSON-RPC request."""
    return '{"id": malformed}'

@pytest.fixture
def request_missing_fields():
    """Returns a JSON-RPC request missing the 'method' field."""
    return {
        "jsonrpc": "2.0",
        "params": {},
        "id": 1
    }


@pytest.fixture
def request_with_string_id():
    """Returns a JSON-RPC request with a string id (valid per JSON-RPC 2.0).
    
    The id can be a string, number, or NULL; this tests string id support.
    """
    return {
        "jsonrpc": "2.0",
        "method": "setup",
        "params": {},
        "id": "string-id-123",
    }

@pytest.fixture
def request_invalid_jsonrpc_version():
    """Returns a JSON-RPC request with an invalid version (1.0 instead of 2.0).
    
    Tests boundary condition: server should reject non-2.0 versions.
    """
    return {
        "jsonrpc": "1.0",
        "method": "setup",
        "params": {},
        "id": 1,
    }

@pytest.fixture
def request_with_session_id():
    """Returns a JSON-RPC request with sessionId in params.
    
    Tests that sessionId parameter is properly extracted and passed through.
    """
    return {
        "jsonrpc": "2.0",
        "method": "setup",
        "params": {"sessionId": "session-abc-123"},
        "id": 1,
    }
