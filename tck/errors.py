"""Error code constants for the TCK server."""

from __future__ import annotations

import logging
from functools import wraps

from hiero_sdk_python.exceptions import MaxAttemptsError, PrecheckError, ReceiptStatusError
from hiero_sdk_python.response_code import ResponseCode


# These constants can be used throughout the codebase to represent specific error conditions.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
HIERO_ERROR = -32001

logger = logging.getLogger(__name__)


class JsonRpcError(Exception):
    """Class representing a JSON-RPC error."""

    def __init__(self, code: int, message: str, data=None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        """Convert the error to a dictionary representation."""
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error

    @classmethod
    def parse_error(cls, data=None, message: str = "Parse error") -> JsonRpcError:
        """Create a Parse Error JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Parse error')
        """
        return cls(PARSE_ERROR, message, data)

    @classmethod
    def invalid_request_error(cls, data=None, message: str = "Invalid Request") -> JsonRpcError:
        """Create an Invalid Request JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Invalid Request')
        """
        return cls(INVALID_REQUEST, message, data)

    @classmethod
    def method_not_found_error(cls, data=None, message: str = "Method not found") -> JsonRpcError:
        """Create a Method Not Found JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Method not found')
        """
        return cls(METHOD_NOT_FOUND, message, data)

    @classmethod
    def invalid_params_error(cls, data=None, message: str = "Invalid params") -> JsonRpcError:
        """Create an Invalid Params JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Invalid params')
        """
        return cls(INVALID_PARAMS, message, data)

    @classmethod
    def internal_error(cls, data=None, message: str = "Internal error") -> JsonRpcError:
        """Create an Internal Error JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Internal error')
        """
        return cls(INTERNAL_ERROR, message, data)

    @classmethod
    def hiero_error(cls, data=None, message: str = "Hiero error") -> JsonRpcError:
        """Create a Hiero-specific JSON-RPC error.

        Args:
            data: Optional error details
            message: Optional custom error message (defaults to 'Hiero error')
        """
        return cls(HIERO_ERROR, message, data)


def handle_sdk_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JsonRpcError:
            raise
        except PrecheckError as e:
            logger.error(f"PrecheckError (status: {ResponseCode(e.status).name}, method: {func.__name__})")
            raise JsonRpcError.hiero_error({"status": ResponseCode(e.status).name}) from e

        except ReceiptStatusError as e:
            logger.error(f"ReceiptStatusError (status: {ResponseCode(e.status).name}, method: {func.__name__})")
            raise JsonRpcError.hiero_error({"status": ResponseCode(e.status).name}) from e

        except MaxAttemptsError as e:
            logger.error(f"MaxAttemptsError (method: {func.__name__})")
            raise JsonRpcError.hiero_error(message=str(e)) from e

        except Exception as e:
            logger.exception("Unhandled error in RPC handler")
            raise JsonRpcError.internal_error(message="Internal error") from e

    return wrapper
