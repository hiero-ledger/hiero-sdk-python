from hiero_sdk_python.tck.errors import JsonRpcError
from hiero_sdk_python.tck.handlers import safe_dispatch
from hiero_sdk_python.tck.protocol import build_json_rpc_error_response, build_json_rpc_success_response, parse_json_rpc_request
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=['POST'])
def json_rpc_endpoint():
    """JSON-RPC 2.0 endpoint to handle requests."""
    # Parse and validate the JSON-RPC request
    parsed_request = parse_json_rpc_request(request.get_json())
    if isinstance(parsed_request, JsonRpcError):
        return build_json_rpc_error_response(parsed_request, request.get('id'))

    method_name = parsed_request['method']
    params = parsed_request['params']
    request_id = parsed_request['id']
    session_id = parsed_request['session_id'] if 'session_id' in parsed_request else None

    # Safely dispatch the request to the appropriate handler
    response = safe_dispatch(method_name, params, session_id)

    # If the response is already an error response, return it directly
    if isinstance(response, dict) and 'error' in response:
        return response

    # Build and return the success response
    return build_json_rpc_success_response(response, request_id)

def start_server():
    """Start the JSON-RPC server using Uvicorn."""
    host = "localhost"
    tck_port = 8544
    print(f"Starting TCK server on {host}:{tck_port}")
    app.run(host=host, port=tck_port)



if __name__ == "__main__":
    start_server()