import grpc
from collections import namedtuple

from hiero_sdk_python.hapi.mirror import (
    consensus_service_pb2_grpc as mirror_consensus_grpc,
)

from .network import Network
from hiero_sdk_python.transaction.transaction_id import TransactionId

Operator = namedtuple('Operator', ['account_id', 'private_key'])

class Client:
    """
    Represents a client to interact with the Hedera network.
    """

    def __init__(self, network=None):
        self.operator_account_id = None
        self.operator_private_key = None

        if network is None:
            network = Network()
        self.network = network
        
        self.channel = None

        self.mirror_channel = None
        self.mirror_stub = None

        self.max_attempts = 10

        node_account_ids = self.get_node_account_ids()
        if not node_account_ids:
            raise ValueError("No nodes available in the network configuration.")

        initial_node_id = node_account_ids[0]
        self._switch_node(initial_node_id)

        self._init_mirror_stub()

    def _init_mirror_stub(self):
        """
        Connect to a mirror node for topic message subscriptions.
        We now use self.network.get_mirror_address() for a configurable mirror address.
        """
        mirror_address = self.network.get_mirror_address()
        self.mirror_channel = grpc.insecure_channel(mirror_address)
        self.mirror_stub = mirror_consensus_grpc.ConsensusServiceStub(self.mirror_channel)

    def set_operator(self, account_id, private_key):
        """
        Sets the operator credentials (account ID and private key).
        """
        self.operator_account_id = account_id
        self.operator_private_key = private_key

    @property
    def operator(self):
        """
        Returns an Operator namedtuple if both account ID and private key are set,
        otherwise None.
        """
        if self.operator_account_id and self.operator_private_key:
            return Operator(account_id=self.operator_account_id, private_key=self.operator_private_key)
        return None

    def generate_transaction_id(self):
        """
        Generates a new transaction ID, requiring that the operator_account_id is set.
        """
        if self.operator_account_id is None:
            raise ValueError("Operator account ID must be set to generate transaction ID.")
        return TransactionId.generate(self.operator_account_id)

    def get_node_account_ids(self):
        """
        Returns a list of node AccountIds that the client can use to send queries and transactions.
        """
        if self.network and self.network.nodes:
            return [account_id for (address, account_id) in self.network.nodes]
        else:
            raise ValueError("No nodes available in the network configuration.")

    def _switch_node(self, node_account_id):
        """
        Switches to the specified node in the network and updates the gRPC stubs.
        """
        node_address = self.network.get_node_address(node_account_id)
        if node_address is None:
            raise ValueError(f"No node address found for account ID {node_account_id}")

        self.channel = grpc.insecure_channel(node_address)
        self.node_account_id = node_account_id

    def close(self):
        """
        Closes any open gRPC channels and frees resources.
        Call this when you are done using the Client to ensure a clean shutdown.
        """
        if self.channel is not None:
            self.channel.close()
            self.channel = None

        if self.mirror_channel is not None:
            self.mirror_channel.close()
            self.mirror_channel = None

        self.mirror_stub = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Automatically close channels when exiting 'with' block.
        """
        self.close()