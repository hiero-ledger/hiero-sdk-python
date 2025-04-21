from hiero_sdk_python.hapi.services import crypto_service_pb2_grpc
from hiero_sdk_python.hapi.services import file_service_pb2_grpc
from hiero_sdk_python.hapi.services import network_service_pb2_grpc
from hiero_sdk_python.hapi.services import smart_contract_service_pb2_grpc
from hiero_sdk_python.hapi.services import token_service_pb2_grpc
from hiero_sdk_python.hapi.services import consensus_service_pb2_grpc
from hiero_sdk_python.hapi.services import freeze_service_pb2_grpc
from hiero_sdk_python.hapi.services import schedule_service_pb2_grpc
from hiero_sdk_python.hapi.services import util_service_pb2_grpc
from hiero_sdk_python.hapi.services import address_book_service_pb2_grpc

class _Channel:
    """
    The _Channel class is a wrapper around gRPC channels that provides access to various 
    Hedera service stubs.
    
    """
    def __init__(self, grpc_channel=None):
        """
        Initialize a new _Channel instance.
        
        Args:
            grpc_channel: The gRPC channel to wrap, obtained from a Client instance.
                          If None, service stub properties will return None when accessed.
        """
        self.channel = grpc_channel

        self._crypto = None
        self._file = None
        self._network = None
        self._smart_contract = None
        self._token = None
        self._topic = None
        self._freeze = None
        self._schedule = None
        self._util = None
        self._address_book = None

    @property
    def crypto(self):
        """
        Provides access to the CryptoService stub for cryptocurrency operations.
        
        This stub handles operations like:
        - Creating accounts (createAccount)
        - Transferring cryptocurrency (cryptoTransfer)
        - Updating accounts (updateAccount)
        - Deleting accounts (cryptoDelete)
        
        Returns:
            CryptoServiceStub: The gRPC stub for crypto operations, or None if no channel exists.
        """
        if self._crypto is None and self.channel is not None:
            self._crypto = crypto_service_pb2_grpc.CryptoServiceStub(self.channel)
        return self._crypto
    
    @property
    def file(self):
        """
        Provides access to the FileService stub for file operations.
        
        This stub handles operations like:
        - Creating files (createFile)
        - Updating files (updateFile)
        - Deleting files (deleteFile)
        
        Returns:
            FileServiceStub: The gRPC stub for file operations, or None if no channel exists.
        """
        if self._file is None and self.channel is not None:
            self._file = file_service_pb2_grpc.FileServiceStub(self.channel)
        return self._file
    
    @property
    def smart_contract(self):
        """
        Provides access to the SmartContractService stub for smart contract operations.
        
        This stub handles operations like:
        - Creating contracts (createContract)
        - Updating contracts (updateContract)
        - Deleting contracts (deleteContract)
        - Calling contracts (contractCallMethod)
        
        Returns:
            SmartContractServiceStub: The gRPC stub for contract operations, or None if no channel exists.
        """
        if self._smart_contract is None and self.channel is not None:
            self._smart_contract = smart_contract_service_pb2_grpc.SmartContractServiceStub(self.channel)
        return self._smart_contract
    
    @property
    def topic(self):
        """
        Provides access to the ConsensusService stub for consensus topic operations.
        
        This stub handles operations like:
        - Creating topics (createTopic)
        - Updating topics (updateTopic)
        - Deleting topics (deleteTopic)
        - Submitting messages to topics (submitMessage)
        - Querying topic info (getTopicInfo)
        
        Returns:
            ConsensusServiceStub: The gRPC stub for consensus operations, or None if no channel exists.
        """
        if self._topic is None and self.channel is not None:
            self._topic = consensus_service_pb2_grpc.ConsensusServiceStub(self.channel)
        return self._topic
    
    @property
    def freeze(self):
        """
        Provides access to the FreezeService stub for network freeze operations.
        
        This stub handles operations like:
        - Freezing the network (freezeNetwork)
        - Administrative operations on the network
        
        Returns:
            FreezeServiceStub: The gRPC stub for freeze operations, or None if no channel exists.
        """
        if self._freeze is None and self.channel is not None:
            self._freeze = freeze_service_pb2_grpc.FreezeServiceStub(self.channel)
        return self._freeze
    
    @property
    def network(self):
        """
        Provides access to the NetworkService stub for network-related operations.
        
        This stub handles operations like:
        - Getting network version info (getVersionInfo)
        - Querying network fees (getFeeSchedule)
        - Querying exchange rates (getExchangeRate)
        
        Returns:
            NetworkServiceStub: The gRPC stub for network operations, or None if no channel exists.
        """
        if self._network is None and self.channel is not None:
            self._network = network_service_pb2_grpc.NetworkServiceStub(self.channel)
        return self._network
    
    @property
    def token(self):
        """
        Provides access to the TokenService stub for token operations.
        
        This stub handles operations like:
        - Creating tokens (createToken)
        - Updating tokens (updateToken)
        - Minting tokens (mintToken)
        - Burning tokens (burnToken)
        
        Returns:
            TokenServiceStub: The gRPC stub for token operations, or None if no channel exists.
        """
        if self._token is None and self.channel is not None:
            self._token = token_service_pb2_grpc.TokenServiceStub(self.channel)
        return self._token
    
    @property
    def schedule(self):
        """
        Provides access to the ScheduleService stub for scheduled transaction operations.
        
        This stub handles operations like:
        - Creating scheduled transactions (createSchedule)
        - Signing scheduled transactions (signSchedule)
        - Deleting scheduled transactions (deleteSchedule)
        
        Returns:
            ScheduleServiceStub: The gRPC stub for scheduled transaction operations, or None if no channel exists.
        """
        if self._schedule is None and self.channel is not None:
            self._schedule = schedule_service_pb2_grpc.ScheduleServiceStub(self.channel)
        return self._schedule
    
    @property
    def util(self):
        """
        Provides access to the UtilService stub for utility operations.
        
        This stub handles operations like:
        - Pinging nodes (ping)
        - Getting transaction records (getTxRecordByTxID)
        
        Returns:
            UtilServiceStub: The gRPC stub for utility operations, or None if no channel exists.
        """
        if self._util is None and self.channel is not None:
            self._util = util_service_pb2_grpc.UtilServiceStub(self.channel)
        return self._util
    
    @property
    def address_book(self):
        """
        Provides access to the AddressBookService stub for node address operations.
        
        This stub handles operations like:
        - Getting the network address book (getAddressBook)
        
        Returns:
            AddressBookServiceStub: The gRPC stub for address book operations, or None if no channel exists.
        """
        if self._address_book is None and self.channel is not None:
            self._address_book = address_book_service_pb2_grpc.AddressBookServiceStub(self.channel)
        return self._address_book
