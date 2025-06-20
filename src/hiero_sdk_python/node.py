import time
import grpc
from typing import Optional
from hiero_sdk_python.account.account_id import AccountId
from hiero_sdk_python.channels import _Channel
from hiero_sdk_python.address_book.node_address import NodeAddress
from hiero_sdk_python.managed_node_address import _ManagedNodeAddress

class _Node:
    
    def __init__(self, account_id: AccountId, address: str, address_book: NodeAddress):
        """
        Initialize a new Node instance.
        
        Args:
            account_id (AccountId): The account ID of the node.
            address (str): The address of the node.
            min_backoff (int): The minimum backoff time in seconds.
        """
        
        self._account_id: AccountId = account_id
        self._channel: Optional[_Channel] = None
        self._address_book: NodeAddress = address_book
        self._address: _ManagedNodeAddress = _ManagedNodeAddress._from_string(address)
    
    def _close(self):
        """
        Close the channel for this node.
        
        Returns:
            None
        """
        if self._channel is not None:
            self._channel.channel.close()
            self._channel = None

    def _get_channel(self):
        """
        Get the channel for this node.
        
        Returns:
            _Channel: The channel for this node.
        """
        if self._channel:
            return self._channel
        
        if self._address._is_transport_security():
            channel = grpc.secure_channel(str(self._address))
        else:
            channel = grpc.insecure_channel(str(self._address))
        
        self._channel = _Channel(channel)
        
        return self._channel