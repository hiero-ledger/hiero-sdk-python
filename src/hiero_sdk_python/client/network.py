"""Network module for managing Hedera SDK connections."""
import secrets
from typing import Dict, List

import requests

from typing import Dict, List, Tuple
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.node import _Node



class Network:
    """
    Manages the network configuration for connecting to the Hedera network.
    """

    MIRROR_ADDRESS_DEFAULT: Dict[str,str] = {
        'mainnet': 'hcs.mainnet.mirrornode.hedera.com:5600',
        'testnet': 'hcs.testnet.mirrornode.hedera.com:5600',
        'previewnet': 'hcs.previewnet.mirrornode.hedera.com:5600',
        'solo': 'localhost:5600'
    }

    MIRROR_NODE_URLS: Dict[str,str] = {
        'mainnet': 'https://mainnet-public.mirrornode.hedera.com',
        'testnet': 'https://testnet.mirrornode.hedera.com',
        'previewnet': 'https://previewnet.mirrornode.hedera.com',
        'solo': 'http://localhost:8080'
    }

    DEFAULT_NODES: Dict[str,List[Tuple[str,AccountId]]] = {
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
    }

    def __init__(
        self,
        network: str = 'testnet',
        nodes: list[_Node] = None,
        mirror_address: str = None,
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
        """
        self.network: str = network or 'testnet'
        self.mirror_address: str = mirror_address or self.MIRROR_ADDRESS_DEFAULT.get(
            network, 'localhost:5600'
        )

        if nodes is not None:
            self.nodes: List[_Node] = nodes
        elif self.network in ('solo', 'localhost', 'local'):
            self.nodes = self._fetch_nodes_from_default_nodes()
        else:
            self.nodes = self._fetch_nodes_from_mirror_node()
            if not self.nodes and self.network in self.DEFAULT_NODES:
                self.nodes = self._fetch_nodes_from_default_nodes()
            elif not self.nodes:
                raise ValueError(f"No default nodes for network='{self.network}'")

        self._node_index: int = secrets.randbelow(len(self.nodes))
        self.current_node: _Node = self.nodes[self._node_index]

    def _fetch_nodes_from_mirror_node(self) -> List[_Node]:
        """
        Fetches the list of nodes from the Hedera Mirror Node REST API.
        Returns:
            list: A list of _Node objects.
        """
        base_url: str = self.MIRROR_NODE_URLS.get(self.network)
        if not base_url:
            print(f"No known mirror node URL for network='{self.network}'. Skipping fetch.")
            return []

        url: str = f"{base_url}/api/v1/network/nodes?limit=100&order=desc"

        try:
            response: requests.Response = requests.get(url, timeout=30) # Add 30 second timeout
            response.raise_for_status()
            data: dict = response.json()

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

    def get_mirror_address(self) -> str:
        """
        Return the configured mirror node address used for mirror queries.
        """
        return self.mirror_address
