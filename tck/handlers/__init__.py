"""TCK handlers - auto-import all handler modules."""

# Import registry functions first to make them available
from .registry import (
    get_handler,
    get_all_handlers,
    safe_dispatch,
)

# Import all handler modules to trigger @rpc_method decorators
from . import sdk  # setup, reset
from . import key
from . import account

__all__ = [
    "get_handler",
    "get_all_handlers",
    "safe_dispatch",
]
