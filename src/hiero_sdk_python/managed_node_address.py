import re

class _ManagedNodeAddress:
    """
    Represents a managed consensus node address with a host and port.
    This class is used to handle consensus node addresses in the Hedera network.
    Note: Mirror nodes are handled separately and do not use this class.
    """
    PORT_NODE_PLAIN = 50211
    PORT_NODE_TLS = 50212
    TLS_PORTS = {PORT_NODE_TLS}
    PLAIN_PORTS = {PORT_NODE_PLAIN}
    
    # Regular expression to parse a host:port string
    HOST_PORT_PATTERN = re.compile(r'^(\S+):(\d+)$')
    
    def __init__(self, address=None, port=None):
        """
        Initialize a new ManagedNodeAddress instance.
        
        Args:
            address (str, optional): The host address.
            port (int, optional): The port number.
        """
        self._address = address
        self._port = port
    
    @classmethod
    def _from_string(cls, address_str):
        """
        Create a ManagedNodeAddress from a string in the format 'host:port'.
        
        Args:
            address_str (str): A string in the format 'host:port'.
            
        Returns:
            ManagedNodeAddress: A new ManagedNodeAddress instance.
            
        Raises:
            ValueError: If the address string is not in the correct format.
        """
        match = cls.HOST_PORT_PATTERN.match(address_str)
        
        if match:
            host = match.group(1)
            try:
                port = int(match.group(2))
                return cls(address=host, port=port)
            except ValueError:
                raise ValueError(f"Failed to parse port number: {match.group(2)}")
        
        raise ValueError("Failed to parse node address. Format should be 'host:port'")
    
    def _is_transport_security(self):
        """
        Check if the address uses a secure port.
        
        Returns:
            bool: True if the port is a secure port (50212), False otherwise.
        """
        return self._port in self.TLS_PORTS
    
    def _to_secure(self):
        """
        Return a new ManagedNodeAddress that uses the secure port when possible.
        Converts consensus node port from plaintext (50211) to TLS (50212).
        """
        if self._is_transport_security():
            return self
        
        port = self._port
        if port == self.PORT_NODE_PLAIN:
            port = self.PORT_NODE_TLS
        return _ManagedNodeAddress(self._address, port)
    
    def _to_insecure(self):
        """
        Return a new ManagedNodeAddress that uses the plaintext port when possible.
        Converts consensus node port from TLS (50212) to plaintext (50211).
        """
        if not self._is_transport_security():
            return self
        
        port = self._port
        if port == self.PORT_NODE_TLS:
            port = self.PORT_NODE_PLAIN
        return _ManagedNodeAddress(self._address, port)
    
    def _get_host(self):
        """
        Return the host component of the address.
        """
        return self._address

    def _get_port(self):
        """
        Return the port component of the address.
        """
        return self._port

    def __str__(self):
        """
        Get a string representation of the ManagedNodeAddress.
        
        Returns:
            str: The string representation in the format 'host:port'.
        """
        if self._address is not None:
            return f"{self._address}:{self._port}"
        
        return ""
