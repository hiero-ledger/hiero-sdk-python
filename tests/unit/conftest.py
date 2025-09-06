import time

import pytest

from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.client.client import Client
from hiero_sdk_python.client.network import Network
from hiero_sdk_python.consensus.topic_id import TopicId
from hiero_sdk_python.contract.contract_id import ContractId
from hiero_sdk_python.crypto.private_key import PrivateKey
from hiero_sdk_python.file.file_id import FileId
from hiero_sdk_python.hapi.services import timestamp_pb2
from hiero_sdk_python.logger.log_level import LogLevel
from hiero_sdk_python.node import _Node
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.tokens.nft_id import NftId
from hiero_sdk_python.tokens.token_id import TokenId
from hiero_sdk_python.transaction.transaction_id import TransactionId


@pytest.fixture
def mock_account_ids():
    """Fixture to provide mock account IDs and token IDs."""
    account_id_sender = AccountId(0, 0, 1)
    account_id_recipient = AccountId(0, 0, 2)
    node_account_id = AccountId(0, 0, 3)
    token_id_1 = TokenId(1, 1, 1)
    token_id_2 = TokenId(2, 2, 2)
    return account_id_sender, account_id_recipient, node_account_id, token_id_1, token_id_2

@pytest.fixture
def amount():
    """Fixture to provide a default amount for fungible tokens."""
    return 1000

@pytest.fixture
def metadata():
    """Fixture to provide mock metadata for NFTs."""
    return [b'a']

@pytest.fixture
def transaction_id():
    """Fixture that generates a transaction ID for testing."""
    return TransactionId.generate(AccountId(0, 0, 1234))

@pytest.fixture
def private_key():
    """Fixture to generate a private key for testing."""
    return PrivateKey.generate()

@pytest.fixture
def topic_id():
    """Fixture to create a topic ID for testing."""
    return TopicId(0, 0, 1234)

@pytest.fixture
def nft_id():
    """Fixture to provide a mock NftId instance."""
    token_id = TokenId(shard=0, realm=0, num=1)
    serial_number = 8
    return NftId(token_id=token_id, serial_number=serial_number)

@pytest.fixture
def token_id():
    """Fixture to provide a mock TokenId instance."""
    return TokenId(shard=0, realm=0, num=3)

@pytest.fixture
def file_id():
    """Fixture to provide a mock FileId instance."""
    return FileId(shard=0, realm=0, file=2)

@pytest.fixture
def contract_id():
    """Fixture to provide a mock ContractId instance."""
    return ContractId(shard=0, realm=0, contract=1)

@pytest.fixture
def mock_client():
    """Fixture to provide a mock client with hardcoded nodes for testing purposes."""
    nodes = [_Node(AccountId(0, 0, 3), "node1.example.com:50211", None)]
    network = Network(nodes=nodes)
    client = Client(network)
    client.logger.set_level(LogLevel.DISABLED)

    operator_key = PrivateKey.generate()
    operator_id = AccountId(0, 0, 1984)
    client.set_operator(operator_id, operator_key)

    return client
