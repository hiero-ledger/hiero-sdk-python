import random
import requests
from hiero_sdk_python.account.account_id import AccountId

class Network:
    """
    Manages the network configuration for connecting to the Hedera network.
    """

    MIRROR_ADDRESS_DEFAULT = {
        'mainnet': 'hcs.mainnet.mirrornode.hedera.com:5600',
        'testnet': 'hcs.testnet.mirrornode.hedera.com:5600',
        'previewnet': 'hcs.previewnet.mirrornode.hedera.com:5600',
        'solo': 'localhost:5600'
    }

    MIRROR_NODE_URLS = {
        'mainnet': 'https://mainnet-public.mirrornode.hedera.com',
        'testnet': 'https://testnet.mirrornode.hedera.com',
        'previewnet': 'https://previewnet.mirrornode.hedera.com',
        'solo': 'http://localhost:8080'
    }

    DEFAULT_NODES = {
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
        nodes: list = None,
        mirror_address: str = None,
    ):
        """
        Initializes the Network with the specified network name or custom config.

        Args:
            network (str): One of 'mainnet', 'testnet', 'previewnet', 'solo', or a custom name if you prefer.
            nodes (list, optional): A list of (node_address, AccountId) pairs. If provided, we skip fetching from the mirror.
            mirror_address (str, optional): A mirror node address (host:port) for topic queries.
                                            If not provided, we'll use a default from MIRROR_ADDRESS_DEFAULT[network].
        """
        self.network = network
        self.mirror_address = mirror_address or self.MIRROR_ADDRESS_DEFAULT.get(network, 'localhost:5600')

        if nodes is not None:
            self.nodes = nodes
        else:
            self.nodes = self._fetch_nodes_from_mirror_node()
            if not self.nodes:
                if self.network in self.DEFAULT_NODES:
                    self.nodes = self.DEFAULT_NODES[self.network]
                else:
                    raise ValueError(f"No default nodes for network='{self.network}'")

        self._select_node()

    def _fetch_nodes_from_mirror_node(self):
        """
        Fetches the list of nodes from the Hedera Mirror Node REST API.
        Returns:
            list: A list of tuples [(node_address, AccountId), ...].
        """
        base_url = self.MIRROR_NODE_URLS.get(self.network)
        if not base_url:
            print(f"No known mirror node URL for network='{self.network}'. Skipping fetch.")
            return []

        url = f"{base_url}/api/v1/network/nodes?limit=100&order=desc"

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            nodes = []
            for node in data.get('nodes', []):
                service_endpoints = node.get('service_endpoints', [])
                for endpoint in service_endpoints:
                    if endpoint.get('port') == 50211 and endpoint.get('protocol') == 'PROTOBUF':
                        ip_address = endpoint.get('ip_address_v4')
                        if ip_address:
                            address = f"{ip_address}:{endpoint['port']}"
                            account_id_str = node['node_account_id']
                            account_id = AccountId.from_string(account_id_str)
                            nodes.append((address, account_id))
            return nodes
        except requests.RequestException as e:
            print(f"Error fetching nodes from mirror node API: {e}")
            return []

    def _select_node(self):
        """
        Select a random node from self.nodes and store it if you want to track a 'current' node.
        This is optional. The client can still pick or switch nodes as needed.
        """
        if not self.nodes:
            raise ValueError("No nodes available to select.")
        self.node_address, self.node_account_id = random.choice(self.nodes)
        # print(f"Selected node: {self.node_address} (Account ID: {self.node_account_id})")

    def get_node_address(self, node_account_id):
        """
        Return the gRPC address (host:port) for the given node_account_id, or None if not found.
        """
        for address, acct_id in self.nodes:
            if acct_id == node_account_id:
                return address
        return None

    def get_mirror_address(self) -> str:
        """
        Return the configured mirror node address used for mirror queries.
        """
        return self.mirror_address
