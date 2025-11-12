class EvmAddress:
    def __init__(self, bytes: bytes) -> None:
        if len(bytes) != 20:
            raise ValueError("EvmAddress must be exactly 20 bytes long.")
        
        self.bytes: "bytes" = bytes
    
    @classmethod
    def from_string(cls, evm_address: str) -> "EvmAddress":
        """
        Create an EvmAddress from a hex string (with or without '0x' prefix).
        """
        address = evm_address[2:] if evm_address.startswith('0x') else evm_address

        if len(address) == 40:
            return cls(bytes=bytes.fromhex(address))
        
        raise ValueError("")
    
    @classmethod
    def from_bytes(cls, bytes: "bytes") -> "EvmAddress":
        """Create an EvmAddress from raw bytes."""
        return cls(bytes=bytes)
    
    def to_string(self) -> str:
        """Return the EVM address as a hex string"""
        return bytes.hex(self.bytes)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self):
        return f"<EvmAddress hex={self.to_string()}>"
    
    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, EvmAddress):
            return False
        
        return self.bytes == obj.bytes
    
    def __hash__(self):
        return hash(self.bytes)
