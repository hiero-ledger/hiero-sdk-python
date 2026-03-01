from typing import Any, Dict, Optional, List
from hiero_sdk_python.node import _Node
from hiero_sdk_python import Client, AccountId, PrivateKey, Network
from tck.handlers.registry import register_handler, validate_request_params
from tck.client_manager import store_client, remove_client
from tck.errors import JsonRpcError


def _create_node_objects(node_addresses: List[str]) -> List[_Node]:
    """Convert node addresses to _Node objects with generated AccountIds.
    Args:
        node_addresses: List of node address strings
        
    Returns:
        List of _Node objects with sequential AccountIds starting from 0.0.3
    """
    node_objects = []
    for idx, node_address in enumerate(node_addresses):
        account_id = AccountId(0, 0, 3 + idx)
        node_obj = _Node(account_id, node_address, None)
        node_objects.append(node_obj)
    return node_objects


def _create_custom_network_client(network_config: Dict[str, Any]) -> Client:
    """Create a client with custom network configuration.
    Args:
        network_config: Dictionary containing 'nodes' key with list of node addresses
  
    Returns:
        Configured Client instance

    Raises:
        JsonRpcError: If nodes configuration is invalid
    """
    nodes = network_config.get('nodes')
    if not isinstance(nodes, list) or len(nodes) == 0 or not all(isinstance(node, str) for node in nodes):
        raise JsonRpcError.invalid_params_error(message='Invalid params: nodes must be a non-empty list of strings')
    
    node_objects = _create_node_objects(nodes)
    network = Network(nodes=node_objects)
    return Client(network)


def _create_client(network_param: Optional[Any]) -> Client:
    """Create and return the appropriate Client based on network parameter.
    Args:
        network_param: Network specification (None/'testnet' for testnet, 'mainnet', or custom dict)
        
    Returns:
        Configured Client instance
        
    Raises:
        JsonRpcError: If network specification is invalid
    """
    if network_param is None or network_param == 'testnet':
        return Client.for_testnet()

    if network_param == 'mainnet':
        return Client.for_mainnet()

    if isinstance(network_param, dict) and 'nodes' in network_param:
        return _create_custom_network_client(network_param)

    raise JsonRpcError.invalid_params_error(message='Invalid params: unknown network specification')


def _parse_operator_credentials(params: Dict[str, Any]) -> tuple[AccountId, PrivateKey]:
    """Parse and validate operator credentials from parameters.
    
    Args:
        params: Request parameters containing operatorAccountId and operatorPrivateKey
        
    Returns:
        Tuple of (AccountId, PrivateKey)
    Raises:
        JsonRpcError: If credentials cannot be parsed
    """
    operator_account_id_str = params['operatorAccountId']
    operator_private_key_str = params['operatorPrivateKey']

    try:
        operator_account_id = AccountId.from_string(operator_account_id_str)
        operator_private_key = PrivateKey.from_string(operator_private_key_str)
    except Exception as e:
        raise JsonRpcError.invalid_params_error(message=f'Invalid params: invalid operatorAccountId/operatorPrivateKey format - {str(e)}') from e

    return operator_account_id, operator_private_key


@register_handler("setup")
def setup_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Setup handler to initialize SDK clients with operator credentials and network configuration."""
    # Validate required parameters
    required_fields = {
        'operatorAccountId': str,
        'operatorPrivateKey': str
    }
    validate_request_params(params, required_fields)

    # Parse operator credentials
    operator_account_id, operator_private_key = _parse_operator_credentials(params)

    # Create client based on network configuration
    client = _create_client(params.get('network'))
    client.set_operator(operator_account_id, operator_private_key)

    # Store the initialized client
    effective_session_id = session_id or "default"
    store_client(effective_session_id, client)

    return {"status": "success", "sessionId": effective_session_id}

@register_handler("reset")
def reset_handler(params: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Reset handler to close connections and clear client state."""
    target_session_id = params.get('sessionId') or session_id
    if target_session_id is None:
        target_session_id = "default"
    remove_client(target_session_id)
    return {"status": "reset completed"}
