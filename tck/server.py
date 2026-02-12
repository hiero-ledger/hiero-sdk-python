"""TCK Server implementation using Flask."""
import os
from dataclasses import dataclass, field
from tck.errors import PARSE_ERROR, JsonRpcError
from tck.handlers import safe_dispatch
from tck.protocol import build_json_rpc_error_response, build_json_rpc_success_response, parse_json_rpc_request
from flask import Flask, request

@dataclass
class ServerConfig:
    """Configuration for the TCK server."""
    host: str = field(default_factory=lambda: os.getenv("TCK_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("TCK_PORT", "8544")))

app = Flask(__name__)

@app.route("/", methods=['POST'])
def json_rpc_endpoint():
    """JSON-RPC 2.0 endpoint to handle requests."""
    try:
        request_json = request.get_json()
    except Exception:
        # Malformed JSON - return parse error
        error = JsonRpcError(PARSE_ERROR, 'Parse error')
        return build_json_rpc_error_response(error, None)
    
    # Parse and validate the JSON-RPC request
    parsed_request = parse_json_rpc_request(request_json)
    if isinstance(parsed_request, JsonRpcError):
        return build_json_rpc_error_response(parsed_request, None)

    method_name = parsed_request['method']
    params = parsed_request['params']
    request_id = parsed_request['id']
    session_id = parsed_request.get('sessionId')

    # Safely dispatch the request to the appropriate handler
    response = safe_dispatch(method_name, params, session_id, request_id)

    # If the response is already an error response, return it directly
    if isinstance(response, dict) and 'error' in response:
        return response

    # Build and return the success response
    return build_json_rpc_success_response(response, request_id)

def start_server(config: ServerConfig = ServerConfig()):
    """Start the JSON-RPC server using Flask."""
    print(f"Starting TCK server on {config.host}:{config.port}")
    app.run(host=config.host, port=config.port)



if __name__ == "__main__":
    start_server()