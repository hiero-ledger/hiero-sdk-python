import json
from typing import Any, Dict, Optional, Union
from tck.errors import JsonRpcError


def _normalize_request_input(request_in: Any) -> Union[Dict[str, Any], JsonRpcError]:
    """Normalize request input to a dictionary
    Args:
        request_in: Either a JSON string or a pre-parsed dict
        
    Returns:
        Parsed dictionary or JsonRpcError if parsing fails
    """
    if isinstance(request_in, str):
        try:
            return json.loads(request_in)
        except json.JSONDecodeError:
            return JsonRpcError.parse_error()

    if isinstance(request_in, dict):
        return request_in

    return JsonRpcError.invalid_request_error()


def _validate_json_rpc_structure(request: Dict[str, Any]) -> Optional[JsonRpcError]:
    """Validate the basic JSON-RPC 2.0 structure.
    Args:
        request: The parsed request dictionary

    Returns:
        JsonRpcError if validation fails, None if valid
    """
    if not isinstance(request, dict):
        return JsonRpcError.invalid_request_error()

    if request.get('jsonrpc') != '2.0':
        return JsonRpcError.invalid_request_error()

    if 'id' not in request:
        return JsonRpcError.invalid_request_error()

    method = request.get('method')
    if not isinstance(method, str):
        return JsonRpcError.invalid_request_error()

    params = request.get('params', {})
    if not (isinstance(params, (dict, list)) or params is None):
        return JsonRpcError.invalid_request_error()

    return None


def _extract_session_id(params: Any) -> Optional[str]:
    """Extract session ID from params if present.
    Args:
        params: Request parameters (dict, list, or None)
        
    Returns:
        Session ID if present, None otherwise
    """
    if isinstance(params, dict):
        return params.get('sessionId')
    return None


def parse_json_rpc_request(request_in: Any) -> Union[Dict[str, Any], JsonRpcError]:
    """Parse and validate a JSON-RPC 2.0 request.

    Accepts either a JSON string or a pre-parsed dict (e.g., Flask request body).
    """
    # Normalize input to a dict
    request = _normalize_request_input(request_in)
    if isinstance(request, JsonRpcError):
        return request

    # Validate JSON-RPC structure
    validation_error = _validate_json_rpc_structure(request)
    if validation_error:
        return validation_error

    # Extract session ID from params
    params = request.get('params', {})
    session_id = _extract_session_id(params)

    return {
        'jsonrpc': '2.0',
        'method': request['method'],
        'params': params,
        'id': request['id'],
        'sessionId': session_id
    }

def build_json_rpc_success_response(result: Any, request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 success response."""
    response = {
        'jsonrpc': '2.0',
        'id': request_id,
        'result': result,
    }
    return response

def build_json_rpc_error_response(error: JsonRpcError,
                                  request_id: Optional[Union[str, int]]) -> Dict[str, Any]:
    """Build a JSON-RPC 2.0 error response."""
    error_obj = error.to_dict()
 
    response = {
        'jsonrpc': '2.0',
        'id': request_id,
        'error': error_obj,
    }
    return response
