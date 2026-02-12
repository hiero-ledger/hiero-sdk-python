
"""Error code constants for the TCK server."""
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
HIERO_ERROR = -32001
# These constants can be used throughout the codebase to represent specific error conditions.

class JsonRpcError(Exception):
    """Class representing a JSON-RPC error."""
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        """Convert the error to a dictionary representation."""
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            error["data"] = self.data
        return error

    
    @classmethod
    def create_parse_error(cls, data=None) -> "JsonRpcError":
        """Create a Parse Error JSON-RPC error."""
        return JsonRpcError(PARSE_ERROR, "Parse error", data)
    
    @classmethod
    def create_invalid_request_error(cls, data=None) -> "JsonRpcError":
        """Create an Invalid Request JSON-RPC error."""
        return JsonRpcError(INVALID_REQUEST, "Invalid Request", data)
    
    @classmethod
    def create_method_not_found_error(cls, data=None) -> "JsonRpcError":
        """Create a Method Not Found JSON-RPC error."""
        return JsonRpcError(METHOD_NOT_FOUND, "Method not found", data)
    
    @classmethod
    def create_invalid_params_error(cls, data=None) -> "JsonRpcError":
        """Create an Invalid Params JSON-RPC error."""
        return JsonRpcError(INVALID_PARAMS, "Invalid params", data)
    
    @classmethod
    def create_internal_error(cls, data=None) -> "JsonRpcError":
        """Create an Internal Error JSON-RPC error."""
        return JsonRpcError(INTERNAL_ERROR, "Internal error", data)
    
    @classmethod
    def create_hiero_error(cls, data=None) -> "JsonRpcError":
        """Create a Hiero-specific JSON-RPC error."""
        return JsonRpcError(HIERO_ERROR, "Hiero error", data)