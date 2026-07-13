"""Build a flexible registry-based method routing system that can dispatch
requests to handlers and transform exceptions into JSON-RPC errors.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from dataclasses import asdict, fields as dc_fields
from typing import Any, get_type_hints

from tck.errors import JsonRpcError, handle_sdk_errors
from tck.protocol import build_json_rpc_error_response


logger = logging.getLogger(__name__)


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
        logger.warning(
            f"MethodNotFoundError (method: {method_name}) error: The requested RPC method is not registered."
        )
        raise JsonRpcError.method_not_found_error(message=f"Method not found: {method_name}")

    try:
        target_func = getattr(handler, "__wrapped__", handler)

        hints = get_type_hints(target_func)
        signature = inspect.signature(handler)
        parameters = list(signature.parameters.values())

        param_name = parameters[0].name

        try:
            param_type = hints.get(param_name, parameters[0].annotation)
            params = param_type.parse_json_params(params)
        except (TypeError, ValueError) as e:
            logger.error(f"InvalidParamsError (method: {method_name}) error: {str(e)}")
            raise JsonRpcError.invalid_params_error(data=str(e)) from e

        result = handler(params)

        return parse_result(result)

    except JsonRpcError:
        raise
    except Exception as e:
        logger.error(f"InternalError (method: {method_name}) error: {str(e)}")
        raise JsonRpcError.internal_error(message="An unexpected system error occurred.") from e


def safe_dispatch(method_name: str, params: Any, request_id: str | int | None) -> Any | dict[str, Any]:
    """Safely dispatch the request and handle exceptions."""
    try:
        return dispatch(method_name, params)
    except JsonRpcError as e:
        return build_json_rpc_error_response(e, request_id)
    except Exception as e:
        logger.error(f"InternalError (method: {method_name}) error: {str(e)}")
        error = JsonRpcError.internal_error(message="An unexpected system error occurred.")
        return build_json_rpc_error_response(error, request_id)


def _strip_none(obj: Any, nullable_keys: set[str] | None = None) -> Any:
    """Recursively strip None values from nested dicts and lists."""
    if isinstance(obj, dict):
        return {
            k: _strip_none(v)
            for k, v in obj.items()
            if v is not None or (nullable_keys is not None and k in nullable_keys)
        }
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj


def parse_result(result: Any) -> dict:
    """Parse the result from the methods to dict containing non none key:values.

    Fields with metadata={"nullable": True} are preserved even when None.
    Recursively strips None from nested structures.
    """
    nullable_fields: set[str] = set()
    for f in dc_fields(result):
        if f.metadata.get("nullable"):
            nullable_fields.add(f.name)

    raw = asdict(result)
    return _strip_none(raw, nullable_keys=nullable_fields)
