"""Network module for managing Hedera SDK connections."""
import secrets
from typing import Dict, List, Optional, Any, Tuple

import requests

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.node import _Node



class Network:
    """
    Manages the network configuration for connecting to the Hedera network.
    """

    # Mirror node gRPC addresses (always use TLS, port 443 for HTTPS)
    MIRROR_ADDRESS_DEFAULT: Dict[str,str] = {
        'mainnet': 'mainnet.mirrornode.hedera.com:443',
        'testnet': 'testnet.mirrornode.hedera.com:443',
        'previewnet': 'previewnet.mirrornode.hedera.com:443',
        'solo': 'localhost:5600'  # Local development only
    }

    # Mirror node REST API base URLs (HTTPS for production networks, HTTP for localhost)
    MIRROR_NODE_URLS: Dict[str,str] = {
        'mainnet': 'https://mainnet-public.mirrornode.hedera.com',
        'testnet': 'https://testnet.mirrornode.hedera.com',
        'previewnet': 'https://previewnet.mirrornode.hedera.com',
        'solo': 'http://localhost:5551'  # Local development only
    }

    DEFAULT_NODES: Dict[str,List[_Node]] = {
        'mainnet': [
            ("35.237.200.180:50211", AccountId(0, 0, 3)),
            ("35.186.191.247:50211", AccountId(0, 0, 4)),
            ("35.192.2.25:50211", AccountId(0, 0, 5)),
            ("35.199.161.108:50211", AccountId(0, 0, 6)),
            ("35.203.82.240:50211", AccountId(0, 0, 7)),
            ("35.236.5.219:50211", AccountId(0, 0, 8)),
            ("35.197.192.225:50211", AccountId(0, 0, 9)),
            ("35.242.233.154:50211", AccountId(0, 0, 10)),
            ("35.240.118.96:50211", AccountId(0, 0, 11)),
            ("35.204.86.32:50211", AccountId(0, 0, 12)),
            ("35.234.132.107:50211", AccountId(0, 0, 13)),
            ("35.236.2.27:50211", AccountId(0, 0, 14)),
        ],
        'testnet': [
            ("0.testnet.hedera.com:50211", AccountId(0, 0, 3)),
            ("1.testnet.hedera.com:50211", AccountId(0, 0, 4)),
            ("2.testnet.hedera.com:50211", AccountId(0, 0, 5)),
            ("3.testnet.hedera.com:50211", AccountId(0, 0, 6)),
        ],
        'previewnet': [
            ("0.previewnet.hedera.com:50211", AccountId(0, 0, 3)),
            ("1.previewnet.hedera.com:50211", AccountId(0, 0, 4)),
            ("2.previewnet.hedera.com:50211", AccountId(0, 0, 5)),
            ("3.previewnet.hedera.com:50211", AccountId(0, 0, 6)),
        ],
        'solo': [
            ("localhost:50211", AccountId(0, 0, 3))
        ],
        'localhost': [
            ("localhost:50211", AccountId(0, 0, 3))
        ],
        'local': [
            ("localhost:50211", AccountId(0, 0, 3))
        ],
    }

    LEDGER_ID: Dict[str, bytes] = {
        'mainnet': bytes.fromhex('00'),
        'testnet': bytes.fromhex('01'),
        'previewnet': bytes.fromhex('02'),
        'solo': bytes.fromhex('03')
    }

    def __init__(
        self,
        network: str = 'testnet',
        nodes: Optional[List[_Node]] = None,
        mirror_address: Optional[str] = None,
        ledger_id: bytes | None = None
    ) -> None:
        """
        Initializes the Network with the specified network name or custom config.

        Args:
            network (str): One of 'mainnet', 'testnet', 'previewnet', 'solo',
            or a custom name if you prefer.
            nodes (list, optional): A list of (node_address, AccountId) pairs. 
            If provided, we skip fetching from the mirror.
            mirror_address (str, optional): A mirror node address (host:port) for topic queries.
                            If not provided,
                            we'll use a default from MIRROR_ADDRESS_DEFAULT[network].
        
        Note:
            TLS is enabled by default for hosted networks (mainnet, testnet, previewnet).
            For local networks (solo, localhost) and custom networks, TLS is disabled by default.
            Certificate verification is enabled by default for all networks.
            Use Client.set_transport_security() and Client.set_verify_certificates() to customize.
        """
        self.network: str = network or 'testnet'
        self.mirror_address: str = mirror_address or self.MIRROR_ADDRESS_DEFAULT.get(
            network, 'localhost:5600'
        )

        self.ledger_id = ledger_id or self.LEDGER_ID.get(network, bytes.fromhex('03'))
        
        # Default TLS configuration: enabled for hosted networks, disabled for local/custom
        hosted_networks = ('mainnet', 'testnet', 'previewnet')
        self._transport_security: bool = self.network in hosted_networks
        self._verify_certificates: bool = True  # Always enabled by default
        self._root_certificates: Optional[bytes] = None

        if nodes is not None:
            final_nodes = nodes
        elif self.network in ('solo', 'localhost', 'local'):
            final_nodes = self._fetch_nodes_from_default_nodes()
        else:
            fetched = self._fetch_nodes_from_mirror_node()
            if not fetched and self.network in self.DEFAULT_NODES:
                final_nodes = self._fetch_nodes_from_default_nodes()
            elif fetched:
                final_nodes = fetched
            else:
                raise ValueError(f"No default nodes for network='{self.network}'")

        self.nodes: List[_Node] = final_nodes
        
        # Apply TLS configuration to all nodes
        for node in self.nodes:
            node._apply_transport_security(self._transport_security)  # pylint: disable=protected-access
            node._set_verify_certificates(self._verify_certificates)  # pylint: disable=protected-access
            node._set_root_certificates(self._root_certificates)  # pylint: disable=protected-access

        self._node_index: int = secrets.randbelow(len(self.nodes))
        self.current_node: _Node = self.nodes[self._node_index]

    def _fetch_nodes_from_mirror_node(self) -> List[_Node]:
        """
        Fetches the list of nodes from the Hedera Mirror Node REST API.
        Returns:
            list: A list of _Node objects.
        """
        base_url: Optional[str] = self.MIRROR_NODE_URLS.get(self.network)
        if not base_url:
            print(f"No known mirror node URL for network='{self.network}'. Skipping fetch.")
            return []

        url: str = f"{base_url}/api/v1/network/nodes?limit=100&order=desc"

        try:
            response: requests.Response = requests.get(url, timeout=30) # Add 30 second timeout
            response.raise_for_status()
            data: Dict[str, Any] = response.json()

            nodes: List[_Node] = []
            # Process each node from the mirror node API response
            for node in data.get('nodes', []):
                address_book: NodeAddress = NodeAddress._from_dict(node)
                account_id: AccountId = address_book._account_id
                address: str = str(address_book._addresses[0])

                nodes.append(_Node(account_id, address, address_book))

            return nodes
        except requests.RequestException as e:
            print(f"Error fetching nodes from mirror node API: {e}")
            return []

    def _fetch_nodes_from_default_nodes(self) -> List[_Node]:
        """
        Fetches the list of nodes from the default nodes for the network.
        """
        nodes: List[_Node] = []
        for node in self.DEFAULT_NODES[self.network]:
            nodes.append(_Node(node[1], node[0], None))
        return nodes

    def _select_node(self) -> _Node:
        """
        Select the next node in the collection of available nodes using round-robin selection.
        
        This method increments the internal node index, wrapping around when reaching the end
        of the node list, and updates the current_node reference.
        
        Raises:
            ValueError: If no nodes are available for selection.
        
        Returns:
            _Node: The selected node instance.
        """
        if not self.nodes:
            raise ValueError("No nodes available to select.")
        self._node_index = (self._node_index + 1) % len(self.nodes)
        self.current_node = self.nodes[self._node_index]
        return self.current_node
    
    def _get_node(self, account_id: AccountId) -> Optional[_Node]:
        """
        Get a node matching the given account ID.

        Args:
            account_id (AccountId): The account ID of the node to locate.

        Returns:
            Optional[_Node]: The matching node, or None if not found.
        """
        for node in self.nodes:
            if node._account_id == account_id:
                return node
        return None

    def get_mirror_address(self) -> str:
        """
        Return the configured mirror node address used for mirror gRPC queries.
        Mirror nodes always use TLS, so addresses should use port 443 for HTTPS.
        """
        return self.mirror_address
    
    def _parse_mirror_address(self) -> Tuple[str, int]:
        """
        Parse mirror_address into host and port.
        
        Returns:
            Tuple[str, int]: (host, port) tuple
        """
        mirror_addr = self.mirror_address
        if ':' in mirror_addr:
            host, port_str = mirror_addr.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 443
        else:
            host = mirror_addr
            port = 443
        return (host, port)
    
    def _determine_scheme_and_port(self, host: str, port: int) -> Tuple[str, int]:
        """
        Determine the scheme (http/https) and port for the REST URL.
        
        Args:
            host: The hostname
            port: The port number
            
        Returns:
            Tuple[str, int]: (scheme, port) tuple
        """
        is_localhost = host in ('localhost', '127.0.0.1')
        
        if is_localhost:
            scheme = 'http'
            if port == 443:
                port = 8080  # Default REST port for localhost
        else:
            scheme = 'https'
            if port == 5600:  # gRPC port, use 443 for REST
                port = 443
        
        return (scheme, port)
    
    def _build_rest_url(self, scheme: str, host: str, port: int) -> str:
        """
        Build the final REST URL with optional port.
        
        Args:
            scheme: URL scheme (http or https)
            host: Hostname
            port: Port number
            
        Returns:
            str: Complete REST URL with /api/v1 suffix
        """
        is_default_port = (scheme == 'https' and port == 443) or (scheme == 'http' and port == 80)
        
        if is_default_port:
            return f"{scheme}://{host}/api/v1"
        return f"{scheme}://{host}:{port}/api/v1"
    
    def get_mirror_rest_url(self) -> str:
        """
        Get the REST API base URL for the mirror node.
        Returns the URL in format: scheme://host[:port]/api/v1
        For non-localhost networks, defaults to https:// with port 443.
        """
        base_url = self.MIRROR_NODE_URLS.get(self.network)
        if base_url:
            # MIRROR_NODE_URLS contains base URLs, append /api/v1
            return f"{base_url}/api/v1"
        
        # Fallback: construct from mirror_address
        host, port = self._parse_mirror_address()
        scheme, port = self._determine_scheme_and_port(host, port)
        return self._build_rest_url(scheme, host, port)

    def set_transport_security(self, enabled: bool) -> None:
        """
        Enable or disable TLS for consensus node connections.
        """
        if self._transport_security == enabled:
            return
        for node in self.nodes:
            node._apply_transport_security(enabled)  # pylint: disable=protected-access
        self._transport_security = enabled

    def is_transport_security(self) -> bool:
        """
        Determine if TLS is enabled for consensus node connections.
        """
        return self._transport_security

    def set_verify_certificates(self, verify: bool) -> None:
        """
        Enable or disable server certificate verification when TLS is enabled.
        """
        if self._verify_certificates == verify:
            return
        for node in self.nodes:
            node._set_verify_certificates(verify)  # pylint: disable=protected-access
        self._verify_certificates = verify

    def set_tls_root_certificates(self, root_certificates: Optional[bytes]) -> None:
        """
        Provide custom root certificates to use when establishing TLS channels.
        """
        self._root_certificates = root_certificates
        for node in self.nodes:
            node._set_root_certificates(root_certificates)  # pylint: disable=protected-access

    def get_tls_root_certificates(self) -> Optional[bytes]:
        """
        Retrieve the configured root certificates used for TLS channels.
        """
        return self._root_certificates

    def is_verify_certificates(self) -> bool:
        """
        Determine if certificate verification is enabled.
        """
        return self._verify_certificates