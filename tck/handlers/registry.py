"""Build a flexible registry-based method routing system that can dispatch 
requests to handlers and transform exceptions into JSON-RPC errors."""
from typing import Any, Dict, Optional, Union, Callable
from tck.errors import (
    JsonRpcError
)
from tck.protocol import build_json_rpc_error_response
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
        raise JsonRpcError.method_not_found_error(message=f'Method not found: {method_name}')
    try:
        if session_id is not None:
            return handler(params, session_id)
        return handler(params)
    except JsonRpcError:
        raise
    except (PrecheckError, ReceiptStatusError, MaxAttemptsError) as e:
        raise JsonRpcError.hiero_error(data=str(e)) from e
    except Exception as e:
        raise JsonRpcError.internal_error(data=str(e)) from e

def safe_dispatch(method_name: str,
                  params: Any,
                  session_id: Optional[str],
                  request_id: Optional[Union[str, int]]) -> Union[Any, Dict[str, Any]]:
    """Safely dispatch the request and handle exceptions."""
    try:
        return dispatch(method_name, params, session_id)
    except JsonRpcError as e:
        return build_json_rpc_error_response(e, request_id)
    except Exception as e: # Defensive fallback for any uncaught exceptions
        error = JsonRpcError.internal_error(data=str(e))
        return build_json_rpc_error_response(error, request_id)

def validate_request_params(params: Any, required_fields: Dict[str, type]) -> None:
    """Validate that required fields are present in params with correct types."""
    if not isinstance(params, dict):
        raise JsonRpcError.invalid_params_error(message='Invalid params: expected object')

    for field, field_type in required_fields.items():
        if field not in params or not isinstance(params[field], field_type):
            raise JsonRpcError.invalid_params_error(message=f'Invalid params: missing or incorrect type for {field}')

