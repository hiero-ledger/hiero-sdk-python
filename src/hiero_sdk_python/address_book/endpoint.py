from typing import TypedDict

from hiero_sdk_python.hapi.services.basic_types_pb2 import ServiceEndpoint

class EndpointDict(TypedDict):
    """
    A TypedDict representing the structure of an endpoint in JSON format.
    
    Attributes:
        ip_address_v4 (str): The IPv4 address of the endpoint.
        port (int): The port number of the endpoint.
        domain_name (str): The domain name of the endpoint.
    """
    ip_address_v4: str
    port: int
    domain_name: str

class Endpoint:
    """
    Represents an endpoint with address, port, and domain name information.
    This class is used to handle service endpoints in the Hedera network.
    """
    
    def __init__(
        self,
        address: bytes = None,
        port: int = None,
        domain_name: str = None
    ) -> None:
        """
        Initialize a new Endpoint instance.
        
        Args:
            address (bytes, optional): The IP address in bytes format.
            port (int, optional): The port number.
            domain_name (str, optional): The domain name.
        """
        self._address: bytes = address
        self._port: int = port
        self._domain_name: str = domain_name
    
    def set_address(self, address: bytes) -> "Endpoint":
        """
        Set the IP address of the endpoint.
        
        Args:
            address (bytes): The IP address in bytes format.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._address = address
        return self
    
    def get_address(self) -> bytes:
        """
        Get the IP address of the endpoint.
        
        Returns:
            bytes: The IP address in bytes format.
        """
        return self._address
    
    def set_port(self, port: int) -> "Endpoint":
        """
        Set the port of the endpoint.
        
        Args:
            port (int): The port number.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._port = port
        return self
    
    def get_port(self) -> int:
        """
        Get the port of the endpoint.
        
        Returns:
            int: The port number.
        """
        return self._port
    
    def set_domain_name(self, domain_name: str) -> "Endpoint":
        """
        Set the domain name of the endpoint.
        
        Args:
            domain_name (str): The domain name.
            
        Returns:
            Endpoint: This instance for method chaining.
        """
        self._domain_name = domain_name
        return self
    
    def get_domain_name(self) -> str:
        """
        Get the domain name of the endpoint.
        
        Returns:
            str: The domain name.
        """
        return self._domain_name
    
    @classmethod
    def _from_proto(cls, service_endpoint: ServiceEndpoint) -> "Endpoint":
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
    
    def _to_proto(self) -> ServiceEndpoint:
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
    
    def __str__(self) -> str:
        """
        Get a string representation of the Endpoint.
        
        Returns:
            str: The string representation in the format 'domain:port' or 'ip:port'.
        """
        
        return f"{self._address.decode('utf-8')}:{self._port}"

    @classmethod
    def from_dict(cls, json_data: EndpointDict) -> "Endpoint":
        """
        Create an Endpoint from a JSON object.
        
        Args:
            json_data: The JSON object.
        """
        if 'ip_address_v4' not in json_data or 'port' not in json_data or 'domain_name' not in json_data:
            raise ValueError("JSON data must contain 'ip_address_v4', 'port', and 'domain_name' keys.")
        return cls(
            address=bytes(json_data.get('ip_address_v4', ''), 'utf-8'),
            port=json_data.get('port'),
            domain_name=json_data.get('domain_name')
        )