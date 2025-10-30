"""
Client module for interacting with the Hedera network.
"""

from typing import NamedTuple, List, Union

import grpc

from hiero_sdk_python.logger.logger import Logger, LogLevel
from hiero_sdk_python.hapi.mirror import (
    consensus_service_pb2_grpc as mirror_consensus_grpc,
)

from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

from .network import Network

class Operator(NamedTuple):
    """A named tuple for the operator's account ID and private key."""
    account_id: AccountId
    private_key: PrivateKey

class Client:
    """
    Client to interact with Hedera network services including mirror nodes and transactions.
    """
    def __init__(self, network: Network = None) -> None:
        """
        Initializes the Client with a given network configuration.
        If no network is provided, it defaults to a new Network instance.
        """
        self.operator_account_id: AccountId = None
        self.operator_private_key: PrivateKey = None

        if network is None:
            network = Network()
        self.network: Network = network

        self.mirror_channel: grpc.Channel = None
        self.mirror_stub: mirror_consensus_grpc.ConsensusServiceStub = None

        self.max_attempts: int = 10

        self._init_mirror_stub()

        self.logger: Logger = Logger(LogLevel.from_env(), "hiero_sdk_python")

    def _init_mirror_stub(self) -> None:
        """
        Connect to a mirror node for topic message subscriptions.
        We now use self.network.get_mirror_address() for a configurable mirror address.
        """
        mirror_address = self.network.get_mirror_address()
        self.mirror_channel = grpc.secure_channel(mirror_address, grpc.ssl_channel_credentials())
        self.mirror_stub = mirror_consensus_grpc.ConsensusServiceStub(self.mirror_channel)

    def set_operator(self, account_id: AccountId, private_key: PrivateKey) -> None:
        """
        Sets the operator credentials (account ID and private key).
        """
        self.operator_account_id = account_id
        self.operator_private_key = private_key

    @property
    def operator(self) -> Union[Operator,None]:
        """
        Returns an Operator namedtuple if both account ID and private key are set,
        otherwise None.
        """
        if self.operator_account_id and self.operator_private_key:
            return Operator(
                account_id=self.operator_account_id, private_key=self.operator_private_key
            )
        return None

    def generate_transaction_id(self) -> TransactionId:
        """
        Generates a new transaction ID, requiring that the operator_account_id is set.
        """
        if self.operator_account_id is None:
            raise ValueError("Operator account ID must be set to generate transaction ID.")
        return TransactionId.generate(self.operator_account_id)

    def get_node_account_ids(self) -> List[AccountId]:
        """
        Returns a list of node AccountIds that the client can use to send queries and transactions.
        """
        if self.network and self.network.nodes:
            return [node._account_id for node in self.network.nodes]  # pylint: disable=W0212
        raise ValueError("No nodes available in the network configuration.")

    def close(self) -> None:
        """
        Closes any open gRPC channels and frees resources.
        Call this when you are done using the Client to ensure a clean shutdown.
        """

        if self.mirror_channel is not None:
            self.mirror_channel.close()
            self.mirror_channel = None

        self.mirror_stub = None

    def __enter__(self) -> "Client":
        """
        Allows the Client to be used in a 'with' statement for automatic resource management.
        This ensures that channels are closed properly when the block is exited.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Automatically close channels when exiting 'with' block.
        """
        self.close()