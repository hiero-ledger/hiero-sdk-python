"""Build a flexible registry-based method routing system that can dispatch
requests to handlers and transform exceptions into JSON-RPC errors.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from tck.errors import JsonRpcError, handle_sdk_errors
from tck.protocol import build_json_rpc_error_response


# A global _HANDLERS dict to store method name -> handler function mappings
_HANDLERS: dict[str, Callable] = {}


def rpc_method(method_name: str):
    """Register a handler function for a given method name."""

    def decorator(func: Callable) -> Callable:
        """Decorator to register a handler function for a given method name."""
        _HANDLERS[method_name] = handle_sdk_errors(func)
        return func

    return decorator


def get_handler(method_name: str) -> Callable | None:
    """Retrieve a handler by method name."""
    return _HANDLERS.get(method_name)


def get_all_handlers() -> dict[str, Callable]:
    """Get all registered handlers."""
    return _HANDLERS.copy()


def dispatch(method_name: str, params: Any) -> Any:
    """Dispatch the request to the appropriate handler based on method_name."""
    handler = get_handler(method_name)

    if handler is None:
        raise JsonRpcError.method_not_found_error(message=f"Method not found: {method_name}")

    try:
        signature = inspect.signature(handler)
        parameters = list(signature.parameters.values())
        param_type = parameters[0].annotation

        try:
            params = param_type.parse_json_params(params)
        except (TypeError, ValueError) as e:
            raise JsonRpcError.invalid_params_error(data=str(e)) from e

        result = handler(params)

        return parse_result(result)

    except JsonRpcError:
        raise
    except Exception as e:
        raise JsonRpcError.internal_error(data=str(e)) from e


def safe_dispatch(method_name: str, params: Any, request_id: str | int | None) -> Any | dict[str, Any]:
    """Safely dispatch the request and handle exceptions."""
    try:
        return dispatch(method_name, params)
    except JsonRpcError as e:
        return build_json_rpc_error_response(e, request_id)
    except Exception as e:
        error = JsonRpcError.internal_error(data=str(e))
        return build_json_rpc_error_response(error, request_id)


def parse_result(result: Any) -> dict:
    """Parse the result from the methods to dict containing non none key:values"""
    return {k: v for k, v in asdict(result).items() if v is not None}
