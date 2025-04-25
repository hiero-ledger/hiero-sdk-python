import re

class _ManagedNodeAddress:
    """
    Represents a managed node address with a host and port.
    This class is used to handle node addresses in the Hedera network.
    """
    
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
            bool: True if the port is a secure port (50212 or 443), False otherwise.
        """
        return self._port == 50212 or self._port == 443
    
    def __str__(self):
        """
        Get a string representation of the ManagedNodeAddress.
        
        Returns:
            str: The string representation in the format 'host:port'.
        """
        if self._address is not None:
            return f"{self._address}:{self._port}"
        
        return ""
