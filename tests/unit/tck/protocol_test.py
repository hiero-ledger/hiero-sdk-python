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
    
    if not isinstance(parsed, dict):
        raise AssertionError("Expected parsed result to be a dict")
    if parsed['jsonrpc'] != '2.0':
        raise AssertionError("Expected jsonrpc version 2.0")
    if parsed['method'] != 'setup':
        raise AssertionError("Expected method to be 'setup'")
    if parsed['id'] != 1:
        raise AssertionError("Expected id to be 1")
    if parsed['sessionId'] is not None:
        raise AssertionError("Expected sessionId to be None when not in params")


def test_response_formatting_success():
    """Test formatting of a successful JSON-RPC response."""
    resp = build_json_rpc_success_response({"ok": True}, 1)
    if resp["jsonrpc"] != "2.0":
        raise AssertionError("Expected jsonrpc version 2.0 in success response")
    if "result" not in resp:
        raise AssertionError("Expected 'result' key in success response")
    if resp["result"] != {"ok": True}:
        raise AssertionError("Expected result to match input")
    if resp["id"] != 1:
        raise AssertionError("Expected id to match request_id")


def test_response_formatting_error():
    """Test formatting of an error JSON-RPC response."""
    error = JsonRpcError.invalid_request_error()
    resp = build_json_rpc_error_response(error, 1)
    if resp["jsonrpc"] != "2.0":
        raise AssertionError("Expected jsonrpc version 2.0 in error response")
    if "error" not in resp:
        raise AssertionError("Expected 'error' key in error response")
    if resp["error"]["code"] != INVALID_REQUEST:
        raise AssertionError("Expected INVALID_REQUEST code")
    if resp["error"]["message"] != "Invalid Request":
        raise AssertionError("Expected error message 'Invalid Request'")

def test_invalid_json_returns_parse_error(invalid_json_request):
    """Test that invalid JSON input returns a parse error."""
    req = invalid_json_request
    parsed = parse_json_rpc_request(req)

    if not isinstance(parsed, JsonRpcError):
        raise AssertionError("Expected JsonRpcError for invalid JSON")
    if parsed.code != PARSE_ERROR:
        raise AssertionError("Expected PARSE_ERROR code")

def test_missing_required_fields_returns_invalid_request(request_missing_fields):
    """Test that missing required fields returns an invalid request error."""
    req = request_missing_fields
    if "method" in req:
        raise AssertionError("Fixture should be missing 'method' field")

    parsed = parse_json_rpc_request(req)
    if not isinstance(parsed, JsonRpcError):
        raise AssertionError("Expected JsonRpcError for missing method")
    if parsed.code != INVALID_REQUEST:
        raise AssertionError("Expected INVALID_REQUEST code")

def test_session_id_extraction_no_session():
    """Test extraction of session ID when no session is present."""
    params = {}
    sid = _extract_session_id(params)
    if sid is not None:
        raise AssertionError("sessionId should be None when not in params")

def test_session_id_extraction_with_session(request_with_session_id):
    """Test extraction of session ID when sessionId is present in params."""
    sid = _extract_session_id(request_with_session_id["params"])
    if sid != "session-abc-123":
        raise AssertionError("Expected sessionId to be extracted from params")

def test_parsing_request_with_string_id(request_with_string_id):
    """Test parsing of a valid JSON-RPC request with string ID."""
    raw = json.dumps(request_with_string_id)
    parsed = parse_json_rpc_request(raw)

    if not isinstance(parsed, dict):
        raise AssertionError("Expected parsed result to be a dict")
    if parsed['jsonrpc'] != '2.0':
        raise AssertionError("Expected jsonrpc version 2.0")
    if parsed['method'] != 'setup':
        raise AssertionError("Expected method to be 'setup'")
    if parsed['id'] != "string-id-123":
        raise AssertionError("Expected string id to be preserved")

def test_invalid_jsonrpc_version_returns_error(request_invalid_jsonrpc_version):
    """Test that invalid jsonrpc version returns an invalid request error."""
    raw = json.dumps(request_invalid_jsonrpc_version)
    parsed = parse_json_rpc_request(raw)

    if not isinstance(parsed, JsonRpcError):
        raise AssertionError("Expected JsonRpcError for invalid version")
    if parsed.code != INVALID_REQUEST:
        raise AssertionError("Expected INVALID_REQUEST code")
