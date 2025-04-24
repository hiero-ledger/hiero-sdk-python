import grpc
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.managed_node import _ManagedNode
from hiero_sdk_python.address_book.node_address import NodeAddress

class _Node(_ManagedNode):
    
    def __init__(self, account_id: AccountId, address: str, min_backoff: int):
        """
        Initialize a new Node instance.
        
        Args:
            account_id (AccountId): The account ID of the node.
            address (str): The address of the node.
            min_backoff (int): The minimum backoff time in seconds.
        """
        
        super().__init__(address, min_backoff)
        
        self._account_id : AccountId = account_id
        self._channel : _Channel = None
        self._address_book : NodeAddress = None
        self._verify_certificate : bool = True
        
    def _get_key(self):
        """
        Get the key for this node, which is the string representation of the account ID.
        
        Returns:
            str: The string representation of the account ID.
        """
        return str(self._account_id)
    
    def _close(self):
        """
        Close the channel for this node.
        
        Returns:
            None
        """
        if self._channel is not None:
            self._channel.channel.close()
            self._channel = None
    
    def _to_secure(self):
        """
        Convert this node to use a secure connection.
        
        Returns:
            Node: A new Node instance with a secure connection.
        """
        new_node = _Node(
            account_id=self._account_id,
            address=str(self._address._to_secure()),
            min_backoff=self._min_backoff
        )
        
        new_node._current_backoff = self._current_backoff
        new_node._last_used = self._last_used
        new_node._readmit_time = self._readmit_time
        new_node._use_count = self._use_count
        new_node._bad_grpc_status_count = self._bad_grpc_status_count
        new_node._address_book = self._address_book
        new_node._verify_certificate = self._verify_certificate
        
        return new_node
    
    def _to_insecure(self):
        """
        Convert this node to use an insecure connection.
        
        Returns:
            Node: A new Node instance with an insecure connection.
        """
        new_node = _Node(
            account_id=self._account_id,
            address=str(self._address._to_insecure()),
            min_backoff=self._min_backoff
        )
        
        new_node._current_backoff = self._current_backoff
        new_node._last_used = self._last_used
        new_node._readmit_time = self._readmit_time
        new_node._use_count = self._use_count
        new_node._bad_grpc_status_count = self._bad_grpc_status_count
        new_node._address_book = self._address_book
        new_node._verify_certificate = self._verify_certificate
        
        return new_node
    
    def _set_verify_certificate(self, verify):
        """
        Set whether to verify the certificate for this node.
        
        Args:
            verify (bool): Whether to verify the certificate.
        """
        self._verify_certificate = verify
    
    def _get_verify_certificate(self):
        """
        Get whether to verify the certificate for this node.
        
        Returns:
            bool: Whether to verify the certificate.
        """
        return self._verify_certificate

    def _get_channel(self):
        """
        Get the channel for this node.
        
        Returns:
            _Channel: The channel for this node.
        """
        if self._channel:
            return self._channel
        
        options = {
            'grpc.keepalive_timeout_ms': 100000,
            'grpc.keepalive_time_ms': 10000,
            "grpc.keepalive_permit_without_calls": 1
        }
        
        if not self._address._is_transport_security():
            channel = grpc.insecure_channel(str(self._address), options)
        else:
            # Create TLS credentials for secure connections
            # TODO: Somehow should verify the certificate
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(str(self._address), credentials, options)
        
        self._channel = _Channel(channel)
        
        return self._channel