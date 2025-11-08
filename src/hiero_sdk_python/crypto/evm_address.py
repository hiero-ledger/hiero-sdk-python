class EvmAddress:
    def __init__(self, bytes: bytes) -> None:
        self.bytes: "bytes" = bytes
    
    @classmethod
    def from_string(cls, evm_address: str) -> "EvmAddress":
        address = evm_address[2:] if evm_address.startswith('0x') else evm_address

        if len(address) == 40:
            return cls(bytes=bytes.fromhex(address))
        
        raise ValueError("")
    
    @classmethod
    def from_bytes(cls, bytes: "bytes") -> "EvmAddress":
        return cls(bytes=bytes)

    def __str__(self) -> str:
        return bytes.hex(self.bytes)

    def __repr__(self):
        return f"<EvmAddress hex={bytes.hex(self.bytes)}>"
    
