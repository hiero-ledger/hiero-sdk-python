class EvmAddress:
    """
    Represents a 20-byte EVM address derived from the rightmost 20 bytes of 
    32 byte Keccak-256 hash of an ECDSA public key.
    """
    def __init__(self, address_bytes: bytes) -> None:
        """
        Initialize an EvmAddress instance from bytes.
        
        Args:
        address_bytes (bytes): A 20-byte sequence representing the EVM address.
        """
        if len(address_bytes) != 20:
            raise ValueError("EvmAddress must be exactly 20 bytes long.")

        self.address_bytes: bytes = address_bytes

    @classmethod
    def from_string(cls, evm_address: str) -> "EvmAddress":
        """
        Create an EvmAddress from a hex string (with or without '0x' prefix).
        """
        if not isinstance(evm_address, str):
            raise TypeError("evm_address must be a of type string.")

        address = evm_address[2:] if evm_address.startswith('0x') else evm_address

        if len(address) == 40:
            return cls(address_bytes=bytes.fromhex(address))

        raise ValueError("Invalid hex string for evm_address.")

    @classmethod
    def from_bytes(cls, address_bytes: "bytes") -> "EvmAddress":
        """Create an EvmAddress from raw bytes."""
        return cls(address_bytes)

    def to_string(self) -> str:
        """Return the EVM address as a hex string"""
        return bytes.hex(self.address_bytes)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"<EvmAddress hex={self.to_string()}>"

    def __eq__(self, obj: object) -> bool:
        if not isinstance(obj, EvmAddress):
            return False

        return self.address_bytes == obj.address_bytes

    def __hash__(self) -> int:
        return hash(self.address_bytes)
