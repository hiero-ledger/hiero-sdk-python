"""
Client module for interacting with the Hedera network.
"""

from decimal import Decimal
import os
from typing import NamedTuple, List, Union, Optional, Literal
from dotenv import load_dotenv
import grpc

from hiero_sdk_python.hbar import Hbar
from hiero_sdk_python.logger.logger import Logger, LogLevel
from hiero_sdk_python.hapi.mirror import (
    consensus_service_pb2_grpc as mirror_consensus_grpc,
)

from hiero_sdk_python.transaction.transaction_id import TransactionId
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.crypto.private_key import PrivateKey

from .network import Network

DEFAULT_MAX_QUERY_PAYMENT = Hbar(1)

NetworkName = Literal["mainnet", "testnet", "previewnet"]

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
        self.default_max_query_payment: Hbar = DEFAULT_MAX_QUERY_PAYMENT

        self._init_mirror_stub()

        self.logger: Logger = Logger(LogLevel.from_env(), "hiero_sdk_python")

    @classmethod
    def from_env(cls, network: Optional[NetworkName] = None) -> "Client":
        """
        Initialize client from environment variables.
        Automatically loads .env file if present.

        Args:
            network (str, optional): Override the network ("testnet", "mainnet", "previewnet").
                                     If not provided, checks 'NETWORK' env var. 
                                     Defaults to 'testnet' if neither is set.

        Raises:
            ValueError: If OPERATOR_ID or OPERATOR_KEY environment variables are not set.

        Example:
            # Defaults to testnet if no env vars set
            client = Client.from_env()
        """
        load_dotenv()
        
        if network:
            network_name = network
        else:
            network_name = os.getenv('NETWORK') or 'testnet'

        network_name = network_name.lower()
        
        try:
            client = cls(Network(network_name))
        except ValueError:
            raise ValueError(f"Invalid network name: {network_name}")

        operator_id_str = os.getenv("OPERATOR_ID")
        operator_key_str = os.getenv("OPERATOR_KEY")

        if not operator_id_str:
            raise ValueError("OPERATOR_ID environment variable is required for Client.from_env()")
        if not operator_key_str:
            raise ValueError("OPERATOR_KEY environment variable is required for Client.from_env()")

        operator_id = AccountId.from_string(operator_id_str)
        operator_key = PrivateKey.from_string(operator_key_str)

        client.set_operator(operator_id, operator_key)

        return client

    @classmethod
    def for_testnet(cls) -> "Client":
        """
        Create a Client configured for Hedera Testnet.
        
        Note: Operator must be set manually using set_operator().

        Returns:
            Client: A Client instance configured for testnet.
        """
        return cls(Network("testnet"))

    @classmethod
    def for_mainnet(cls) -> "Client":
        """
        Create a Client configured for Hedera Mainnet.
        
        Note: Operator must be set manually using set_operator().

        Returns:
            Client: A Client instance configured for mainnet.
        """
        return cls(Network("mainnet"))

    @classmethod
    def for_previewnet(cls) -> "Client":
        """
        Create a Client configured for Hedera Previewnet.
        
        Note: Operator must be set manually using set_operator().

        Returns:
            Client: A Client instance configured for previewnet.
        """
        return cls(Network("previewnet"))

    def _init_mirror_stub(self) -> None:
        """
        Connect to a mirror node for topic message subscriptions.
        Mirror nodes always use TLS (mandatory). We use self.network.get_mirror_address()
        for a configurable mirror address, which should use port 443 for HTTPS connections.
        """
        mirror_address = self.network.get_mirror_address()
        if mirror_address.endswith(':50212') or mirror_address.endswith(':443'):
            self.mirror_channel = grpc.secure_channel(mirror_address, grpc.ssl_channel_credentials())
        else:
            self.mirror_channel = grpc.insecure_channel(mirror_address)
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

    def set_transport_security(self, enabled: bool) -> "Client":
        """
        Enable or disable TLS for consensus node connections.
        
        Note:
            TLS is enabled by default for hosted networks (mainnet, testnet, previewnet).
            For local networks (solo, localhost) and custom networks, TLS is disabled by default.
            Use this method to override the default behavior.
        """
        self.network.set_transport_security(enabled)
        return self

    def is_transport_security(self) -> bool:
        """
        Determine if TLS is enabled for consensus node connections.
        """
        return self.network.is_transport_security()

    def set_verify_certificates(self, verify: bool) -> "Client":
        """
        Enable or disable verification of server certificates when TLS is enabled.
        
        Note:
            Certificate verification is enabled by default for all networks.
            Use this method to disable verification (e.g., for testing with self-signed certificates).
        """
        self.network.set_verify_certificates(verify)
        return self

    def is_verify_certificates(self) -> bool:
        """
        Determine if certificate verification is enabled.
        """
        return self.network.is_verify_certificates()

    def set_tls_root_certificates(self, root_certificates: Optional[bytes]) -> "Client":
        """
        Provide custom root certificates for TLS connections.
        """
        self.network.set_tls_root_certificates(root_certificates)
        return self

    def get_tls_root_certificates(self) -> Optional[bytes]:
        """
        Retrieve the configured root certificates for TLS connections.
        """
        return self.network.get_tls_root_certificates()
    
    def set_default_max_query_payment(self, max_query_payment: Union[int, float, Decimal, Hbar]) -> "Client":
        """
        Sets the default maximum Hbar amount allowed for any query executed by this client.

        The SDK fetches the actual query cost and fails early if it exceeds this limit.
        Individual queries may override this value via `Query.set_max_query_payment()`.

        Args:
            max_query_payment (Union[int, float, Decimal, Hbar]):
                The maximum amount of Hbar that any single query is allowed to cost.
        Returns:
            Client: The current client instance for method chaining.
        """
        if isinstance(max_query_payment, bool) or not isinstance(max_query_payment, (int, float, Decimal, Hbar)):
            raise TypeError(
                "max_query_payment must be int, float, Decimal, or Hbar, "
                f"got {type(max_query_payment).__name__}"
            )
        
        value = (
            max_query_payment 
            if isinstance(max_query_payment, Hbar)
            else Hbar(max_query_payment)
        )

        if value < Hbar(0):
            raise ValueError("max_query_payment must be non-negative")

        self.default_max_query_payment = value
        return self

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