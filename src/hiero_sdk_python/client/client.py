from hiero_sdk_python.logger.logger import Logger, LogLevel
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
        
        self.mirror_channel = None
        self.mirror_stub = None

        self.max_attempts = 10
        
        self._init_mirror_stub()
        
        self.logger = Logger(LogLevel.from_env(), "hiero_sdk_python")

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

    def close(self):
        """
        Closes any open gRPC channels and frees resources.
        Call this when you are done using the Client to ensure a clean shutdown.
        """

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