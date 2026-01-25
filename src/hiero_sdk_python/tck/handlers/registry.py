"""Build a flexible registry-based method routing system that can dispatch 
requests to handlers and transform exceptions into JSON-RPC errors."""
from typing import Any, Dict, Optional, Union, Callable
from hiero_sdk_python.tck.errors import INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND, HIERO_ERROR, INVALID_REQUEST
from hiero_sdk_python.tck.protocol import build_json_rpc_error_response, JsonRpcError
from hiero_sdk_python.exceptions import PrecheckError, ReceiptStatusError, MaxAttemptsError


# A global _HANDLERS dict to store method name -> handler function mappings
_HANDLERS: Dict[str, Callable] = {}

def register_handler(method_name: str):
    """Register a handler function for a given method name."""
    def decorator(func: Callable) -> Callable:
        """Decorator to register a handler function for a given method name."""
        _HANDLERS[method_name] = func
        return func
    return decorator

def get_handler(method_name: str) -> Optional[Callable]:
    """Retrieve a handler by method name."""
    return _HANDLERS.get(method_name)

def get_all_handlers() -> Dict[str, Callable]:
    """Get all registered handlers."""
    return _HANDLERS.copy()


def dispatch(method_name: str, params: Any, session_id: Optional[str]) -> Any:
    """Dispatch the request to the appropriate handler based on method_name."""
    handler = get_handler(method_name)
    
    if handler is None:
        raise JsonRpcError(METHOD_NOT_FOUND, f'Method not found: {method_name}')
    try:
        if session_id is not None:
            return handler(params, session_id)
        return handler(params)
    except JsonRpcError:
        raise
    except Exception as e:
        error = JsonRpcError(INTERNAL_ERROR, 'Internal error', str(e))
        return build_json_rpc_error_response(error, None)

def safe_dispatch(method_name: str,
                  params: Any,
                  session_id: Optional[str]) -> Union[Any, Dict[str, Any]]:
    """Safely dispatch the request and handle exceptions."""
    try:
        return dispatch(method_name, params, session_id)
    except JsonRpcError as e:
        return build_json_rpc_error_response(e, None)
    except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
        error = JsonRpcError(HIERO_ERROR, 'Hiero error', str(e))
        return build_json_rpc_error_response(error, None)
    except Exception as e:
        error = JsonRpcError(INTERNAL_ERROR, 'Internal error', str(e))
        return build_json_rpc_error_response(error, None)

def validate_request_params(params: Any, required_fields: Dict[str, type]) -> None:
    """Validate that required fields are present in params with correct types."""
    if not isinstance(params, dict):
        raise JsonRpcError(INVALID_REQUEST, 'Invalid Request')

    for field, field_type in required_fields.items():
        if field not in params or not isinstance(params[field], field_type):
            raise JsonRpcError(INVALID_PARAMS, f'Invalid params: missing or incorrect type for {field}')

