"""TCK handlers - auto-import all handler modules."""

# Import registry functions first to make them available
# Import all handler modules to trigger @rpc_method decorators
from . import (
    account,
    key,
    sdk,  # setup, reset
)
from .registry import (
    get_all_handlers,
    get_handler,
    safe_dispatch,
)


__all__ = [
    "get_handler",
    "get_all_handlers",
    "safe_dispatch",
    "account",
    "key",
    "sdk",
]
