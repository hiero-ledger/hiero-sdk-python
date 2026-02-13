"""TCK handlers - auto-import all handler modules."""

# Import registry functions first to make them available
from .registry import get_handler, get_all_handlers, safe_dispatch, validate_request_params

# Import all handler modules to trigger @register_handler decorators
from . import sdk      # setup, reset

__all__ = ["get_handler", "get_all_handlers", "safe_dispatch", "validate_request_params"]