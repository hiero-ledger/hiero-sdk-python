from hiero_sdk_python.hapi.services.basic_types_pb2 import ServiceEndpoint

class Endpoint:
    """
    Represents an endpoint with address, port, and domain name information.
    This class is used to handle service endpoints in the Hedera network.
    """
    
    def __init__(self, address=None, port=None, domain_name=None):
        """
        Initialize a new Endpoint instance.
        
        Args:
            address (bytes, optional): The IP address in bytes format.
            port (int, optional): The port number.
            domain_name (str, optional): The domain name.
        """
        self._address : bytes = address
        self._port : int = port
        self._domain_name : str = domain_name
    
    def set_address(self, address):
        """
        Set the IP address of the endpoint.
        
        Args:
            address (bytes): The IP address in bytes format.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._address = address
        return self
    
    def get_address(self):
        """
        Get the IP address of the endpoint.
        
        Returns:
            bytes: The IP address in bytes format.
        """
        return self._address
    
    def set_port(self, port):
        """
        Set the port of the endpoint.
        
        Args:
            port (int): The port number.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._port = port
        return self
    
    def get_port(self):
        """
        Get the port of the endpoint.
        
        Returns:
            int: The port number.
        """
        return self._port
    
    def set_domain_name(self, domain_name):
        """
        Set the domain name of the endpoint.
        
        Args:
            domain_name (str): The domain name.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._domain_name = domain_name
        return self
    
    def get_domain_name(self):
        """
        Get the domain name of the endpoint.
        
        Returns:
            str: The domain name.
        """
        return self._domain_name
    
    @classmethod
    def from_proto(cls, service_endpoint : 'ServiceEndpoint'):
        """
        Create an Endpoint from a protobuf ServiceEndpoint.
        
        Args:
            service_endpoint: The protobuf ServiceEndpoint object.
            
        Returns:
            Endpoint: A new Endpoint instance.
        """
        port = service_endpoint.port
        
        if port == 0 or port == 50111:
            port = 50211
        
        return cls(
            address=service_endpoint.ipAddressV4,
            port=port,
            domain_name=service_endpoint.domain_name
        )
    
    def _to_proto(self):
        """
        Convert this Endpoint to a protobuf ServiceEndpoint.
        
        Returns:
            ServiceEndpoint: A protobuf ServiceEndpoint object.
        """
        
        return ServiceEndpoint(
            ipAddressV4=self._address,
            port=self._port,
            domain_name=self._domain_name
        )
    
    def __str__(self):
        """
        Get a string representation of the Endpoint.
        
        Returns:
            str: The string representation in the format 'domain:port' or 'ip:port'.
        """
        if self._domain_name:
            # If domain name is populated, use domain_name + port
            return f"{self._domain_name}:{self._port}"
        else:
            # Format IP address as dotted decimal notation
            if self._address:
                return f"{self._address[0] & 0xFF}.{self._address[1] & 0xFF}.{self._address[2] & 0xFF}.{self._address[3] & 0xFF}:{self._port}"
            return ""
