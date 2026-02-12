"""Unit tests for the JSON-RPC protocol handling in the TCK."""
import json
import pytest

from tck.protocol import (
    parse_json_rpc_request,
    _extract_session_id,
    build_json_rpc_success_response,
    build_json_rpc_error_response,
)
from tck.errors import INVALID_REQUEST,PARSE_ERROR, JsonRpcError

pytestmark = pytest.mark.unit

def test_parsing_valid_request(valid_jsonrpc_request):
    """Test parsing of a valid JSON-RPC request."""
    raw = json.dumps(valid_jsonrpc_request)
    parsed = parse_json_rpc_request(raw)
    
    assert isinstance(parsed, dict), "Expected parsed result to be a dict"
    assert parsed['jsonrpc'] == '2.0', "Expected jsonrpc version 2.0"
    assert parsed['method'] == 'setup', "Expected method to be 'setup'"
    assert parsed['id'] == 1, "Expected id to be 1"
    assert parsed['sessionId'] is None, "Expected sessionId to be None when not in params"


def test_response_formatting_success():
    """Test formatting of a successful JSON-RPC response."""
    resp = build_json_rpc_success_response({"ok": True}, 1)
    assert resp["jsonrpc"] == "2.0", "Expected jsonrpc version 2.0 in success response"
    assert "result" in resp, "Expected 'result' key in success response"
    assert resp["result"] == {"ok": True}, "Expected result to match input"
    assert resp["id"] == 1, "Expected id to match request_id"


def test_response_formatting_error():
    """Test formatting of an error JSON-RPC response."""
    error = JsonRpcError(INVALID_REQUEST, "Invalid Request")
    resp = build_json_rpc_error_response(error, 1)
    assert resp["jsonrpc"] == "2.0", "Expected jsonrpc version 2.0 in error response"
    assert "error" in resp, "Expected 'error' key in error response"
    assert resp["error"]["code"] == INVALID_REQUEST, f"Expected INVALID_REQUEST code, got {resp['error']['code']}"
    assert resp["error"]["message"] == "Invalid Request", "Expected error message 'Invalid Request'"

def test_invalid_json_returns_parse_error(invalid_json_request):
    """Test that invalid JSON input returns a parse error."""
    req = invalid_json_request
    parsed = parse_json_rpc_request(req)

    assert isinstance(parsed, JsonRpcError), "Expected JsonRpcError for invalid JSON"
    assert parsed.code == PARSE_ERROR, f"Expected PARSE_ERROR code, got {parsed.code}"

def test_missing_required_fields_returns_invalid_request(request_missing_fields):
    """Test that missing required fields returns an invalid request error."""
    req = request_missing_fields
    assert "method" not in req, "Fixture should be missing 'method' field"

    parsed = parse_json_rpc_request(req)
    assert isinstance(parsed, JsonRpcError), "Expected JsonRpcError for missing method"
    assert parsed.code == INVALID_REQUEST, f"Expected INVALID_REQUEST code, got {parsed.code}"

def test_session_id_extraction_no_session():
    """Test extraction of session ID when no session is present."""
    params = {}
    sid = _extract_session_id(params)
    assert sid is None, "sessionId should be None when not in params"

def test_session_id_extraction_with_session(request_with_session_id):
    """Test extraction of session ID when sessionId is present in params."""
    sid = _extract_session_id(request_with_session_id["params"])
    assert sid == "session-abc-123", "Expected sessionId to be extracted from params"

def test_parsing_request_with_string_id(request_with_string_id):
    """Test parsing of a valid JSON-RPC request with string ID."""
    raw = json.dumps(request_with_string_id)
    parsed = parse_json_rpc_request(raw)

    assert isinstance(parsed, dict), "Expected parsed result to be a dict"
    assert parsed['jsonrpc'] == '2.0', "Expected jsonrpc version 2.0"
    assert parsed['method'] == 'setup', "Expected method to be 'setup'"
    assert parsed['id'] == "string-id-123", "Expected string id to be preserved"

def test_invalid_jsonrpc_version_returns_error(request_invalid_jsonrpc_version):
    """Test that invalid jsonrpc version returns an invalid request error."""
    raw = json.dumps(request_invalid_jsonrpc_version)
    parsed = parse_json_rpc_request(raw)

    assert isinstance(parsed, JsonRpcError), "Expected JsonRpcError for invalid version"
    assert parsed.code == INVALID_REQUEST, f"Expected INVALID_REQUEST code, got {parsed.code}"
