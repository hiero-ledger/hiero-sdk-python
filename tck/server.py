"""TCK Server implementation using Flask."""
import os
from dataclasses import dataclass, field
import logging
from flask import Flask, jsonify, request
from tck.errors import JsonRpcError
from tck.handlers import safe_dispatch
from tck.protocol import build_json_rpc_error_response, build_json_rpc_success_response, parse_json_rpc_request

@dataclass
class ServerConfig:
    """Configuration for the TCK server."""
    host: str = field(default_factory=lambda: os.getenv("TCK_HOST", "localhost"))
    port: int = field(default_factory=lambda: _parse_port(os.getenv("TCK_PORT", "8544")))

def _parse_port(port_str: str) -> int:
    try:
        port = int(port_str)
    except ValueError as exc:
        raise ValueError(f"TCK_PORT must be a valid integer, got: '{port_str}'") from exc
    if not (1 <= port <= 65535):
        raise ValueError(f"TCK_PORT must be between 1 and 65535, got: {port}")
    return port

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route("/", methods=['POST'])
def json_rpc_endpoint():
    """JSON-RPC 2.0 endpoint to handle requests."""
    if request.mimetype != 'application/json':
        error = JsonRpcError.parse_error(message='Parse error: Content-Type must be application/json')
        return jsonify(build_json_rpc_error_response(error, None))
    try:
        request_json = request.get_json(force=True)
    except Exception:
        # Malformed JSON - return parse error
        error = JsonRpcError.parse_error()
        return jsonify(build_json_rpc_error_response(error, None))
    
    # Parse and validate the JSON-RPC request
    parsed_request = parse_json_rpc_request(request_json)
    if isinstance(parsed_request, JsonRpcError):
        # Use request id if available, else None per JSON-RPC 2.0 spec
        request_id = request_json.get('id') if isinstance(request_json, dict) else None
        return jsonify(build_json_rpc_error_response(parsed_request, request_id))


    method_name = parsed_request['method']
    params = parsed_request['params']
    request_id = parsed_request['id']
    session_id = parsed_request.get('sessionId')

    # Safely dispatch the request to the appropriate handler
    response = safe_dispatch(method_name, params, session_id, request_id)

    # If the response is already an error response, return it directly
    if isinstance(response, dict) and 'jsonrpc' in response and 'error' in response:
        return jsonify(response)

    # Build and return the success response
    return jsonify(build_json_rpc_success_response(response, request_id))

def start_server(config: ServerConfig | None = None):
    """Start the JSON-RPC server using Flask."""
    if config is None:
        config = ServerConfig()
    logger.info(f"Starting TCK server on {config.host}:{config.port}")
    app.run(host=config.host, port=config.port)



if __name__ == "__main__":
    start_server()